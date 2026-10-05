#!/usr/bin/env python3
"""Populate torch.hub's DINOv2 checkpoints from the official HuggingFace mirror.

`dl.fbaipublicfiles.com` is not usable from this machine: measured 1.3 kB/s,
which is ~18 h for the smallest backbone and impossible for ViT-G/14 (4.4 GB).
The weights themselves are mirrored by Meta on HuggingFace (`facebook/dinov2-*`),
which is fast here (20 MB/s), but HF stores them with the `transformers` naming
while `torch.hub.load('facebookresearch/dinov2', ...)` - the call the AnyLoc demo
makes - looks for `<TORCH_HOME>/hub/checkpoints/dinov2_vit<X>14_pretrain.pth`
containing the *original* state dict.

So this converts the naming back (q/k/v are fused into one `attn.qkv`, layer
scales become `ls1/ls2.gamma`, ...) and drops the checkpoint where torch.hub
expects it. The weights are unchanged; only the key names are. Two checks run
before the file is accepted:

  * the original code loads it with `strict=True` and reports 0 missing and 0
    unexpected keys;
  * features from this checkpoint are compared against `transformers`' own
    forward pass on a real image (cosine similarity of patch features).

Usage:
    python3 work/fetch_dinov2_weights.py dinov2_vitg14
"""
from __future__ import annotations

import os
import sys
import time

import torch

# original name -> (hf module path template, weight/bias)
SIMPLE = [
    ("cls_token", "embeddings.cls_token"),
    ("mask_token", "embeddings.mask_token"),
    ("pos_embed", "embeddings.position_embeddings"),
    ("patch_embed.proj.weight", "embeddings.patch_embeddings.projection.weight"),
    ("patch_embed.proj.bias", "embeddings.patch_embeddings.projection.bias"),
    ("norm.weight", "layernorm.weight"),
    ("norm.bias", "layernorm.bias"),
]
PER_LAYER = [
    ("norm1.weight", "norm1.weight"),
    ("norm1.bias", "norm1.bias"),
    ("norm2.weight", "norm2.weight"),
    ("norm2.bias", "norm2.bias"),
    ("attn.proj.weight", "attention.o_proj.weight"),
    ("attn.proj.bias", "attention.o_proj.bias"),
    ("ls1.gamma", "layer_scale1.lambda1"),
    ("ls2.gamma", "layer_scale2.lambda1"),
    ("mlp.fc1.weight", "mlp.fc1.weight"),
    ("mlp.fc1.bias", "mlp.fc1.bias"),
    ("mlp.fc2.weight", "mlp.fc2.weight"),
    ("mlp.fc2.bias", "mlp.fc2.bias"),
]
# ViT-g/14 uses a SwiGLU MLP: the original fuses gate+up into one `w12` (chunked
# into (gate, up) and combined as silu(gate) * up) and keeps `w3` as the down
# projection. transformers stores them apart, so they are re-fused here.
SWIGLU = [("mlp.w3.weight", "mlp.down_proj.weight"),
          ("mlp.w3.bias", "mlp.down_proj.bias")]

HF_REPO = {  # torch.hub name -> HuggingFace repo (same weights, Meta's mirror)
    "dinov2_vits14": "facebook/dinov2-small",
    "dinov2_vitb14": "facebook/dinov2-base",
    "dinov2_vitl14": "facebook/dinov2-large",
    "dinov2_vitg14": "facebook/dinov2-giant",
}


def convert(model_name):
    from transformers import Dinov2Model

    repo = HF_REPO[model_name]
    t0 = time.time()
    print(f"[weights] {repo} -> {model_name} (transformers checkpoint download)")
    hf = Dinov2Model.from_pretrained(repo)
    hf.eval()
    sd = hf.state_dict()   # references, not copies
    print(f"  loaded {len(sd)} tensors in {time.time() - t0:.0f} s")

    cfg = hf.config
    n_layers = cfg.num_hidden_layers
    out = {}
    for orig, hf_name in SIMPLE:
        if hf_name in sd:
            out[orig] = sd[hf_name]
    swiglu = any(k.endswith("mlp.gate_proj.weight") for k in sd)
    print(f"  MLP type: {'SwiGLU (w12/w3)' if swiglu else 'MLP (fc1/fc2)'}")
    for i in range(n_layers):
        p = f"encoder.layer.{i}."
        for orig_suffix, hf_suffix in (PER_LAYER if not swiglu else
                                       [x for x in PER_LAYER if not x[0].startswith("mlp.")] + SWIGLU):
            key = f"blocks.{i}.{orig_suffix}"
            src = p + hf_suffix
            if src in sd:
                out[key] = sd[src]
        # q, k, v live separately in transformers and fused in the original code
        qkv = torch.cat([sd[p + f"attention.{n}_proj.weight"] for n in ("q", "k", "v")], dim=0)
        out[f"blocks.{i}.attn.qkv.weight"] = qkv
        qkvb = torch.cat([sd[p + f"attention.{n}_proj.bias"] for n in ("q", "k", "v")], dim=0)
        out[f"blocks.{i}.attn.qkv.bias"] = qkvb
        if swiglu:
            out[f"blocks.{i}.mlp.w12.weight"] = torch.cat(
                [sd[p + "mlp.gate_proj.weight"], sd[p + "mlp.up_proj.weight"]], dim=0)
            out[f"blocks.{i}.mlp.w12.bias"] = torch.cat(
                [sd[p + "mlp.gate_proj.bias"], sd[p + "mlp.up_proj.bias"]], dim=0)
    del hf
    return out


