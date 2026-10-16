"""Package matched live 3D A/B runs and score common scan timestamps."""
import argparse
import csv
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation, Slerp

from package_frozen_practice import ROOT, read, write, sha, windows_path, score as grid_score
from package_session import gif, probe
from render_cleaning_review import render

SUITE=ROOT / "results/reference/practice-3d-visible-20261016"
METHODS=("raw","dufomap","beautymap")


def copy_sources(run, out):
    out.mkdir(parents=True,exist_ok=True)
    for pattern in ("*.json","*.jsonl","*.csv","*.rviz","recording.started","recording.stopped"):
        for p in run.glob(pattern):
            if p.is_file():shutil.copyfile(p,out/p.name)
    shutil.copytree(run/'logs',out/'logs',dirs_exist_ok=True)


def video(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    subprocess.run(['ffmpeg','-v','error','-i',str(target),'-f','null','-'],check=True)
    timing=gif(target,target.with_suffix('.gif'))
    midpoint=float(probe(target)['format']['duration'])/2
    subprocess.run(['ffmpeg','-v','error','-ss',str(midpoint),'-i',str(target),'-frames:v','1','-y',str(target.with_suffix('.png'))],check=True)
    return timing


def seal(out, value):
    value['artifacts']={p.relative_to(out).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size}
                        for p in out.rglob('*') if p.is_file() and p!=out/'record.json' and p.suffix!='.pcd'}
    write(out/'record.json',value)


def package_a(scene,run,maps):
    out=SUITE/(scene+'-A')
    assert not (out/'record.json').exists()
    assert read(run/'metrics.json')['status']=='completed'
    processing=read(maps/'record.json')
    assert sha(run/'mapping-clouds.npz')==processing['input_sha256']
    copy_sources(run,out)
    (out/'maps').mkdir(exist_ok=True)
    shutil.copyfile(maps/'record.json',out/'maps/record.json')
    for method in METHODS:
        target=out/'maps'/method;target.mkdir(exist_ok=True)
        for name in ('map.yaml','map.pgm','points.npy'):shutil.copyfile(maps/method/name,target/name)
    if scene=='dynamic':
        subprocess.run([sys.executable,str(Path(__file__).with_name('score_map_labels.py')),str(run),str(maps)],check=True)
        labels=np.load(maps/'point-labels.npy')
        shutil.copyfile(maps/'point-label-scores.json',out/'point-label-scores.json')
    else:
        with np.load(run/'mapping-clouds.npz') as archive:
            labels=np.concatenate([np.where(np.linalg.norm(archive[f'scan_{i:04d}'],axis=1)>=.45,0,-1) for i in processing['selected_scan_ids']])
    raw=np.load(maps/'raw/points.npy');assert len(raw)==len(labels)
    scores={}
    raw_voxels=set(map(tuple,np.unique(np.floor(raw/.15).astype(int),axis=0)))
    for method in METHODS:
        points=np.load(maps/method/'points.npy')
        retained=cKDTree(points).query(raw,workers=2)[0]<2e-5
        voxels=set(map(tuple,np.unique(np.floor(points/.15).astype(int),axis=0)))
        scores[method]={'static_retention':float(retained[labels==0].mean()),
                        'dynamic_removal':float((~retained[labels==1]).mean()) if (labels==1).any() else None,
                        'points':len(points),'occupied_15cm_voxels':len(voxels),
                        'voxel_overlap_with_raw':len(voxels & raw_voxels)/len(voxels | raw_voxels)}
    write(out/'map-score.json',{'methods':scores,'static_points':int((labels==0).sum()),'dynamic_points':int((labels==1).sum()),
                               'scope':'Same selected A points; ignore self returns below .45 m; dynamic labels from synchronized moving-box geometry; DA/SA are point retention/removal ratios.'})
    timing=video(run/'execution.mp4',out/'execution.mp4')
    render(scene,maps=out/'maps',output=out/'cleaning-review',source_record=out.relative_to(ROOT).as_posix()+'/record.json')
    seal(out,{'kind':'live_3d_acquisition_and_author_cleaning','status':'executed','source_run':str(run),
              'provided_mapping_poses':True,'scope':'Live 16-channel XYZ acquisition in Orbit view; native DUFOMap/BeautyMap run offline on identical A scans with provided simulation poses; not full 3D SLAM.',
              'mapping_archive':{'path':str(run/'mapping-clouds.npz'),'sha256':sha(run/'mapping-clouds.npz')},
              'map_quality':scores,'timing':timing})
    print('PACKAGED A: '+scene,flush=True)


