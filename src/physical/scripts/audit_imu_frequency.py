"""Host-time resampled FFT as a vibration clue, not a causal/Allan analysis."""
import argparse
import json
from pathlib import Path
import numpy as np


ap=argparse.ArgumentParser()
ap.add_argument("session",type=Path)
ap.add_argument("--output",type=Path,required=True)
args=ap.parse_args()
a=np.loadtxt(args.session/"imu.csv",delimiter=",",skiprows=1)
t=a[:,2]-a[0,2]; a=a[t>=10]; t=a[:,2]-a[0,2]
hz=(len(t)-1)/(t[-1]-t[0]); regular=np.arange(0,t[-1],1/hz)
window=np.hanning(len(regular)); frequencies=np.fft.rfftfreq(len(regular),1/hz)
result={"method":"last 50s approximately, host receive timeline, linear interpolation, demean, Hann window, FFT magnitude",
        "source_sha256":json.loads((args.session/"capture.json").read_text())["raw_sha256"],
        "host_sampling_hz":hz,"frequency_resolution_hz":float(frequencies[1]),"axis_peaks_hz":{},
        "interpretation":"Frequency coincidence with motor is a hypothesis, not proof of mechanical causality or noise calibration"}
for i,axis in enumerate(("wx","wy","wz")):
    y=np.interp(regular,t,a[:,7+i]); y-=y.mean()
    magnitude=np.abs(np.fft.rfft(y*window)); magnitude[frequencies<0.5]=0
    result["axis_peaks_hz"][axis]=frequencies[np.argsort(magnitude)[-5:][::-1]].tolist()
period=json.loads((args.session/"capture.json").read_text())["last_inside_state"]["com_rotation_period"]
result["reported_com_motor_hz"]=1e6/period
args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
