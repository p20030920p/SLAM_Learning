"""Run both original methods and original evaluation on all released labeled data.

Uses author README BeautyMap settings for KITTI and semi-indoor. Argoverse2
uses the outdoor KITTI settings as an explicitly recorded parameter choice;
this is not a claim that all paper hyperparameters/ablations are reproduced.
"""
from __future__ import annotations
import argparse
import difflib
import json
import shutil
import subprocess
import sys
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--name',default='released-lidar-01')
    args=parser.parse_args()
    r=args.runtime.resolve(); root=r/'runs'/args.name
    root.mkdir(parents=True,exist_ok=False)
    record=Path(__file__).with_name('record_command.py')
    def run(name,source,method,scope,command,artifact):
        return subprocess.run([sys.executable,str(record),'--output',str(root/name),'--cwd',str(source),
            '--method',method,'--scope',scope,'--artifact',str(artifact),'--',
            'systemd-run','--user','--scope','--unit','slam-author-'+args.name+'-'+name,
            '-p','MemoryMax=8G','-p','MemorySwapMax=2G',*map(str,command)]).returncode
    sequences=['00','05','av2','semindoor']; outcomes={}
    for seq in sequences:
        data=root/'dataset'/seq;data.mkdir(parents=True)
        original=r/'data/00-pristine' if seq=='00' else r/'data/benchmark-released'/seq
        shutil.copy2(original/'gt_cloud.pcd',data/'gt_cloud.pcd')
        if seq=='00':
            shutil.copy2(r/'runs/dufomap-cpp-original-01/input/00/dufomap_output.pcd',data/'dufomap_output.pcd')
            shutil.copy2(r/'runs/beautymap-original-01/input/00/beautymap_output.pcd',data/'beautymap_output.pcd')
            outcomes[seq]={'dufomap':'existing original run, same SHA-256','beautymap':'existing original run, same SHA-256'}
        else:
            outcomes[seq]={}
            for method in ['dufomap','beautymap']:
                input_dir=root/'inputs'/seq/method
                shutil.copytree(original,input_dir)
                source=r/'upstream'/method
                artifact=input_dir/(method+'_output.pcd')
                if method=='dufomap':
                    command=[r/'build/dufomap-gcc11/dufomap_run',input_dir,source/'assets/config.toml']
                    scope='All released '+seq+' scans, original C++ and default author config, g++-11 compatibility toolchain'
                else:
                    settings=['10','0.5','0.2'] if seq=='semindoor' else ['40','1','0.5']
                    command=[r/'envs/lidar/bin/python',source/'main.py','--data_dir',input_dir,
                             '--dis_range',settings[0],'--xy_resolution',settings[1],'--h_res',settings[2]]
                    scope='All released '+seq+' scans; original Python; settings '+str(settings)
                    if seq=='av2':scope+='; outdoor README settings transferred, not independently paper-verified'
                code=run(seq+'-'+method,source,method,scope,command,artifact)
                outcomes[seq][method]=code
                if code==0:shutil.copy2(artifact,data/artifact.name)
        for method in ['dufomap','beautymap']:
            if not (data/(method+'_output.pcd')).exists():continue
            artifact=data/'eval'/(method+'_output_exportGT.pcd')
            outcomes[seq][method+'-export']=run(seq+'-'+method+'-export',r/'upstream/dynamicmap',
                'DynamicMap-export','Author PCL nearest-neighbor labels, 0.05m, all GT points',
                [r/'build/dynamicmap/export_eval_pcd',data,method+'_output.pcd','0.05'],artifact)
        (root/'outcomes.json').write_text(json.dumps(outcomes,indent=2)+'\n')
    complete=[seq for seq in sequences if all((root/'dataset'/seq/'eval'/(method+'_output_exportGT.pcd')).exists()
                                               for method in ['dufomap','beautymap'])]
    scripts=root/'author-scripts';shutil.copytree(r/'upstream/dynamicmap/scripts',scripts)
    path=scripts/'py/eval/evaluate_all.py';original=path.read_text()
    settings={'Result_Folder':str(root/'dataset'),'algorithms':['dufomap','beautymap'],'all_seqs':complete}
    edited=''.join(next((key+' = '+repr(value)+'\n' for key,value in settings.items() if line.startswith(key+' = ')),line)
                   for line in original.splitlines(True))
    path.write_text(edited)
    (root/'evaluation-config.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),edited.splitlines(True),
                                         fromfile='author/evaluate_all.py',tofile='configured/evaluate_all.py')))
    subprocess.run([sys.executable,str(record),'--output',str(root/'scores'),'--cwd',str(r/'upstream/dynamicmap'),
                    '--method','DynamicMap-score','--scope','Author formulas; complete released sequences '+repr(complete),
                    '--',str(r/'envs/lidar/bin/python'),str(path)],check=True)
    if len(complete)!=len(sequences):raise RuntimeError('Some author runs/exports failed; see outcomes.json')

if __name__=='__main__':main()
