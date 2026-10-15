import hashlib
import json
import os
import time
from pathlib import Path
import numpy as np
import rclpy
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from rclpy.qos import qos_profile_sensor_data

repo=Path(os.environ['SLAM_TEST_REPO'])
rclpy.init()
node=rclpy.create_node('omni_3d_source_smoke')
frames=[]
def receive(msg):
    xyz=point_cloud2.read_points_numpy(msg,field_names=('x','y','z'),skip_nans=True)
    valid=xyz[np.isfinite(xyz).all(axis=1)]
    frames.append({'stamp_s':msg.header.stamp.sec+msg.header.stamp.nanosec/1e9,
        'frame_id':msg.header.frame_id,'width':msg.width,'height':msg.height,
        'fields':[field.name for field in msg.fields],'finite_points':len(valid),
        'z_span_m':float(np.ptp(valid[:,2])) if len(valid) else 0.0})
node.create_subscription(PointCloud2,'/points',receive,qos_profile_sensor_data)
deadline=time.monotonic()+35
while rclpy.ok() and time.monotonic()<deadline and len(frames)<15:
    rclpy.spin_once(node,timeout_sec=0.25)
passed=len(frames)>=5 and all(frame['frame_id']=='lidar_3d_link' and frame['height']==16
    and frame['width']==720 and frame['finite_points']>100 and frame['z_span_m']>0.1 for frame in frames)
rate=(len(frames)-1)/(frames[-1]['stamp_s']-frames[0]['stamp_s']) if len(frames)>1 and frames[-1]['stamp_s']>frames[0]['stamp_s'] else None
report={'kind':'T0_stationary_3d_sensor_smoke','profile':'omni-3d-v1','passed':passed,
    'scope':'Native Sim2Real chassis stationary in an isolated box world; ROS PointCloud2 source only. Not a mapping/localization trial.',
    'source_revision':'53324d40def0dd753b4a99021b8fe596955a1ecd',
    'input_urdf_sha256':hashlib.sha256((repo/'config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf').read_bytes()).hexdigest(),
    'harness_sha256':hashlib.sha256((repo/'src/scripts/testing/verify_3d_source.sh').read_bytes()).hexdigest(),
    'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'world_sha256':hashlib.sha256((repo/'.cache/omni-3d-smoke/world.sdf').read_bytes()).hexdigest(),
    'observed_sim_rate_hz':rate,'frames':frames,
    'mapping_tested':False,'localization_tested':False,'motion_tested':False}
(repo/'docs/testing/t0-3d-source.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':passed,'frames':len(frames),'sim_rate_hz':rate,'last_frame':frames[-1] if frames else None}))
node.destroy_node()
rclpy.shutdown()
raise SystemExit(0 if passed else 1)
