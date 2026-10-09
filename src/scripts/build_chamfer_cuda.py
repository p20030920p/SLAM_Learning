"""Build the unchanged pinned chamferdist source with the local CUDA 11.8 toolkit."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
parser.add_argument('--name',required=True)
args=parser.parse_args()
r=args.runtime.resolve();source=r/'dependencies/chamferdist'
assert not subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True).strip()
root=r/'runs'/args.name
assert root.resolve().is_relative_to(r/'runs')
root.mkdir(exist_ok=False)
state={'status':'preparing_source','scope':'Dependency build only; no author algorithm execution'}
def save():(root/'outcomes.json').write_text(json.dumps(state,indent=2)+'\n')
def on_exception(kind,value,traceback):
    state.update(status='failed',error_type=kind.__name__,error=str(value));save()
    sys.__excepthook__(kind,value,traceback)
sys.excepthook=on_exception
save()
copy=root/'source';copy.mkdir()
manifest={}
for name in subprocess.check_output(['git','-C',str(source),'ls-files','-z']).decode().split('\0'):
    if not name:continue
    original=source/name;target=copy/name
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,target)
    digest=hashlib.sha256(original.read_bytes()).hexdigest()
    assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
    manifest[name]=digest
(root/'source-copy.json').write_text(json.dumps(manifest,indent=2)+'\n')
cuda=r/'envs/cuda118';python=r/'envs/conceptgraphs/bin/python'
os.environ.update(CUDA_HOME=str(cuda),PATH=str(cuda/'bin')+os.pathsep+os.environ['PATH'],
    LD_LIBRARY_PATH=str(cuda/'lib')+os.pathsep+os.environ.get('LD_LIBRARY_PATH',''),
    FORCE_CUDA='1',CUDA_VISIBLE_DEVICES='',TORCH_CUDA_ARCH_LIST='8.9',MAX_JOBS='2',CC='gcc-11',CXX='g++-11')
uv=shutil.which('uv') or str(Path.home()/'.local/bin/uv')
assert Path(uv).is_file(), 'uv executable is required'
command=['systemd-run','--user','--scope','--unit','slam-author-'+args.name,
    '-p','MemoryMax=6G','-p','MemorySwapMax=8G',uv,'--no-cache','pip','install',
    '--python',str(python),'--reinstall','--no-deps','--no-build-isolation',str(copy)]
state.update(status='building');save()
code=subprocess.call([sys.executable,str(Path(__file__).with_name('record_command.py')),
    '--output',str(root/'build'),'--cwd',str(copy),'--source',str(source),'--method','chamferdist-CUDA-build',
    '--scope','Unchanged tracked source copy; FORCE_CUDA=1, CUDA 11.8, arch 8.9, gcc11; no GPU allocation during compilation. Fixes original evaluator dependency, not its algorithm. Source hashes in source-copy.json.',
    '--timeout','1800','--',*command])
if code:
    state.update(status='failed',build_exit_code=code);save();raise SystemExit(code)
probe=subprocess.check_output([str(python),'-c',
    'import torch; from chamferdist import _C; assert hasattr(_C,"knn_check_version"); print("CUDA-only binding present:",_C.__file__)'],text=True)
(root/'compile-preflight.log').write_text(probe)
state.update(status='compiled_cuda_binding_present',build_exit_code=0,
    scope='CUDA-only binding is present; actual GPU KNN smoke test still required before evaluation');save()
print(probe,flush=True)
