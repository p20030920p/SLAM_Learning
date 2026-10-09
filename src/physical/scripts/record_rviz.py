"""Record an isolated RViz view of live ROS data, without the Windows desktop."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time


class RvizRecording:
    def __init__(self, session, configuration, domain):
        self.session = Path(session)
        self.processes = []
        self.logs = []
        self.result = dict(status='starting', output='rviz-live.mp4',
                           content='Actual independent RViz view of live ROS topics; no synthetic poses',
                           frame_rate=10, size=[1440,1000], audio=False)
        self.encoder = None
        self.screen = None
        try:
            # WSLg's mounted X11 directory rejects Xvfb's -displayfd probe.
            # An explicit free display can use its local abstract UNIX socket.
            occupied={line.split()[-1] for line in Path('/proc/net/unix').read_text().splitlines() if line.split()}
            number=next((n for n in range(90,190) if not Path(f'/tmp/.X{n}-lock').exists()
                         and f'@/tmp/.X11-unix/X{n}' not in occupied
                         and f'/tmp/.X11-unix/X{n}' not in occupied),None)
            if number is None:
                raise RuntimeError('No free local X display for video')
            self.display = ':'+str(number)
            self.screen=self.spawn(['Xvfb',self.display,'-screen','0','1440x1000x24','-nolisten','tcp'],
                                   'video-display.log')
            deadline=time.monotonic()+5
            while True:
                try:
                    with socket.socket(socket.AF_UNIX) as probe:
                        probe.connect('\0/tmp/.X11-unix/X'+str(number))
                    break
                except OSError:
                    if self.screen.poll() is not None or time.monotonic()>deadline:
                        raise RuntimeError('Video display failed to become ready')
                    time.sleep(0.1)
            env = dict(os.environ,DISPLAY=self.display,QT_QPA_PLATFORM='xcb',
                       LIBGL_ALWAYS_SOFTWARE='1',LP_NUM_THREADS='2',ROS_DOMAIN_ID=str(domain),ROS_LOCALHOST_ONLY='1')
            self.rviz = self.spawn(['rviz2','-d',str(configuration)],'video-rviz.log',env=env)
            self.encoder = self.spawn(['ffmpeg','-nostdin','-hide_banner','-loglevel','warning',
                                       '-thread_queue_size','16','-f','x11grab','-draw_mouse','0','-framerate','10',
                                       '-video_size','1440x1000','-i',self.display+'.0',
                                       '-an','-c:v','libx264','-threads','2','-preset','ultrafast','-crf','23',
                                       '-pix_fmt','yuv420p','-movflags','+faststart',
                                       str(self.session/'rviz-live.mp4')],'video-ffmpeg.log',env=env)
            self.result.update(status='recording',display=self.display,started_monotonic=time.monotonic())
        except Exception as error:
            self.result.update(status='failed',error=repr(error))
            self.close()
            raise

    def spawn(self, command, name, **kwargs):
        log=(self.session/name).open('w')
        self.logs.append(log)
        process=subprocess.Popen(command,stdout=log,stderr=log,start_new_session=True,**kwargs)
        self.processes.append(process)
        return process

    def check(self):
        if any(process.poll() is not None for process in self.processes):
            raise RuntimeError('Video display/recorder stopped early; inspect video logs')

    def close(self):
        # Stop ffmpeg first so its MP4 index is written while the display exists.
        ordered=([self.encoder] if self.encoder else []) + [p for p in reversed(self.processes) if p is not self.encoder]
        forced=[]
        for process in ordered:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGINT)
                try:
                    process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                    process.wait()
                    forced.append(process.pid)
        for log in self.logs:
            log.close()
        if self.result['status']=='recording':
            self.result['elapsed_seconds']=time.monotonic()-self.result.pop('started_monotonic')
            self.result['status']='saved'
            self.result['forced_shutdown_pids']=forced
            video=self.session/'rviz-live.mp4'
            try:
                probe=subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
                                      '-show_entries','stream=codec_name,width,height,nb_frames:format=duration',
                                      '-of','json',str(video)],check=True,capture_output=True,text=True)
                self.result['probe']=json.loads(probe.stdout)
                stream=self.result['probe']['streams'][0]
                if int(stream.get('nb_frames',0))<1:
                    raise ValueError('Video has no encoded frames')
                self.result['bytes']=video.stat().st_size
            except Exception as error:
                self.result.update(status='failed',error=repr(error))
        (self.session/'video.json').write_text(json.dumps(self.result,indent=2)+'\n')
        return self.result
