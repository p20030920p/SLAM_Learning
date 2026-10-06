#!/usr/bin/env python3
"""02-07 · AnyLoc on 17 Places, with the authors' own code and vocabulary.

Everything that decides a number here is upstream:

  * feature extraction and VLAD  - `demo/utilities.py` (`DinoV2ExtractFeatures`,
    `VLAD`), the distilled SOTA implementation the authors point users at;
  * the vocabulary               - the authors' released cluster centres
    (`dinov2_vitg14/l31_value_c32/<domain>/c_centers.pt`), fetched from the
    official HuggingFace Space that the repo README links as its demo. The
    original OneDrive release now answers with a sign-in page, so this is the
    same artefact from the same authors, mirrored where their own README points;
  * the recall                   - `utilities.get_top_k_recall` (faiss
    IndexFlatIP on L2-normalised descriptors, the paper's seed 42).

The paper's Table III row for 17 Places is AnyLoc-VLAD-DINOv2 R@1 / R@5 =
65.0 / 80.5, with 406 database and 406 query images and a 5-frame tolerance,
which is exactly what `ground_truth_new.npy` encodes.

Usage:
    python3 work/run_17places.py                  # the paper's configuration
    python3 work/run_17places.py --model dinov2_vits14 --layer 11 --limit 8
"""
from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
REPO = os.path.join(FOLDER, "code", "AnyLoc")
DATA = os.path.join(FOLDER, "data", "raw", "17places", "17places")
VOCAB_SRC = os.path.join(FOLDER, "data", "raw", "vocabulary")
PAPER = {"R@1": 65.0, "R@5": 80.5}


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def vocab_path(model, layer, facet, num_c, domain):
    """Copy the authors' released vocabulary where the demo looks for it."""
    spec = f"{model}/l{layer}_{facet}_c{num_c}"
    dst_dir = os.path.join(REPO, "cache", "vocabulary", spec, domain)
    dst = os.path.join(dst_dir, "c_centers.pt")
    if not os.path.exists(dst):
        src = os.path.join(VOCAB_SRC, f"c_centers_{domain}_c{num_c}.pt")
        if not os.path.exists(src):
            raise SystemExit(f"vocabulary missing: {src} (see the README for the "
                             "official HuggingFace Space it comes from)")
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy(src, dst)
    return dst, spec


def images(split, limit=None):
    import natsort
    d = os.path.join(DATA, split)
    if not os.path.isdir(d):
        raise SystemExit(f"images missing: {d}")
    names = natsort.natsorted(f for f in os.listdir(d) if f.endswith(".jpg"))
    return [os.path.join(d, f) for f in (names[:limit] if limit else names)]


def build_models(model, layer, facet, num_c, domain, device):
    """Load the extractor and the authors' vocabulary once for both splits.

    Loading ViT-G/14 twice (once per split) peaks at two copies of a 4.5 GB model
    and got the first attempt OOM-killed between the splits; one instance is
    enough and keeps the peak near a single model.
    """
    demo = load_module(os.path.join(REPO, "demo", "utilities.py"), "anyloc_demo_utils")
    extractor = demo.DinoV2ExtractFeatures(model, layer, facet, device=device)
    c_centers_file, _spec = vocab_path(model, layer, facet, num_c, domain)
    vlad = demo.VLAD(num_c, desc_dim=None, cache_dir=os.path.dirname(c_centers_file))
    vlad.fit(None)
    print(f"  vocabulary: {os.path.relpath(c_centers_file, FOLDER)} ({num_c} clusters)")
    return extractor, vlad


