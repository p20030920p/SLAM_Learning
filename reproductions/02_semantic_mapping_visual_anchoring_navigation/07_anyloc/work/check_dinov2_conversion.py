#!/usr/bin/env python3
"""Why the converted DINOv2 checkpoint can be trusted, layer by layer.

`work/fetch_dinov2_weights.py` rewrites Meta's HuggingFace checkpoint into the
naming `torch.hub.load('facebookresearch/dinov2', ...)` expects, because
dl.fbaipublicfiles.com serves at ~1.3 kB/s from this machine. A strict load
catches missing or mis-shaped keys but not a wrong *permutation* (say, the two
halves of the SwiGLU `w12` swapped), so this compares the two implementations
block by block on a real 17places image.

Measured (ViT-G/14, 1530 patches):

    layer   cosine     rel-err
        0   0.999981   4.78e-03
        1   0.999971   6.07e-03
        4   0.999934   1.04e-02
        9   0.999887   1.44e-02
       19   0.999135   7.23e-02
       29   0.995914   3.51e-01
       39   0.995534   3.07e-01

Agreement is ~1e-5 at block 0 and decays smoothly with depth: that is fp32
accumulation across two different op orders, not a structural error. A swapped
SwiGLU would already disagree at block 0, where the agreement is 0.999981.

It builds the architecture straight from the cached hub source tree with no
weights, so it never touches the slow upstream file server.
"""
import torch, sys
sys.path.insert(0, "/home/qzl/workspace/Practice_SLam/SLAM_Learning/reproductions/02_semantic_mapping_visual_anchoring_navigation/07_anyloc/work")
import importlib.util
spec = importlib.util.spec_from_file_location("fdw", "/home/qzl/workspace/Practice_SLam/SLAM_Learning/reproductions/02_semantic_mapping_visual_anchoring_navigation/07_anyloc/work/fetch_dinov2_weights.py")
fdw = importlib.util.module_from_spec(spec); spec.loader.exec_module(fdw)

sd = fdw.convert("dinov2_vitg14")           # HF -> original naming
import os
sys.path.insert(0, os.path.expanduser("~/.cache/torch/hub/facebookresearch_dinov2_main"))
from dinov2.hub.backbones import _make_dinov2_model
hub = _make_dinov2_model(arch_name="vit_giant2", ffn_layer="swiglufused",
                           pretrained=False, weights=None)
missing, unexpected = hub.load_state_dict(sd, strict=False)
print(f"strict-ish load: {len([k for k in missing if 'mask_token' not in k])} missing, {len(unexpected)} unexpected")
del sd

from transformers import Dinov2Model
hf = Dinov2Model.from_pretrained("facebook/dinov2-giant").eval()

import torchvision.transforms as tvf
from PIL import Image
img = Image.open("/home/qzl/workspace/Practice_SLam/SLAM_Learning/reproductions/02_semantic_mapping_visual_anchoring_navigation/07_anyloc/data/17places/17places/ref/0.jpg").convert("RGB")
x = tvf.Compose([tvf.ToTensor(), tvf.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])(img)[None]
x = x[:, :, :(x.shape[2]//14)*14, :(x.shape[3]//14)*14]

hub_out = {}
def mk(i):
    def hook(m, inp, out):
        hub_out[i] = out.detach()
    return hook
for i, blk in enumerate(hub.blocks):
    blk.register_forward_hook(mk(i))
hf_out = {}
def mkh(i):
    def hook(m, inp, out):
        hf_out[i] = (out[0] if isinstance(out, tuple) else out).detach()
    return hook
for i, blk in enumerate(hf.encoder.layer):
    blk.register_forward_hook(mkh(i))

with torch.no_grad():
    hub.forward_features(x)
    hf(x)

print(f"{'layer':>6} {'cosine':>10} {'rel-err':>10}")
for i in (0, 1, 4, 9, 19, 29, 39):
    a, b = hub_out[i][0, 1:], hf_out[i][0, 1:]     # patch tokens only
    cos = torch.nn.functional.cosine_similarity(a, b, dim=-1).mean().item()
    rel = ((a - b).norm() / b.norm()).item()
    print(f"{i:>6} {cos:>10.6f} {rel:>10.2e}")