def prepare_b(scene):
    a=SUITE/(('static' if scene=='change' else scene)+'-A')
    maps=a/'maps'
    assert (a/'record.json').exists()
    for method in METHODS:
        p=np.load(maps/method/'points.npy').astype('<f4')
        header=('# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\n'
                f'WIDTH {len(p)}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS {len(p)}\nDATA binary\n').encode()
        (maps/method/'map-3d.pcd').write_bytes(header+p.tobytes())
    out=SUITE/(scene+'-B');out.mkdir(parents=True,exist_ok=True)
    paths=[maps/method/name for method in METHODS for name in ('points.npy','map-3d.pcd','map.yaml','map.pgm')]
    frozen={str(path):sha(path) for path in paths}
    write(out/'frozen-inputs.json',{'A_record':a.relative_to(ROOT).as_posix()+'/record.json','map_sha256':frozen})
    marker='maps-'+('static' if scene=='change' else scene)+'-latest.json'
    write(ROOT/'.cache/presentation'/marker,{'path':'/mnt/'+maps.drive[0].lower()+'/'+maps.as_posix()[3:]})


def scan_score(run):
    begin,end=read(run/'metrics.json')['recording_interval_sim_s']
    native={};invalid={}
    for method in METHODS:
        with (run/(method+'-poses3d.csv')).open() as stream:rows=list(csv.DictReader(stream))
        columns=['stamp_s','estimate_x','estimate_y','estimate_z','estimate_qx','estimate_qy','estimate_qz','estimate_qw']
        selected={};bad=0
        for row in rows:
            a=np.array([float(row[k]) for k in columns])
            if not begin+5<=a[0]<end:continue
            if not np.isfinite(a).all() or np.linalg.norm(a[4:])<.5:bad+=1;continue
            selected[round(a[0],6)]=a
        native[method]=selected;invalid[method]=bad
    common=sorted(set.intersection(*(set(values) for values in native.values())))
    truth=[__import__('json').loads(line) for line in (run/'truth.jsonl').read_text().splitlines()]
    tt,ids=np.unique([row['stamp_s'] for row in truth],return_index=True)
    xyz=np.array([row['xyz'] for row in truth])[ids]
    rotations=Rotation.from_quat(np.array([row['xyzw'] for row in truth])[ids])
    target=np.column_stack([np.interp(common,tt,xyz[:,i]) for i in range(3)])
    target_rotation=Slerp(tt,rotations)(common)
    source_times={round(t,6) for t in read(run/'input-cloud-stamps.json') if begin+5<=t<end}
    scores={}
    for method in METHODS:
        a=np.array([native[method][t] for t in common])
        distance=np.linalg.norm(a[:,1:4]-target,axis=1)
        angles=np.rad2deg((target_rotation.inv()*Rotation.from_quat(a[:,4:])).magnitude())
        scores[method]={'position_rmse_m':float(np.sqrt(np.mean(distance**2))),
                       'rotation_rmse_deg':float(np.sqrt(np.mean(angles**2))),
                       'common_samples':len(common),'valid_native_samples':len(native[method]),'invalid_rows':invalid[method],
                       'scan_output_coverage':len(set(native[method]) & source_times)/len(source_times)}
    return {'dimension':'3D','scope':'Exact common native scan-header timestamps after 5 s; truth interpolated at those same times. No holding an earlier pose against later truth. No trajectory alignment; truth only for scoring.',
            'common_scan_samples':len(common),'observed_input_scan_samples':len(source_times),'methods':scores}


def package_b(scene,run):
    out=SUITE/(scene+'-B');assert not (out/'record.json').exists()
    assert read(run/'metrics.json')['status']=='completed'
    frozen=read(out/'frozen-inputs.json')
    for path,expected in frozen['map_sha256'].items():assert sha(Path(path))==expected
    copy_sources(run,out)
    scores=scan_score(run);write(out/'score.json',scores)
    write(out/'grid-score-diagnostic.json',grid_score(run,METHODS,'3D'))
    timing={method:video(run/'executions'/(method+'.mp4'),out/'executions'/(method+'.mp4')) for method in METHODS}
    cases=read(run/'cases.json')
    for method in METHODS:
        path=windows_path(cases[method]['map_pcd']);assert str(path) in frozen['map_sha256']
    hashes={method:sha(windows_path(cases[method]['map_pcd'])) for method in METHODS}
    seal(out,{'kind':'live_3d_frozen_map_localization','status':'executed','source_run':str(run),
              'frozen_maps_unchanged':True,'truth_input_to_localizers':False,'score':scores,'timing':timing,
              'map_pcd_sha256':hashes,'identical_raw_dufomap_map':hashes['raw']==hashes['dufomap'],
              'scope':'Same fresh B stream and native GICP parameters; separate processes can receive different subsets. Single exploratory trial, not proof of causal benefit in an unstable corridor.'})
    print('PACKAGED B: '+scene,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['A','prepare-B','B']);parser.add_argument('scene');parser.add_argument('run',nargs='?',type=Path);parser.add_argument('maps',nargs='?',type=Path)
    args=parser.parse_args()
    if args.action=='A':package_a(args.scene,args.run,args.maps)
    elif args.action=='prepare-B':prepare_b(args.scene)
    else:package_b(args.scene,args.run)