def extract(fnames, extractor, vlad, device, cache):
    """Descriptor extraction, exactly the demo's preprocessing."""
    import numpy as np
    import torch
    import torchvision.transforms as tvf
    import torchvision.transforms.functional as T
    from PIL import Image
    from tqdm import tqdm

    if os.path.exists(cache):
        arr = np.load(cache)
        if arr.shape[0] == len(fnames):
            print(f"  cached descriptors: {os.path.relpath(cache, FOLDER)} {arr.shape}")
            return arr
    part = cache + ".partial.npy"
    done = 0
    if os.path.exists(part):
        arr = np.load(part)
        done = int(arr.shape[0])
        print(f"  resuming after {done} images from {os.path.basename(part)}")

    base_tf = tvf.Compose([tvf.ToTensor(),
                           tvf.Normalize(mean=[0.485, 0.456, 0.406],
                                         std=[0.229, 0.224, 0.225])])
    out = list(np.load(part)) if done else []
    fnames = fnames[done:] if done else fnames
    t0 = time.time()
    for i, fname in enumerate(tqdm(fnames, desc="  features", ncols=80), 1):
        with torch.no_grad():
            img_pt = base_tf(Image.open(fname).convert("RGB")).to(device)
            c, h, w = img_pt.shape
            img_pt = tvf.CenterCrop(((h // 14) * 14, (w // 14) * 14))(img_pt)[None, ...]
            ret = extractor(img_pt)                      # [1, patches, desc_dim]
            gd = vlad.generate(ret.cpu().squeeze())      # [agg_dim]
        out.append(gd.numpy())
        if i % 25 == 0 or i == len(fnames):
            dt = time.time() - t0
            print(f"    {i}/{len(fnames)} · {dt / i:.2f} s/img · "
                  f"ETA {(len(fnames) - i) * dt / i / 60:.1f} min", flush=True)
            # checkpoint the descriptors: this is a multi-hour CPU job and a
            # restart must not begin from image 1
            os.makedirs(os.path.dirname(cache), exist_ok=True)
            np.save(cache + ".partial.npy", np.stack(out))
    arr = np.stack(out)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    np.save(cache, arr)
    return arr


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="dinov2_vitg14")
    ap.add_argument("--layer", type=int, default=31)
    ap.add_argument("--facet", default="value", choices=["query", "key", "value", "token"])
    ap.add_argument("--num-c", type=int, default=32)
    ap.add_argument("--domain", default="indoor", choices=["indoor", "urban", "aerial"])
    ap.add_argument("--limit", type=int, default=None, help="first N images (smoke test)")
    ap.add_argument("--out", default=os.path.join(FOLDER, "results", "anyloc_17places.json"))
    args = ap.parse_args()

    import numpy as np

    torch_mod = __import__("torch")
    device = torch_mod.device("cpu")
    print(f"[anyloc] {args.model} layer {args.layer} facet {args.facet} · "
          f"VLAD c{args.num_c} · domain {args.domain} · device cpu "
          f"({torch_mod.get_num_threads()} threads)")

    db_files, qu_files = images("ref", args.limit), images("query", args.limit)
    print(f"  database {len(db_files)} images · query {len(qu_files)} images")

    tag = f"{args.model}_l{args.layer}_{args.facet}"
    cache_dir = os.path.join(HERE, "descs")
    extractor, vlad = build_models(args.model, args.layer, args.facet, args.num_c,
                                   args.domain, device)
    db = extract(db_files, extractor, vlad, device,
                 os.path.join(cache_dir, f"{tag}_17places_db.npy"))
    gc.collect()
    qu = extract(qu_files, extractor, vlad, device,
                 os.path.join(cache_dir, f"{tag}_17places_query.npy"))

    # The paper's recall function, unmodified.
    sys.path.insert(0, REPO)
    utils = load_module(os.path.join(REPO, "utilities.py"), "anyloc_root_utils")
    results = {"model": args.model, "layer": args.layer, "facet": args.facet,
               "num_clusters": args.num_c, "domain": args.domain,
               "database": len(db_files), "query": len(qu_files),
               "limit": args.limit, "paper": PAPER, "recall": {}}
    for gt_name in ("ground_truth_new.npy", "my_ground_truth_new.npy"):
        gt = np.load(os.path.join(DATA, gt_name), allow_pickle=True)
        gt_pos = [list(row[1]) for row in gt]
        _d, _i, recalls = utils.get_top_k_recall([1, 5], torch_mod.from_numpy(db),
                                                 torch_mod.from_numpy(qu), gt_pos,
                                                 method="cosine", norm_descs=True,
                                                 use_gpu=False, use_percentage=True)
        # `get_top_k_recall(..., use_percentage=True)` returns a *fraction*: the
        # upstream name is misleading (it divides by the number of queries and
        # stops there). Scale to percent so the numbers read like the paper's.
        results["recall"][gt_name] = {f"R@{k}": round(float(v) * 100, 2)
                                      for k, v in recalls.items()}
        print(f"  {gt_name}: "
              + " · ".join(f"R@{k} {v * 100:.1f}" for k, v in recalls.items()))

    primary = results["recall"]["ground_truth_new.npy"]
    results["primary_gt"] = "ground_truth_new.npy"
    results["diff_vs_paper"] = {k: round(primary[k] - PAPER[k], 2) for k in PAPER}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    print(f"[anyloc] wrote {os.path.relpath(args.out, FOLDER)}")
    print(f"  paper R@1/R@5 = {PAPER['R@1']}/{PAPER['R@5']} · "
          f"ours {primary['R@1']:.1f}/{primary['R@5']:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
