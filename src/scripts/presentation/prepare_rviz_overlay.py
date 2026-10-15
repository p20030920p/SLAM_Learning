from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[3] / ".cache/presentation/rviz-overlay"
share = root / "share/rviz_rendering"
shutil.copytree("/opt/ros/jazzy/share/rviz_rendering", share, dirs_exist_ok=True)
index = root / "share/ament_index/resource_index/packages"
index.mkdir(parents=True, exist_ok=True)
(index / "rviz_rendering").write_text("")
shader = share / "ogre_media/materials/glsl120/indexed_8bit_image.frag"
source = shader.read_text()
source = source.replace("#version 120", "#version 120\n#extension GL_ARB_shading_language_420pack : require")
source = source.replace(
    "uniform sampler2D eight_bit_image;", "layout(binding = 0) uniform sampler2D eight_bit_image;"
)
source = source.replace("uniform sampler1D palette;", "layout(binding = 1) uniform sampler1D palette;")
shader.write_text(source)
print("Created isolated RViz asset overlay; installed package unchanged.")
