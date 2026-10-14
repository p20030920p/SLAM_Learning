"""Generate a matched corridor with a plain centre and distinctive end rooms."""
from pathlib import Path
import xml.etree.ElementTree as ET


def generate(path: Path):
    source = path.parent / "S1_static.world"
    tree = ET.parse(source)
    world = tree.getroot().find("world")
    for item in list(world):
        if item.tag == "include" or (item.tag == "model" and item.get("name") != "ground_plane"):
            world.remove(item)
    ground = world.find("model[@name='ground_plane']")
    for size in ground.findall(".//plane/size"):
        size.text = "40 24"

    def box(name, pose, dimensions, colour, *, collision=True):
        model = ET.SubElement(world, "model", name=name)
        ET.SubElement(model, "static").text = "true"
        ET.SubElement(model, "pose").text = " ".join(map(str, (*pose, 0, 0, 0)))
        link = ET.SubElement(model, "link", name="link")
        if collision:
            shape = ET.SubElement(ET.SubElement(ET.SubElement(link, "collision", name="collision"), "geometry"), "box")
            ET.SubElement(shape, "size").text = " ".join(map(str, dimensions))
        visual = ET.SubElement(link, "visual", name="visual")
        shape = ET.SubElement(ET.SubElement(visual, "geometry"), "box")
        ET.SubElement(shape, "size").text = " ".join(map(str, dimensions))
        material = ET.SubElement(visual, "material")
        for tag in ("ambient", "diffuse"):
            ET.SubElement(material, tag).text = " ".join(map(str, (*colour, 1)))

    # Centre is geometrically invariant along X. No furniture/door edges in the
    # 3.5 m pressure scan at the starting pose; full 12 m scans see the end rooms.
    for side, y in (("north", -1.6), ("south", -4.6)):
        box("plain_wall_" + side, (7.15, y, 1.1), (14, .18, 2.2), (.42, .48, .56))
        for end, x in (("west", -2.35), ("east", 16.65)):
            box(f"end_room_{end}_{side}", (x, y + (1.8 if side == "north" else -1.8), 1.1), (5, .18, 2.2), (.24, .40, .55))
    for end, x in (("west", -4.94), ("east", 19.24)):
        box("end_wall_" + end, (x, -3.1, 1.1), (.18, 6.6, 2.2), (.24, .40, .55))
    for end, x in (("west", .15), ("east", 14.15)):
        for side, y in (("north", -.7), ("south", -5.5)):
            box(f"room_shoulder_{end}_{side}", (x, y, 1.1), (.18, 1.8, 2.2), (.24, .40, .55))
    box("west_unique_column", (-1.5, -1.15, .9), (.7, .7, 1.8), (.85, .55, .18))
    box("east_unique_block", (16.3, -4.8, .75), (1.4, .6, 1.5), (.18, .62, .45))
    box("east_unique_column", (17.8, -1.6, 1), (.55, .55, 2), (.18, .62, .45))
    # Coloured floor zones make geometry readable in Gazebo. At floor height,
    # they supply no features to the planar laser used in this experiment.
    box("plain_floor_zone", (7.15, -3.1, .002), (14, 2.8, .004), (.73, .76, .80), collision=False)
    box("west_floor_zone", (-2.35, -3.1, .002), (5, 6.4, .004), (.84, .78, .64), collision=False)
    box("east_floor_zone", (16.65, -3.1, .002), (5, 6.4, .004), (.65, .81, .74), collision=False)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[3] / "config/presentation/worlds/S4_degradation.world")
