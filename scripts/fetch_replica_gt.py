"""Download the official 17-part original Replica release, then stream-extract it.

Rendered NICE-SLAM RGB-D does not include the original 3D semantic ground truth.
This uses the same public release parts as the author's download.sh. Curl can
resume after interruption. Large assets stay outside the documentation checkout.
"""
import argparse
import concurrent.futures
import gzip
import hashlib
import io
import json
import subprocess
import tarfile
import urllib.request
from pathlib import Path

def sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):digest.update(block)
    return digest.hexdigest()

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
args=parser.parse_args()
r=args.runtime.resolve();downloads=r/'downloads/replica-original'
downloads.mkdir(parents=True,exist_ok=True)
metadata=json.load(urllib.request.urlopen('https://api.github.com/repos/facebookresearch/Replica-Dataset/releases/tags/v1.0',timeout=30))
(downloads/'release.json').write_text(json.dumps(metadata,indent=2)+'\n')
assets=sorted([asset for asset in metadata['assets'] if asset['name'].startswith('replica_v1_0.tar.gz.part')],key=lambda x:x['name'])
assert len(assets)==17
def fetch(asset):
    target=downloads/asset['name']
    if not target.exists() or target.stat().st_size!=asset['size']:
        partial=target.with_suffix(target.suffix+'.partial')
        subprocess.run(['curl','-L','--fail','--retry','3','--continue-at','-',
                        '--connect-timeout','30','--speed-limit','1024','--speed-time','120',
                        '--silent','--show-error',asset['browser_download_url'],'-o',str(partial)],check=True)
        if partial.stat().st_size!=asset['size']:raise RuntimeError('Incomplete '+asset['name'])
        partial.rename(target)
    digest=sha256(target)
    if asset.get('digest') and asset['digest']!='sha256:'+digest:raise RuntimeError('Author asset digest mismatch')
    print('Verified complete part: '+asset['name'],flush=True)
    return {'name':asset['name'],'bytes':asset['size'],'sha256':digest,'url':asset['browser_download_url'],
            'author_digest':asset.get('digest')}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: manifest=list(pool.map(fetch,assets))
(r/'replica-original-parts-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

class Parts(io.RawIOBase):
    def __init__(self,paths):self.paths=iter(paths);self.current=None
    def readable(self):return True
    def read(self,size=-1):
        if size<0:raise ValueError('Bounded reads required')
        result=bytearray()
        while len(result)<size:
            if self.current is None:
                try:self.current=next(self.paths).open('rb')
                except StopIteration:break
            block=self.current.read(size-len(result))
            if block:result.extend(block)
            else:self.current.close();self.current=None
        return bytes(result)
destination=r/'data/replica-original'
destination.mkdir(parents=True,exist_ok=True)
stream=Parts([downloads/asset['name'] for asset in assets])
with gzip.GzipFile(fileobj=stream) as decompressed:
    with tarfile.open(fileobj=decompressed,mode='r|') as archive:
        for member in archive:
            target=(destination/member.name).resolve()
            if not target.is_relative_to(destination.resolve()):raise ValueError('Unsafe archive path')
            if not (member.isfile() or member.isdir()):raise ValueError('Unexpected non-data tar member')
            archive.extract(member,path=destination)
    while decompressed.read(4*1024*1024):pass  # Consume footer and verify full gzip CRC.
print('Original Replica release fully extracted with gzip CRC verified',flush=True)
roots=list(destination.rglob('room0/habitat/mesh_semantic.ply'))
if len(roots)!=1:raise RuntimeError('Cannot uniquely find original room0 semantics')
dataset_root=roots[0].parents[2]
result={'root':str(dataset_root),'release':'v1.0','gzip_crc':'verified','scenes':{}}
for scene in ['office0','office1','office2','office3','office4','room0','room1','room2']:
    semantic=dataset_root/scene/'habitat/mesh_semantic.ply'
    info=dataset_root/scene/'habitat/info_semantic.json'
    result['scenes'][scene]={'mesh':str(semantic),'mesh_sha256':sha256(semantic),
                             'info_exists':info.is_file()}
(r/'replica-original-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
