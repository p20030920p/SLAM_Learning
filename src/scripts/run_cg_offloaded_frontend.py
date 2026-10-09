"""Explicit sequential GPU model residency for original RAM+DINO+SAM+CLIP.

The pinned author checkout stays unchanged. A generated entry and unified diff
are bound to each receipt. This is a resource variant, not a default execution
or a claim of numerical equivalence to the default resident-model pipeline.
"""
import argparse
import ast
import difflib
import os
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--name', required=True)
parser.add_argument('--scene', default='office1')
parser.add_argument('--dataset-root', type=Path)
parser.add_argument('--end', type=int, default=2000)
parser.add_argument('--timeout', type=int, default=7200)
parser.add_argument('--memory-max', default='16G')
parser.add_argument('--swap-max', default='48G')
args = parser.parse_args()
assert args.end > 0 and args.end <= 2000 and args.end % 5 == 0
r = args.runtime.resolve()
assert Path(args.name).name == args.name and args.name not in ('.', '..')
source = r / 'upstream/conceptgraphs'
if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip():
    raise RuntimeError('Author checkout must be clean')
commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
assert commit == '93277a02bd89171f8121e84203121cf7af9ebb5d'
# WSL NVML may omit active CUDA PIDs. Also reject any other task-owned entry.
active = subprocess.check_output(['ps', '-eo', 'pid,args'], text=True).splitlines()
entries = ('generate_gsa_results.py', 'application/semantic_segmentation.py')
for line in active:
    if any(entry in line for entry in entries) and 'python' in line:
        raise RuntimeError('An author GPU entry is already active: ' + line)
dataset = (args.dataset_root or r / 'data/replica-full/Replica').resolve()
assert dataset.is_relative_to(r), 'Use this runtime or an isolated fixture inside it'
scene = dataset / args.scene
for name in ['gsa_detections_ram_withbg_allclasses', 'gsa_vis_ram_withbg_allclasses',
             'gsa_classes_ram_withbg_allclasses.json']:
    if (scene / name).exists():
        raise FileExistsError('Preserve previous frontend before retry: ' + str(scene / name))
variant = r / 'variants' / args.name
variant.mkdir(parents=True, exist_ok=False)
original = (source / 'conceptgraph/scripts/generate_gsa_results.py').read_text()
edited = original

def replace(old, new):
    global edited
    assert edited.count(old) == 1, repr(old)
    edited = edited.replace(old, new, 1)

replace('def main(args: argparse.Namespace):\n', '''def _resource_place(module, device):
    module.to(device)
    if str(device) == "cpu":
        torch.cuda.empty_cache()


def main(args: argparse.Namespace):
    assert args.class_set == "ram" and args.detector == "dino" and args.sam_variant == "sam"
    assert str(args.device).startswith("cuda")
    print("RESOURCE VARIANT: sequential GPU residency; original CUDA forwards/weights/settings retained", flush=True)
''')
replace('''        device=args.device
    )

    ### Initialize the SAM model''', '''        device=args.device
    )
    _resource_place(grounding_dino_model.model, "cpu")

    ### Initialize the SAM model''')
replace('    clip_model = clip_model.to(args.device)\n', '    clip_model = clip_model.to("cpu")\n')
replace('        tagging_model = tagging_model.eval().to(args.device)\n',
        '        tagging_model = tagging_model.eval().to("cpu")\n')
