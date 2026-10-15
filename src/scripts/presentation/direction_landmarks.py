"""A labelled geometry control; physical LiDAR-visible objects, no virtual QR."""

import xml.etree.ElementTree as ET


def landmark_world(source, run):
    tree = ET.parse(source)
    world = tree.getroot().find("world")
    for name, x, y in (("asymmetric_landmark_a", 6.0, -2.48), ("asymmetric_landmark_b", 8.35, -3.72)):
        model = ET.SubElement(world, "model", name=name)
        ET.SubElement(model, "static").text = "true"
        ET.SubElement(model, "pose").text = f"{x} {y} 0.45 0 0 0"
        link = ET.SubElement(model, "link", name="body")
        for tag in ("collision", "visual"):
            entity = ET.SubElement(link, tag, name=tag)
            ET.SubElement(
                ET.SubElement(ET.SubElement(entity, "geometry"), "box"), "size"
            ).text = "0.24 0.24 0.9"
            if tag == "visual":
                mat = ET.SubElement(entity, "material")
                ET.SubElement(mat, "diffuse").text = "0.9 0.2 0.05 1"
    output = run / "landmark-corridor.world"
    tree.write(output, encoding="unicode")
    return output
