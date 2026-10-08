"""Render recorded algorithm outputs beside real input; never synthesize poses."""
import argparse
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np


def label(canvas,text,xy,size=0.55,color=(225,225,225)):
    cv2.putText(canvas,text,xy,cv2.FONT_HERSHEY_SIMPLEX,size,color,1,cv2.LINE_AA)


def project(canvas,xyz,origin,axes=(0,1),scale=50,color=(190,180,90)):
    if not len(xyz):
        return
    uv=np.rint(np.column_stack((origin[0]+xyz[:,axes[0]]*scale,
                               origin[1]-xyz[:,axes[1]]*scale))).astype(int)
    valid=(uv[:,0]>=0)&(uv[:,0]<canvas.shape[1])&(uv[:,1]>=0)&(uv[:,1]<canvas.shape[0])
    canvas[uv[valid,1],uv[valid,0]]=color


def rotation(q):
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("dataset",type=Path)
    ap.add_argument("run",type=Path)
    ap.add_argument("--name",default="preview")
    args=ap.parse_args()
    result=json.loads((args.run/"result.json").read_text())
    stereo=result["mode"]=="stereo"
    motion=result.get("session_type")=="motion"
    dataset=json.loads((args.dataset/("stereo.json" if stereo else "clouds.json")).read_text())
    rows=dataset["pairs"][:result["published_pairs"]]
    statuses={r["stamp_ns"]:r for r in json.loads((args.run/"status.json").read_text())}
    poses={p["stamp_ns"]:p for p in json.loads((args.run/"poses.json").read_text())}
    valid=[p for p in poses.values() if p["covariance0"]<9999]
    origin=np.asarray(valid[0]["xyz"]) if valid else np.zeros(3)
    plot_scale=120/max(0.05,result.get("translation_excursion_max_m",result.get("static_translation_max_m",0))*1.1)
    plot_axes=(0,2) if motion and stereo else (0,1)
    last_map=np.load(args.run/"last_local_map.npz")["xyz"] if (args.run/"last_local_map.npz").exists() else np.zeros((0,3))
    fps=(len(rows)-1)/(rows[-1]["stamp_s"]-rows[0]["stamp_s"])
    if Path(args.name).name!=args.name or not args.name:
        ap.error("Use a filename stem without directory components")
    temporary=args.run/f"{args.name}-uncompressed.avi"
    writer=cv2.VideoWriter(str(temporary),cv2.VideoWriter_fourcc(*"MJPG"),fps,(1280,960))
    if not writer.isOpened():
        raise OSError("Video writer failed")
    trail=[]; history=[]; accumulated=[]
    for i,row in enumerate(rows):
        ns=round(row["stamp_s"]*1e9); status=statuses.get(ns); pose=poses.get(ns)
        canvas=np.full((960,1280,3),18,dtype=np.uint8)
        if stereo:
            for x,side in ((0,"left"),(640,"right")):
                image=cv2.imread(str(args.dataset/row[side]))
                canvas[:480,x:x+640]=image
                cv2.rectangle(canvas,(x,0),(x+640,40),(15,15,15),-1)
                label(canvas,f"ACTUAL {side.upper()} IR | 640x480",(x+10,27))
        else:
            source_row=dataset["pairs"][0] if result.get("repeat_first_cloud_control") else row
            with np.load(args.dataset/source_row["cloud"]) as cloud:
                xyz=cloud["xyzi"][:,:3]
            for x,axes,title in ((0,(0,1),"RAW CLOUD TOP X/Y"),(640,(0,2),"RAW CLOUD SIDE X/Z")):
                pane=canvas[:480,x:x+640]
                project(pane,xyz,(320,250),axes,55)
                label(pane,f"{title} | {len(xyz)} points",(12,30))
                label(pane,f"{dataset['lines_per_cloud']}-line grouping; no IMU; no deskew",(12,460),0.5)
            if pose and pose["covariance0"]<9999:
                world=xyz@rotation(pose["xyzw"]).T+np.asarray(pose["xyz"])
                accumulated.append(world[::8])
        cv2.rectangle(canvas,(0,480),(1280,555),(30,30,30),-1)
        state="MISSING OUTPUT" if status is None else status.get("quality_state",("LOST" if status["lost"] else "TRACKING"))
        algorithm="KISS-ICP" if result["algorithm"]=="KISS-ICP" else f"RTAB-Map {'STEREO' if stereo else 'ICP'}"
        if result.get("prediction_policy")=="zero_delta_control":
            algorithm+=" / ZERO-DELTA CONTROL"
        if result.get("repeat_first_cloud_control"):
            algorithm+=" / SYNTHETIC IDENTICAL-CLOUD CONTROL"
        label(canvas,f"SAVED ALGORITHM OUTPUT REPLAY | {algorithm} | {state}",(15,510),0.48,
              (80,220,80) if state=="TRACKING" else (70,70,255))
        elapsed=row["stamp_s"]-rows[0]["stamp_s"]
        if status:
            quality=(f"features {status['features']} / inliers {status['inliers']}" if stereo else
                     f"ICP inlier ratio {status['icp_inliers_ratio']:.3f}" if status['icp_inliers_ratio'] is not None else
                     f"registration source points {status['source_points']}; no tracking flag exposed")
            label(canvas,f"t={elapsed:.1f}s | {quality} | compute {status['time_estimation_s']*1000:.1f}ms",(15,540))
        label(canvas,"MOTION: EXPECT SMOOTH PATH FOLLOWING ACTUAL MOVEMENT" if motion else
              "STATIONARY: EXPECT TRAJECTORY NEAR ORIGIN",(15,585),0.55)
        panel=canvas[600:870,:640]
        cv2.line(panel,(320,0),(320,270),(70,70,70),1); cv2.line(panel,(0,135),(640,135),(70,70,70),1)
        if not motion:
            cv2.circle(panel,(320,135),round(0.05*plot_scale),(50,100,50),1)
        if pose and pose["covariance0"]<9999:
            delta=np.asarray(pose["xyz"])-origin
            trail.append(delta)
            history.append([elapsed,*delta])
            label(canvas,f"displacement from first registered pose: {np.linalg.norm(delta)*1000:.3f} mm",(15,890),0.5)
        if trail:
            uv=np.asarray([[320+p[plot_axes[0]]*plot_scale,135-p[plot_axes[1]]*plot_scale] for p in trail]).astype(np.int32)
            uv[:,0]=np.clip(uv[:,0],0,639); uv[:,1]=np.clip(uv[:,1],0,269)
            cv2.polylines(panel,[uv],False,(80,210,250),2)
            cv2.circle(panel,tuple(uv[-1]),4,(60,255,80),-1)
        axes_name="X/Z" if plot_axes==(0,2) else "X/Y"
        suffix="initial camera frame; no static drift gate" if motion else "green circle = 5cm target"
        label(canvas,f"{axes_name}: half-width {320/plot_scale*100:.1f}cm | {suffix}",(15,920),0.48)
        if stereo:
            pane=canvas[570:935,660:1280]
            project(pane,last_map,(310,320),(0,2),75,color=(110,220,120))
            label(pane,"FINAL SPARSE LOCAL MAP (REFERENCE)",(5,25),0.5)
            label(pane,"X/Z projection, 75 px/m; no loop-closure node",(5,350),0.45)
        elif accumulated:
            pane=canvas[570:935,660:1280]
            world=np.concatenate(accumulated[-100:])
            project(pane,world,(310,180),(0,1),45,color=(110,220,120))
            label(pane,"ACCUMULATED USING ESTIMATED POSES",(5,25),0.5)
            label(pane,"Top X/Y; recent 100 clouds; not ground truth",(5,350),0.45)
        footer=("MOTION ODOMETRY REPLAY | No external ground truth / ATE | No loop-closure node"
                if motion else "DIAGNOSTIC CONTROL: modified prediction or repeated input; not a new default hardware baseline"
                if result.get("is_diagnostic_control") else
                "Static stability only | No external ground truth / ATE | This is offline output playback")
        label(canvas,footer,(15,950),0.5)
        writer.write(canvas)
        if i==len(rows)//2:
            cv2.imwrite(str(args.run/f"{args.name}.png"),canvas)
    writer.release()
    video=args.run/f"{args.name}.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-n","-i",str(temporary),
                    "-c:v","libx264","-threads","2","-crf","24","-pix_fmt","yuv420p",
                    "-movflags","+faststart",str(video)],check=True)
    temporary.unlink()
    (args.run/"video.json").write_text(json.dumps({"kind":"saved_algorithm_output_replay","frames":len(rows),
        "fps":fps,"duration_s":len(rows)/fps,"result":str(args.run/"result.json"),"path":str(video)},indent=2)+"\n")
    print(video)


if __name__=="__main__":
    main()
