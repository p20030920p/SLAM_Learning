"""Publish small execution evidence; keep large data/weights/results local."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

def sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b''): digest.update(chunk)
    return digest.hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for record in sorted((args.runtime/'runs').rglob('record.json')):
        target=args.output/'runs'/record.relative_to(args.runtime/'runs')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(record,target)
        log=record.with_name('run.log')
        if log.is_file(): shutil.copy2(log,target.with_name('run.log'))
    for name in ['lidar-environment.txt','conceptgraphs-environment.txt','hovsg-environment.txt','workspace.json',
                 'replica-full-manifest.json','benchmark-released-manifest.json','clip-cache-provenance.json']:
        source=args.runtime/name
        if source.is_file(): shutil.copy2(source,args.output/name)
    for source in (args.runtime/'runs').glob('*/setup.log'):
        target=args.output/'setup-logs'/source.parent.name/'setup.log'
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
    environment_log=args.runtime/'hovsg-author-environment-create.log'
    if environment_log.is_file():
        target=args.output/'setup-logs/hovsg-author-environment-create.log'
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(environment_log,target)
    weights=args.runtime/'weights/SHA256SUMS'
    if weights.is_file():shutil.copy2(weights,args.output/'weights-SHA256SUMS.txt')
    manifest={}
    paths=list((args.runtime/'data/00-pristine').rglob('*'))
    paths+=list((args.runtime/'runs').rglob('*.pcd'))
    paths+=list((args.runtime/'runs').rglob('*.diff'))
    paths+=list((args.runtime/'build').glob('*/dufomap_run'))
    paths+=list((args.runtime/'build').glob('*/export_eval_pcd'))
    for path in sorted(paths):
        if not path.is_file(): continue
        relative=path.relative_to(args.runtime).as_posix()
        manifest[relative]={'bytes':path.stat().st_size,'sha256':sha256(path)}
        if path.suffix=='.diff':
            target=args.output/'configuration-diffs'/path.name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,target)
    (args.output/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    sources={}
    for source in sorted((args.runtime/'upstream').iterdir()):
        if not (source/'.git').exists():continue
        def git(*parts):return subprocess.check_output(['git','-C',str(source),*parts],text=True).strip()
        sources[source.name]={'commit':git('rev-parse','HEAD'),'origin':git('remote','get-url','origin'),
                              'status':git('status','--porcelain')}
    (args.output/'source-status.json').write_text(json.dumps(sources,indent=2)+'\n')
    print(f'Collected {len(manifest)} artifact hashes; source statuses: {sources}')

if __name__=='__main__':main()