replace('                res = inference_ram(raw_image , tagging_model)\n', '''                if idx < 3: print(f"residency frame={idx} RAM begin", flush=True)
                _resource_place(tagging_model, args.device)
                res = inference_ram(raw_image , tagging_model)
                _resource_place(tagging_model, "cpu")
''')
replace('''                detections = grounding_dino_model.predict_with_classes(
''', '''                if idx < 3: print(f"residency frame={idx} DINO begin", flush=True)
                _resource_place(grounding_dino_model.model, args.device)
                detections = grounding_dino_model.predict_with_classes(
''')
replace('''                    text_threshold=args.text_threshold,
                )
''', '''                    text_threshold=args.text_threshold,
                )
                _resource_place(grounding_dino_model.model, "cpu")
''')
replace('''                detections.mask = get_sam_segmentation_from_xyxy(
''', '''                if idx < 3: print(f"residency frame={idx} SAM begin", flush=True)
                detections.mask = get_sam_segmentation_from_xyxy(
''')
replace('                # Compute and save the clip features of detections  \n'
        '''                image_crops, image_feats, text_feats = compute_clip_features(
                    image_rgb, detections, clip_model, clip_preprocess, clip_tokenizer, classes, args.device)
''', '''                # Compute and save the clip features of detections
                if idx < 3: print(f"residency frame={idx} CLIP begin", flush=True)
                _resource_place(clip_model, args.device)
                image_crops, image_feats, text_feats = compute_clip_features(
                    image_rgb, detections, clip_model, clip_preprocess, clip_tokenizer, classes, args.device)
                _resource_place(clip_model, "cpu")
''')
ast.parse(edited)
entry = variant / 'generate_gsa_results.py'
entry.write_text(edited)
diff = variant / 'model-residency-compatibility.diff'
diff.write_text(''.join(difflib.unified_diff(original.splitlines(True), edited.splitlines(True),
    fromfile='author/generate_gsa_results.py', tofile='compatibility/generate_gsa_results.py')))
os.environ.pop('PYTORCH_CUDA_ALLOC_CONF', None)
os.environ.update(OMP_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', MKL_NUM_THREADS='8', WANDB_MODE='disabled',
    HF_HUB_CACHE=str(r / 'cache/huggingface/hub'), GSA_PATH=str(r / 'dependencies/Grounded-Segment-Anything'))
scope = (f'Replica {args.scene}, start=0,end={args.end},stride=5: {args.end // 5} frames; '
    'generated source copy explicitly offloads RAM, DINO and CLIP to CPU between their original CUDA forward passes; '
    'SAM stays CUDA-resident. No weights, dtypes, prompts, thresholds, masks, classes or frame-selection changes. '
    'Unified diff and generated entry recorded. Resource compatibility variant; numerical equivalence and default memory behavior unproven. '
    f'RAM/swap bounds {args.memory_max}/{args.swap_max}; no semantic evaluation in this frontend entry.')
command = [r / 'envs/conceptgraphs/bin/python', entry, '--dataset_root', dataset,
    '--dataset_config', source / 'conceptgraph/dataset/dataconfigs/replica/replica.yaml',
    '--scene_id', args.scene, '--class_set', 'ram', '--stride', '5', '--end', str(args.end),
    '--box_threshold', '0.2', '--text_threshold', '0.2', '--add_bg_classes', '--accumu_classes',
    '--exp_suffix', 'withbg_allclasses']
limited = ['systemd-run', '--user', '--scope', '--unit', 'slam-author-' + args.name,
    '-p', 'MemoryMax=' + args.memory_max, '-p', 'MemorySwapMax=' + args.swap_max, *map(str, command)]
recorder = [sys.executable, str(Path(__file__).with_name('record_command.py')),
    '--output', str(r / 'runs' / args.name), '--cwd', str(source / 'conceptgraph'), '--source', str(source),
    '--method', 'ConceptGraphs-Detect-sequential-GPU-residency', '--scope', scope, '--timeout', str(args.timeout)]
for path in [entry, diff, scene / 'gsa_classes_ram_withbg_allclasses.json',
             scene / f'gsa_detections_ram_withbg_allclasses/frame{args.end - 5:06d}.pkl.gz',
             scene / f'gsa_vis_ram_withbg_allclasses/frame{args.end - 5:06d}.jpg']:
    recorder += ['--artifact', str(path)]
raise SystemExit(subprocess.call([*recorder, '--', *limited]))
