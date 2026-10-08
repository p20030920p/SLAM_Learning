from pathlib import Path
from PIL import Image, ImageDraw

root=Path(r'D:\workspace\be2\submission-review\results\reference\visual-review')
paths=[p for m in ('dufomap','beautymap','conceptgraphs','hovsg') for p in sorted((root/m).glob('qa-*.png'))]
for page in range((len(paths)+11)//12):
    selected=paths[page*12:(page+1)*12]
    canvas=Image.new('RGB',(2560,1280),'#ffffff')
    draw=ImageDraw.Draw(canvas)
    for i,path in enumerate(selected):
        x,y=(i%4)*640,(i//4)*426
        with Image.open(path) as im:
            canvas.paste(im.resize((640,400)),(x,y+24))
        draw.text((x+8,y+5),path.parent.name+' / '+path.stem,fill='black')
    canvas.save(root/f'contact-{page+1}.png')
print(len(paths),'stages prepared for visual review')
