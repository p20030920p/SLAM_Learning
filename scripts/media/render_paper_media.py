"""Render measured outputs as H.264 replays; playback rate is not algorithm throughput."""
from __future__ import annotations

import argparse
import copy
import gzip
import json
import pickle
import shutil
import sys
import uuid
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from slam_learning.core.provenance import digest, environment, git_state, utc_now, write_json
from slam_learning.runtime.runner import verify_record
from slam_learning.core.pose_audit import audit_camera_snapshots


def semantic_frames(method, record_path, record, output):
    run = record_path.parent
    source_hashes = {}
    if method == "conceptgraphs":
        with gzip.open(run / "objects.pkl.gz", "rb") as stream:
            saved = pickle.load(stream)  # Only a fully verified locally generated author map.
        clouds = [np.asarray(obj["pcd_np"]) for obj in saved["objects"]]
        image_root = run / "input/Replica/room0"
        world_from_map = np.eye(4)
        poses = np.loadtxt(image_root / "traj.txt").reshape(-1, 4, 4)
        snapshots = sorted((image_root / "objects_all_frames").rglob("[0-9]*.pkl.gz"))
        audit = audit_camera_snapshots(snapshots, poses, list(range(1, 40)))
        source_hashes.update({Path(path).relative_to(run).as_posix(): value
                             for path, value in audit["source_hashes"].items()})
        images = sorted((image_root / "gsa_vis_none").glob("*.jpg"))
        frame_ids = [int(path.stem.replace("frame", "")) for path in images]
    else:
        import open3d as o3d
        clouds = [np.asarray(o3d.io.read_point_cloud(str(path)).points)
                  for path in sorted((run / "objects").glob("*.ply"))]
        image_root = run / "input/Replica/room0"
        observations = json.loads((run / "frame_observations.json").read_text())
        images = [image_root / "results" / f"frame{item['source_index']:06d}.jpg" for item in observations]
        frame_ids = [int(path.stem.replace("frame", "")) for path in images]
    if len(images) != record.get("summary", {}).get("observations", 40) or not clouds:
        raise ValueError("Complete native outputs required")
    # Keep final-map framing fixed across all source observations and all text queries.
    points = np.concatenate(clouds)
    lower, upper = np.quantile(points[:, [0, 2]], [0.001, 0.999], axis=0)
    margin = np.maximum((upper - lower) * .05, .1)
    lower, upper = lower - margin, upper + margin
    chosen = np.unique(np.linspace(0, len(images)-1, min(20, len(images)), dtype=int))
    queries = copy.deepcopy(record["summary"]["queries"])
    frames, metadata = [], []
    for order, index in enumerate(chosen):
        path = images[index]
        source_hashes[path.relative_to(run).as_posix()] = digest(path)
        image = np.asarray(Image.open(path).convert("RGB"))
        if method == "hovsg":
            masks_path = run / "observations" / f"{index:06d}.npz"
            with np.load(masks_path) as observations:
                masks = observations["masks"]
            source_hashes[masks_path.relative_to(run).as_posix()] = digest(masks_path)
            colors = plt.get_cmap("tab20")
            image = image.astype(float)
            for i, mask in enumerate(masks):
                image[mask] = .65 * image[mask] + .35 * np.asarray(colors(i % 20)[:3]) * 255
            image = np.asarray(image, dtype=np.uint8)
        query = queries[min(len(queries)-1, order*len(queries)//len(chosen))]
        best = query["top_objects"][0]
        fig, axes = plt.subplots(1, 2, figsize=(12.8, 6.5), layout="constrained")
        axes[0].imshow(image)
        axes[0].set_title(f"Native SAM observations | source frame {frame_ids[index]:06d}", fontsize=11)
        axes[0].axis("off")
        for i, cloud in enumerate(clouds):
            selected = cloud[np.linspace(0, len(cloud)-1, min(1500, len(cloud)), dtype=int)]
            axes[1].scatter(selected[:, 0], selected[:, 2], s=.5,
                            c="#d74f2f" if i == best["object_index"] else "#a4b5b8", linewidths=0)
        center = best["center_world_m"]
        axes[1].scatter(center[0], center[2], s=85, marker="x", color="#d74f2f", linewidths=2)
        axes[1].set(xlim=(lower[0], upper[0]), ylim=(lower[1], upper[1]), aspect="equal",
                    xlabel="Replica world X (m)", ylabel="Replica world Z (m)")
        axes[1].set_title(f"Final map | {len(clouds)} segments | query: {query['query']}", fontsize=11)
        fig.suptitle(f"{record['method']} | Replica room0 | supplied camera poses", fontsize=15)
        fig.supxlabel(f"Candidate #{best['object_index']} | cosine {best['cosine_similarity']:.3f} | "
                      f"center ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f}) m\n"
                      "Offline final-map replay. Query correctness and navigation are not evaluated.", fontsize=10)
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("RGB"))
        plt.close(fig)
        metadata.append({"source_frame": frame_ids[index], "query": query["query"], "candidate": best})
    return frames, {"view": "Fixed Replica world XZ final-map projection", "bounds_xz_m": [lower.tolist(), upper.tolist()],
                    "map_frame_to_replica_world": world_from_map.tolist() if method == "conceptgraphs" else np.eye(4).tolist(),
                    "coordinate_audit": {"entrypoint": "cfslam_pipeline_batch.py uses absolute dataset.poses; loader normalized __getitem__ poses are bypassed",
                                         "checked_native_camera_poses": audit["checked_native_camera_poses"],
                                         "maximum_absolute_matrix_error": audit["maximum_absolute_matrix_error"]} if method == "conceptgraphs" else {"entrypoint": "HOV-SG ReplicaDataset reads absolute traj.txt matrices"},
                    "source_artifact_hashes": source_hashes, "frames": metadata,
                    "scope": "Final semantic map replay with source observations; no evolving-map or live-screen claim"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("method", choices=("dufomap", "beautymap", "conceptgraphs", "hovsg"))
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = args.record.resolve()
    issues = verify_record(source, full=True)
    record = json.loads(source.read_text(encoding="utf-8"))
    if issues or record.get("status") != "executed":
        raise ValueError(f"Completed full local evidence required: {issues}")
    output = root / "results/runs" / f"paper-media-{args.method}-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    started = utc_now()
    if args.method in ("dufomap", "beautymap"):
        if record.get("kind") != "author_map_replay":
            raise ValueError("Verified PCL map replay input required")
        frames = []
        with Image.open(source.parent / "replication_hero.gif") as gif:
            font = ImageFont.truetype("DejaVuSans.ttf", 20)
            for index, frame in enumerate(ImageSequence.Iterator(gif)):
                frame = frame.convert("RGB")
                # One method's native map panels, retaining full horizontal world view.
                y0, y1 = (30, 315) if args.method == "dufomap" else (320, 600)
                panel = frame.crop((0, y0, frame.width, y1)).resize((1200, 320))
                canvas = Image.new("RGB", (1200, 440), "white")
                canvas.paste(panel, (0, 65))
                draw = ImageDraw.Draw(canvas)
                frame_id = record["rendering"]["frame_ids"][index]
                draw.text((25, 15), args.method.upper() + " | " + frame_id + " | offline final-map replay", font=font, fill="#19383f")
                draw.text((25, 385), "Green: removed dynamic   Red: removed static   Blue: retained dynamic", font=font, fill="#19383f")
                draw.text((25, 413), "21 selected frames / 141 scored. Playback speed is not runtime.", font=font, fill="#19383f")
                frames.append(canvas)
        settings = {"view": record["rendering"]["camera"], "source_frame_ids": record["rendering"]["frame_ids"],
                    "scope": "One method cropped from the verified common PCL-label replay; all metrics computed before rendering"}
    else:
        expected = "ConceptGraphs" if args.method == "conceptgraphs" else "HOV-SG"
        if record.get("method") != expected:
            raise ValueError("Wrong semantic method record")
        frames, settings = semantic_frames(args.method, source, record, output)
    # Encode H.264 for browser playback; decode every frame to validate completion.
    import imageio_ffmpeg
    import cv2
    width, height = frames[0].size
    fps, repeats = 12, 8
    writer = imageio_ffmpeg.write_frames(str(output / "replay.mp4"), (width, height), fps=fps,
                                        codec="libx264", quality=7, macro_block_size=2,
                                        output_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    writer.send(None)
    for frame in frames:
        for _ in range(repeats):
            writer.send(np.asarray(frame))
    writer.close()
    cap = cv2.VideoCapture(str(output / "replay.mp4"))
    decoded, ranges = 0, []
    while True:
        okay, frame = cap.read()
        if not okay:
            break
        decoded += 1
        if decoded in (1, len(frames)*repeats//2, len(frames)*repeats):
            ranges.append(float(frame.std()))
    cap.release()
    if decoded != len(frames)*repeats or min(ranges) < 5:
        raise ValueError("Encoded replay is truncated or blank")
    preview = [frame.resize((960, round(frame.height * 960 / frame.width))).quantize(colors=128)
               for frame in frames]
    preview[0].save(output / "preview.gif", save_all=True, append_images=preview[1:],
                    duration=round(1000*repeats/fps), loop=0, optimize=True)
    frames[0].save(output / "poster.png")
    shutil.copy2(source, output / "input-record.json")
    settings.update(playback_fps=fps, repeats_per_observation=repeats, encoded_frames=decoded,
                    duration_s=decoded/fps, codec="H.264", inspected_frame_stddev=ranges,
                    reference={"repository": "https://github.com/p20030920p/Sim2Real-AlgoBench",
                               "commit": "53324d40def0dd753b4a99021b8fe596955a1ecd",
                               "adapted_convention": "Per-method MP4 + GIF + metadata, fixed view and decoded-output QA; no source copied"})
    write_json(output / "render.json", settings)
    result = {"schema_version": 1, "kind": "paper_reproduction_media", "method": args.method,
              "status": "executed", "started_at": started, "finished_at": utc_now(),
              "environment": environment(), "repository": git_state(root), "generator_sha256": digest(Path(__file__)),
              "input_record_sha256": digest(source), "rendering": settings, "artifacts": {}}
    for name in ("replay.mp4", "preview.gif", "poster.png", "render.json", "input-record.json"):
        path = output / name
        result["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}
    write_json(output / "record.json", result)
    print(output / "record.json", flush=True)


if __name__ == "__main__":
    main()
