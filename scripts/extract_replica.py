"""Extract the complete author-linked Replica archive and record all 8 scenes."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
args=parser.parse_args()
r=args.runtime
destination=r/'data/replica-full'
destination.mkdir(parents=True,exist_ok=False)
archive=r/'downloads/Replica.zip'
with zipfile.ZipFile(archive) as zip:
    # Archive is downloaded from the author URL; still reject paths escaping the destination.
    for item in zip.infolist():
        if not (destination/item.filename).resolve().is_relative_to(destination.resolve()):raise ValueError(item.filename)
    zip.extractall(destination)
root=destination/'Replica'
if not root.is_dir():raise FileNotFoundError(root)
camera=root/'cam_params.json'
if not camera.exists():shutil.copy2(Path(__file__).resolve().parents[1]/'config/replica-cam-params.json',camera)
manifest={}
for scene in ['office0','office1','office2','office3','office4','room0','room1','room2']:
    folder=root/scene
    rgb=sorted((folder/'results').glob('frame*.jpg'))
    depth=sorted((folder/'results').glob('depth*.png'))
    poses=(folder/'traj.txt').read_text().splitlines()
    if len(rgb)!=2000 or len(depth)!=2000 or len(poses)!=2000:raise RuntimeError((scene,len(rgb),len(depth),len(poses)))
    manifest[scene]={'rgb_frames':len(rgb),'depth_frames':len(depth),'poses':len(poses)}
digest=hashlib.sha256()
with archive.open('rb') as stream:
    for block in iter(lambda:stream.read(4*1024*1024),b''):digest.update(block)
result={'url':'https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip',
        'archive_bytes':archive.stat().st_size,'archive_sha256':digest.hexdigest(),
        'root':str(root.resolve()),'scenes':manifest,
        'camera_json_sha256':hashlib.sha256(camera.read_bytes()).hexdigest()}
(r/'replica-full-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
