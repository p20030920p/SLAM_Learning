"""Create a raw RGB-D human-review package, without loading any model output."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.identity_budget import REVIEW_CHECKS, digest, validate_annotations


# Raw-image coordinates, manually proposed from held-out RGB only. Human review is pending.
POLYGONS = {
    "blue_vase": {12: [[509,8],[553,8],[544,31],[548,46],[565,68],[565,99],[555,139],[544,147],[520,146],
                       [511,131],[503,100],[502,72],[514,45],[517,29]],
                  62: [[281,0],[326,0],[330,27],[349,49],[361,82],[359,115],[353,145],[339,157],[298,158],
                       [285,143],[278,110],[273,78],[277,49],[291,23]],
                  112: [[305,123],[352,123],[343,145],[344,163],[360,181],[369,210],[366,235],[358,259],
                        [343,264],[318,261],[308,244],[300,217],[296,192],[300,173],[314,153]],
                  162: [[467,16],[509,16],[501,37],[504,55],[519,75],[520,105],[514,137],[503,151],
                        [481,153],[469,138],[464,112],[459,82],[466,59],[477,40]]},
    "bird_figurine": {12: [[622,207],[655,216],[672,197],[675,183],[686,176],[697,179],[703,195],
                           [704,217],[694,236],[682,241],[662,238],[646,230],[620,216]],
                      62: [[450,222],[477,227],[494,213],[499,196],[514,186],[528,190],[537,210],
                           [535,235],[524,250],[512,253],[492,249],[477,240],[446,232]],
                      112: [[438,323],[461,330],[478,314],[481,298],[494,288],[507,291],[515,307],
                            [516,328],[505,342],[490,348],[473,342],[457,335],[433,331]],
                      162: [[580,207],[607,214],[624,198],[629,183],[641,177],[652,182],[658,198],
                            [660,216],[652,230],[639,237],[622,233],[606,226],[579,215]]},
    "brown_jar": {12: [[575,247],[594,246],[598,257],[613,269],[622,287],[617,306],[606,313],
                      [584,312],[574,304],[569,285],[569,269],[579,258]],
                  62: [[402,273],[424,273],[426,285],[444,297],[451,319],[447,340],[433,348],
                       [408,347],[396,337],[391,317],[389,299],[401,286]],
                  112: [[398,364],[419,364],[424,375],[433,387],[436,407],[431,426],[417,435],
                        [396,436],[386,427],[381,406],[381,388],[395,375]],
                  162: [[538,246],[559,246],[561,258],[575,270],[577,288],[571,307],[556,313],
                        [540,310],[532,299],[530,280],[530,265],[541,257]]},
    "fish_figurine": {12: [[519,215],[534,210],[553,206],[581,200],[597,200],[600,206],[591,211],
                           [576,215],[568,229],[543,232],[533,225],[519,225]],
                      62: [[317,247],[331,241],[350,232],[372,227],[397,225],[414,221],[420,228],
                           [410,236],[387,240],[381,257],[350,261],[336,255],[316,260]],
                      112: [[319,340],[332,333],[354,324],[380,321],[402,317],[410,322],[399,329],
                            [384,333],[379,350],[350,355],[336,348],[318,353]],
                      162: [[479,216],[493,210],[513,204],[535,202],[554,199],[559,206],[548,212],
                            [535,216],[529,229],[502,234],[488,227],[478,231]]},
    "chair": {12: [[357,425],[382,414],[517,433],[537,443],[536,478],[524,621],[521,650],
                    [501,678],[99,678],[121,653],[151,638],[363,660],[354,504]],
              62: [[223,581],[249,566],[484,532],[506,531],[518,539],[516,575],[493,679],[236,679]],
              112: [[347,556],[366,544],[548,521],[571,520],[582,531],[582,570],[577,679],[361,679]],
              162: [[451,437],[469,426],[607,416],[624,423],[629,446],[619,598],[618,641],
                     [870,628],[897,660],[898,679],[416,679],[446,661],[446,491]]}
}


def draft():
    queries = {"blue_vase": "vase", "bird_figurine": "bird figurine", "brown_jar": "jar",
               "fish_figurine": "fish figurine", "chair": "chair"}
    return {"schema_version": 2, "scene": "room2", "version": "v2-draft-1", "coordinate_canvas": [1200, 680],
            "human_reviewed": False,
            "provenance": "AI-assisted raw held-out RGB proposals; depth previews supplied for human review. No room2 frontend or mapper output inspected. Not official Replica GT.",
            "duplicate_definition": "Two qualifying map objects representing the same selected physical ID count as one duplicate excess; disjoint fragments are recorded by coverage, not automatically counted as complete recoveries.",
            "exclusions": ["walls/floor/ceiling/windows/door", "shelf, its shelves and supports",
                           "plants and all other vases/containers", "books, boxes, plates and other unlabelled decor",
                           "occluded geometry; no inferred back surfaces"],
            "instances": [{"id": identity, "query": queries[identity], "first_reference_frame": 12,
                           "parts": "Whole physical object; visible surface only. Include attached base/legs/seat where visible; exclude surrounding shelf, decorations and other objects.",
                           "visibility": {str(f): "annotated" for f in views},
                           "views": [{"frame": f, "polygon": polygon} for f, polygon in views.items()]}
                          for identity, views in POLYGONS.items()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--room1-data", type=Path)
    args = parser.parse_args()
    cfg = json.loads(args.protocol.read_text())
    ann = draft()
    validate_annotations(cfg, ann, require_review=False)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "targets.draft.json").write_text(json.dumps(ann, indent=2) + "\n", encoding="utf-8")
    palette = ["#ff453a", "#30d5c8", "#ffd60a", "#bf5af2", "#0a84ff"]
    assets = []

    def raw_views(scene, data, frames, annotation):
        folder = args.output / scene
        folder.mkdir()
        for frame in frames:
            name = f"{frame:06d}"
            source = data / scene / "results" / f"frame{name}.jpg"
            target = folder / f"raw-{name}.jpg"
            shutil.copyfile(source, target)
            rgb = Image.open(source).convert("RGB").resize(tuple(annotation["coordinate_canvas"]))
            draw = ImageDraw.Draw(rgb)
            for i, target_ann in enumerate(annotation["instances"]):
                for view in target_ann["views"]:
                    if view["frame"] != frame:
                        continue
                    points = [tuple(p) for p in view["polygon"]]
                    draw.line(points + points[:1], fill=palette[i % len(palette)], width=3)
                    draw.text(points[0], f"{i + 1}: {target_ann['id']}", fill=palette[i % len(palette)], stroke_width=1)
            rgb.save(folder / f"proposal-{name}.png")
            depth_path = data / scene / "results" / f"depth{name}.png"
            depth = np.asarray(Image.open(depth_path), dtype=float) / 6553.5
            image = np.zeros((*depth.shape, 3), dtype=np.uint8)
            scaled = np.clip(depth / 6, 0, 1)
            image[..., 0] = (255 * scaled).astype(np.uint8)
            image[..., 1] = (255 * (1 - scaled)).astype(np.uint8)
            image[..., 2] = 100
            image[depth <= 0] = 0
            Image.fromarray(image).save(folder / f"depth-{name}.png")
            assets.append({"scene": scene, "frame": frame, "raw_rgb_sha256": digest(source),
                           "raw_depth_sha256": digest(depth_path), "depth_display": "0-6m green-to-red; invalid black"})
    raw_views("room2", args.data, cfg["reference_frames"], ann)
    if args.room1_data:
        baseline = json.loads((Path(__file__).resolve().parents[1] / "annotations/room1/targets.json").read_text())
        # Copy baseline as a new draft; never edit or rescore the original.
        baseline.update(version="v2-posthoc-draft", human_reviewed=False,
                        analysis_role="posthoc only; original v1 labels and results immutable")
        (args.output / "room1.targets.posthoc-draft.json").write_text(json.dumps(baseline, indent=2) + "\n")
        raw_views("room1", args.room1_data, [12, 137, 262, 387], baseline)
    receipt = {"reviewer_role": "human", "reviewer": "", "reviewed_at_utc": "", "approved": False,
               "checks": dict.fromkeys(REVIEW_CHECKS, False), "protocol_sha256": digest(args.protocol),
               "annotations_sha256": "SET_AFTER_HUMAN_EDITS", "source_manifest_sha256": digest(args.data / "manifest.json"),
               "notes": "Do not mark approved until the owner has actually checked the package."}
    (args.output / "human-review.template.json").write_text(json.dumps(receipt, indent=2) + "\n")
    template = Path(__file__).with_name("identity_review_template.html").read_text(encoding="utf-8")
    (args.output / "index.html").write_text(template.replace("__ANNOTATIONS__", json.dumps(ann)).replace(
        "__RECEIPT__", json.dumps(receipt)), encoding="utf-8")
    manifest = {"kind": "raw_annotation_review_package", "status": "human_review_pending",
                "protocol_sha256": digest(args.protocol), "source_manifest_sha256": digest(args.data / "manifest.json"),
                "source_url": "https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip",
                "license_context": "Replica rendered RGB-D from NICE-SLAM; review/reference use, not official instance GT",
                "draft_annotations_sha256": digest(args.output / "targets.draft.json"), "assets": assets}
    (args.output / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Raw review package ready; no freeze/model outputs: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
