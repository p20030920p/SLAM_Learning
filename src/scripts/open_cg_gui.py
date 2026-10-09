"""Open the unchanged author viewer on a hash-verified completed map."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
parser.add_argument('--validation',type=Path,required=True)
parser.add_argument('--name',required=True)
parser.add_argument('--software-rendering',action='store_true')
args=parser.parse_args()
r=args.runtime.resolve()
validation=json.loads(args.validation.read_text())
assert validation['status']=='validated' and validation['post_objects']>0
maps=[Path(name) for name in validation['artifacts'] if name.endswith('_post.pkl.gz')]
assert len(maps)==1
path=maps[0]
assert path.resolve().is_relative_to(r/'data')
digest=hashlib.sha256()
with path.open('rb') as stream:
    for block in iter(lambda:stream.read(4*1024*1024),b''):digest.update(block)
assert digest.hexdigest()==validation['artifacts'][str(path)]['sha256']
source=r/'upstream/conceptgraphs'
work=r/'runs'/(args.name+'-work')
assert work.resolve().is_relative_to(r/'runs')
work.mkdir(exist_ok=False)
if args.software_rendering:os.environ['LIBGL_ALWAYS_SOFTWARE']='1'
os.environ.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
command=[r/'envs/conceptgraphs/bin/python',source/'conceptgraph/scripts/visualize_cfslam_results.py',
    '--result_path',path,'--no_clip']
limited=['systemd-run','--user','--scope','--unit','slam-author-'+args.name,
    '-p','MemoryMax=8G','-p','MemorySwapMax=40G',*map(str,command)]
scope=('Unchanged author GUI on a completed, hash-verified '+validation['scene']+' map. '
    'No CLIP model/query or relationship graph; visualization only, not a semantic-accuracy experiment. '
    'Original viewer downsamples display geometry to 0.05m; saved map unchanged. Software OpenGL='+str(args.software_rendering))
raise SystemExit(subprocess.call([sys.executable,str(Path(__file__).with_name('record_command.py')),
    '--output',str(r/'runs'/args.name),'--cwd',str(work),'--source',str(source),
    '--method','ConceptGraphs-original-GUI','--scope',scope,'--timeout','3600','--artifact',str(path),'--',*limited]))
