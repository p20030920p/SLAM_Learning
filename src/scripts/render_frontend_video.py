"""Render saved, validated 2D outputs; this is playback, not a GUI recording."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--scene-root',type=Path,required=True)
parser.add_argument('--validation',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
validation=json.loads(args.validation.read_text())
assert validation['status']=='validated' and validation['processed_frames']==400
variant=validation['variant']
all_rgb=sorted((args.scene_root/'results').glob('frame*.jpg'))
assert len(all_rgb)==2000
rgb=all_rgb[::5]
assert len(rgb)==400
source_manifest={}
for path in rgb:
    visualization=args.scene_root/('gsa_vis_'+variant)/path.name
    expected=validation['artifacts'][str(visualization)]
    for source in [path,visualization]:
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        source_manifest[str(source)]={'bytes':source.stat().st_size,'sha256':digest}
    assert source_manifest[str(visualization)]==expected, 'Validated mask visualization changed: '+str(visualization)
args.output.mkdir(parents=True,exist_ok=False)
source_report=args.output/'source-manifest.json'
source_report.write_text(json.dumps(source_manifest,indent=2)+'\n')
sources=[]
for key,folder in [('rgb',args.scene_root/'results'),('masks',args.scene_root/('gsa_vis_'+variant))]:
    paths=[folder/path.name for path in rgb]
    assert all(path.is_file() for path in paths)
    # Paths belong to our fixed local Replica tree, not arbitrary shell input.
    assert all("'" not in str(path) and '\n' not in str(path) for path in paths)
    manifest=args.output/(key+'-frames.txt')
    manifest.write_text(''.join("file '"+str(path)+"'\nduration 0.1\n" for path in paths))
    sources.append(manifest)
video=args.output/(args.scene_root.name+'-rgb-and-sam-playback.mp4')
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
filters=("[0:v][1:v]hstack=inputs=2,scale=1920:544,pad=1920:608:0:32:color=0x111827,"
    "drawtext=fontfile="+font+":text='RGB input - Replica "+args.scene_root.name+"':x=16:y=7:fontsize=19:fontcolor=white,"
    "drawtext=fontfile="+font+":text='Author SAM masks - batch16 compatibility':x=976:y=7:fontsize=19:fontcolor=white,"
    "drawtext=fontfile="+font+":text='400 source samples at stride 5 | Saved 2D output playback | 3D and semantic accuracy not shown':x=16:y=582:fontsize=17:fontcolor=white[v]")
command=['ffmpeg','-nostdin','-n','-threads','2','-filter_complex_threads','1',
    '-f','concat','-safe','0','-i',str(sources[0]),'-f','concat','-safe','0','-i',str(sources[1]),
    '-filter_complex',filters,'-map','[v]','-r','10','-frames:v','400','-an',
    '-c:v','libx264','-threads','2','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
with (args.output/'ffmpeg.log').open('w') as log:
    subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
    '-show_entries','stream=width,height,nb_frames,r_frame_rate:format=duration','-of','json',str(video)],text=True))
assert int(probe['streams'][0]['nb_frames'])==400
assert abs(float(probe['format']['duration'])-40)<0.1
for number in [0,199,399]:
    subprocess.run(['ffmpeg','-nostdin','-n','-loglevel','error','-i',str(video),'-vf',
        'select=eq(n\\,'+str(number)+')','-frames:v','1',str(args.output/('sample-'+str(number)+'.png'))],check=True)
digest=hashlib.sha256(video.read_bytes()).hexdigest()
report={'status':'rendered','scene':args.scene_root.name,'source_frames':2000,'stride':5,'output_frames':400,
    'video':str(video),'video_sha256':digest,'bytes':video.stat().st_size,'ffprobe':probe,'command':command,
    'validation_source':str(args.validation),'validation_sha256':hashlib.sha256(args.validation.read_bytes()).hexdigest(),
    'source_manifest':str(source_report),'source_manifest_sha256':hashlib.sha256(source_report.read_bytes()).hexdigest(),
    'validated_visualizations_rehashed':400,'rgb_sources_hashed':400,
    'scope':'Real saved RGB and author SAM/CLIP frontend output playback. Explicit batch16 resource compatibility. Not an interactive-window recording, 3D map or semantic-accuracy evaluation.'}
(args.output/'media.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:report[key] for key in ['status','output_frames','video','video_sha256','bytes','scope']}),flush=True)
