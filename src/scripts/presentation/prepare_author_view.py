"""Create an actual RViz display for current author-algorithm state."""
import sys
from pathlib import Path

run, method = Path(sys.argv[1]), sys.argv[2]
center = (1.0, -3.75, 22) if method == "ir-mcl" else (15.0, 10.0, 8)
displays = ""
for name, label, color, size in (("map", "Current native retained/map state", "180; 185; 195", 2),
                                 ("removed", "Current native removed points", "255; 60; 70", 5),
                                 ("input", "Current scan (display thinned)", "60; 210; 255", 3),
                                 ("particles", "Native IR-MCL particles (display thinned)", "255; 190; 40", 3)):
    enabled = name in (("map", "particles") if method == "ir-mcl" else ("map", "removed", "input"))
    displays += f'''    - Class: rviz_default_plugins/PointCloud2
      Name: {label}
      Enabled: {str(enabled).lower()}
      Topic:
        Value: /author/{name}
        Reliability Policy: Reliable
        Durability Policy: Volatile
        Depth: 5
      Style: Points
      Size (Pixels): {size}
      Color Transformer: FlatColor
      Color: {color}
      Position Transformer: XYZ
'''
for name, color in (("path", "60; 160; 255"), ("truth", "60; 230; 140")):
    displays += f'''    - Class: rviz_default_plugins/Path
      Name: {'Live particle estimate' if name == 'path' else 'Reference for display only'}
      Enabled: {str(method == 'ir-mcl').lower()}
      Topic:
        Value: /author/{name}
      Color: {color}
      Line Width: 0.04
'''
displays += '''    - Class: rviz_default_plugins/Marker
      Name: Current native frame and processing phase
      Enabled: true
      Topic:
        Value: /author/status
'''
config = f'''Panels:
  - Class: rviz_common/Displays
    Name: Displays
Visualization Manager:
  Class: ""
  Displays:
{displays}  Global Options:
    Fixed Frame: author_map
    Background Color: 18; 22; 28
    Frame Rate: 15
  Tools: []
  Views:
    Current:
      Class: rviz_default_plugins/TopDownOrtho
      Target Frame: author_map
      Scale: {center[2]}
      X: {center[0]}
      Y: {center[1]}
Window Geometry:
  Width: 1200
  Height: 760
  X: 0
  Y: 0
'''
(run / "author-live.rviz").write_text(config)
