"""Record one observed, viewable X11 window; inputs are controlled separately."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--window-id',type=lambda value:int(value,0),required=True)
parser.add_argument('--gui-record',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--seconds',type=int,default=45)
args=parser.parse_args()
assert 1<=args.seconds<=180
gui=json.loads(args.gui_record.read_text())
assert gui['method']=='ConceptGraphs-original-GUI' and gui['status']=='running'
source_map=Path(gui['command'][gui['command'].index('--result_path')+1])
info=subprocess.check_output(['xwininfo','-id',str(args.window_id)],text=True)
assert 'Map State: IsViewable' in info
assert 'Open3D - full_pcd_' in info, 'Select the observed author map window'
width=int(re.search(r'Width:\s+(\d+)',info).group(1))
height=int(re.search(r'Height:\s+(\d+)',info).group(1))
assert width%2==0 and height%2==0
args.output.mkdir(parents=True,exist_ok=False)
video=args.output/'conceptgraphs-room0-original-window.mp4'
command=['ffmpeg','-nostdin','-n','-f','x11grab','-framerate','15','-video_size',f'{width}x{height}',
    '-window_id',str(args.window_id),'-i',os.environ.get('DISPLAY',':0'),'-t',str(args.seconds),
    '-an','-c:v','libx264','-threads','2','-preset','fast','-crf','22','-pix_fmt','yuv420p',
    '-movflags','+faststart',str(video)]
started=datetime.now(timezone.utc).isoformat()
with (args.output/'ffmpeg.log').open('w') as log:
    subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
    '-show_entries','stream=width,height,nb_frames,r_frame_rate:format=duration','-of','json',str(video)],text=True))
assert abs(float(probe['format']['duration'])-args.seconds)<0.2
for second in [0,args.seconds//2,args.seconds-1]:
    subprocess.run(['ffmpeg','-nostdin','-n','-loglevel','error','-ss',str(second),'-i',str(video),
        '-frames:v','1',str(args.output/('sample-'+str(second)+'.png'))],check=True)
report={'status':'rendered','video':str(video),'bytes':video.stat().st_size,
    'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'started_at':started,
    'window_info':info,'command':command,'ffprobe':probe,'gui_record':str(args.gui_record),
    'source_commit':gui['source_commit'],'source_map':str(source_map),
    'scope':'Direct capture of the unchanged author Open3D GUI on the validated room0 map. Actual window pixels, not a terminal video or synthesized 3D animation. GUI actions are recorded separately. Display-only 0.05m downsampling and no_clip; no semantic-query accuracy or relation-graph claim.'}
(args.output/'media.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key not in ['window_info','command','ffprobe']}),flush=True)