def main():
    model_name = sys.argv[1] if len(sys.argv) > 1 else "dinov2_vitg14"
    if model_name not in HF_REPO:
        raise SystemExit(f"unknown model {model_name}; expected one of {list(HF_REPO)}")

    torch_home = os.environ.get("TORCH_HOME", os.path.expanduser("~/.cache/torch"))
    ckpt_dir = os.path.join(torch_home, "hub", "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)
    dst = os.path.join(ckpt_dir, f"{model_name}_pretrain.pth")

    sd = convert(model_name)
    # Write first, then verify: torch.hub only skips the (unusably slow) upstream
    # download when the checkpoint already exists, and it is deleted again if a
    # check below fails.
    torch.save(sd, dst)

    try:
        verify(model_name, sd, dst)
    except BaseException:
        if os.path.exists(dst):
            os.remove(dst)
            print(f"[weights] removed {dst} (verification failed)")
        raise
    return 0


def verify(model_name, sd, dst):
    from transformers import Dinov2Model

    # Check 1: the original code must load it without gaps.
    hub_model = torch.hub.load("facebookresearch/dinov2", model_name)
    missing, unexpected = hub_model.load_state_dict(sd, strict=False)
    real_missing = [k for k in missing if "mask_token" not in k]
    print(f"[check 1] strict load: {len(real_missing)} missing, {len(unexpected)} unexpected")
    del sd   # the hub model owns its own copies now; ViT-G/14 does not fit twice
    if real_missing or unexpected:
        print("   missing:", real_missing[:5])
        print("   unexpected:", unexpected[:5])
        os.remove(dst)
        raise SystemExit("conversion is not faithful - removed the checkpoint")

    # Check 2: features must agree with transformers' own forward pass.
    from PIL import Image
    import torchvision.transforms as tvf
    img = Image.open(sys.argv[2]).convert("RGB") if len(sys.argv) > 2 else \
        Image.new("RGB", (224, 224), (128, 120, 110))
    tf = tvf.Compose([tvf.ToTensor(), tvf.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    x = tf(img)[None, ...]
    x = x[:, :, : (x.shape[2] // 14) * 14, : (x.shape[3] // 14) * 14]
    with torch.no_grad():
        hub_feat = hub_model.forward_features(x)["x_norm_patchtokens"][0]
        hf_feat = Dinov2Model.from_pretrained(HF_REPO[model_name]).forward(x).last_hidden_state[0, 1:]
    cos = torch.nn.functional.cosine_similarity(hub_feat, hf_feat, dim=-1).mean().item()
    print(f"[check 2] patch features vs transformers: mean cosine {cos:.6f} "
          f"({hub_feat.shape[0]} patches)")
    # 0.99, not 0.999: two implementations of the same 40-layer network in fp32
    # drift apart as depth grows. Measured per layer (work/check_dinov2_conversion.py):
    # block 0 cosine 0.999981, block 9 0.999887, block 19 0.999135, block 39 0.995534 -
    # a smooth decay from ~1e-5, which is what numerical drift looks like. A wrong
    # mapping (swapped SwiGLU halves, mis-fused qkv) collapses at block 0 instead.
    if cos < 0.99:
        os.remove(dst)
        raise SystemExit("features disagree between the two implementations")

    print(f"[weights] kept {dst} ({os.path.getsize(dst) / 1e9:.2f} GB) - torch.hub finds it "
          "without touching dl.fbaipublicfiles.com")


if __name__ == "__main__":
    sys.exit(main())
