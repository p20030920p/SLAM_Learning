"""Download/checksum author releases, keeping unlabeled demonstrations separate."""
import argparse
import concurrent.futures
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--runtime',type=Path,required=True)
parser.add_argument('--qualitative-only',action='store_true',help='Fetch kthcampus/twofloor without GT; never use them for accuracy scores')
args=parser.parse_args()
r=args.runtime
metadata=json.load(urllib.request.urlopen('https://zenodo.org/api/records/10886629',timeout=30))
(r/'downloads/zenodo-10886629.json').write_text(json.dumps(metadata,indent=2)+'\n')
def fetch(item):
    target=r/'downloads'/item['key']
    temporary=target.with_suffix('.zip.partial')
    if not target.exists():
        offset=temporary.stat().st_size if temporary.exists() else 0
        if offset>item['size']:raise RuntimeError(f'Oversized partial file: {temporary}')
        if offset<item['size']:
            request=urllib.request.Request(item['links']['self'],headers={'Range':f'bytes={offset}-'} if offset else {})
            with urllib.request.urlopen(request,timeout=120) as source:
                append=offset>0 and source.status==206
                if append and not source.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
                    raise RuntimeError('Unexpected HTTP Content-Range')
                print(f'{item["key"]}: resume offset {offset if append else 0}',flush=True)
                with temporary.open('ab' if append else 'wb') as output:
                    while block:=source.read(1024*1024):output.write(block)
        temporary.rename(target)
    digest=hashlib.md5()
    with target.open('rb') as source:
        for block in iter(lambda:source.read(4*1024*1024),b''):digest.update(block)
    actual='md5:'+digest.hexdigest()
    if actual!=item['checksum'] or target.stat().st_size!=item['size']:raise RuntimeError(f'Checksum mismatch: {target}')
    destination=r/('data/benchmark-qualitative' if args.qualitative_only else 'data/benchmark-released')
    destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target) as archive:
        for member in archive.infolist():
            if not (destination/member.filename).resolve().is_relative_to(destination.resolve()):raise ValueError(member.filename)
        bad=archive.testzip()
        if bad:raise RuntimeError('Zip CRC failed: '+bad)
        archive.extractall(destination)
    scene=target.stem
    folder=destination/scene
    count=len(list((folder/'pcd').glob('*.pcd')))
    expected={'kthcampus':18,'twofloor':3305}.get(scene)
    has_gt=(folder/'gt_cloud.pcd').is_file()
    if not count or (expected is not None and count!=expected) or (not args.qualitative_only and not has_gt):
        raise RuntimeError(f'Incomplete input: {folder}')
    return {'name':scene,'url':item['links']['self'],'bytes':item['size'],'checksum':actual,'zip_crc':'verified',
            'scans':count,'root':str(folder),'has_ground_truth':has_gt,
            'scope':'Qualitative only; no accuracy GT' if args.qualitative_only else 'Author labeled release'}
names=['kthcampus.zip','twofloor.zip'] if args.qualitative_only else ['05.zip','av2.zip','semindoor.zip']
items=[item for item in metadata['files'] if item['key'] in names]
assert len(items)==len(names),'Missing author release metadata'
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(fetch,items))
(r/('benchmark-qualitative-manifest.json' if args.qualitative_only else 'benchmark-released-manifest.json')).write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
