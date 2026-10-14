"""Save Gazebo entity parentage for independent moving-box point labels."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, "/opt/ros/jazzy/opt/gz_msgs_vendor/lib/python")
from google.protobuf import text_format
from gz.msgs10.scene_pb2 import Scene


def main():
    run = Path(sys.argv[1])
    scene = text_format.Parse((run / "object-scene.pbtxt").read_text(), Scene())
    world = ET.parse(json.loads((run / "runtime.json").read_text())["world"])
    result = []
    for model in scene.model:
        if not model.name.startswith("dynamic_obstacle"):
            continue
        element = world.find(f".//model[@name='{model.name}']")
        link = next(link for link in model.link if link.name == "body")
        geometry = element.find("link/collision/geometry/box/size")
        result.append({"name": model.name, "model_id": model.id, "link_id": link.id,
                       "size_xyz": list(map(float, geometry.text.split())),
                       "pose_semantics": "Pose_V model world pose multiplied by body pose relative to model"})
    if len(result) != 3:
        raise ValueError("Expected the three actual moving boxes and their body IDs")
    (run / "object-geometry.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
