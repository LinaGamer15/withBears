import pathlib, typing, random, xml.etree.ElementTree as ET
from itertools import chain
from typing import List, Tuple
from PIL import Image, ImageOps

def split_background(background: Image.Image) -> list[Image.Image]:
    res = []
    for x in range(0, background.width-416, 416):
        for y in range(0, background.height-416, 416):
            res.append(background.crop((x, y, x+416, y+416)))
    return res

random.seed(42)
# Load raw images
cur = pathlib.Path(__file__).resolve().parent
backgrounds = [Image.open(i) for i in (cur/'backgrounds').iterdir()]
bears = [Image.open(i) for i in (cur/'bears').iterdir()]
print("Images loaded")
sliced = []
for background in backgrounds:
    sliced.extend(split_background(background))
    background.close()
backgrounds = sliced
print("Backgrounds sliced")
# Process images
class BearData:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __init__(self, xmin: float, ymin: float, xmax: float, ymax: float) -> None:
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

def commit_transposes(image: Image.Image) -> list[Image.Image]:
    rotations = [
        image,
        image.rotate(90, expand=True),
        image.rotate(180, expand=True),
        image.rotate(270, expand=True)
    ]
    res = chain(*map(lambda im: [
        im,
        ImageOps.flip(im),
        ImageOps.mirror(im),
        ImageOps.flip(ImageOps.mirror(im)),
    ], rotations))
    return list(res)

def gen_xml(file: str, bears: list[BearData], width: int, height: int) -> ET.ElementTree:
    root = ET.Element("annotation")
    ET.SubElement(root, "folder").text = ""
    ET.SubElement(root, "filename").text = file + '.png'

    source = ET.SubElement(root, "source")
    ET.SubElement(source, "database").text = "Unknown"
    ET.SubElement(source, "annotation").text = "Unknown"
    ET.SubElement(source, "image").text = "Unknown"

    size = ET.SubElement(root, "size")
    ET.SubElement(size, "width").text = str(width)
    ET.SubElement(size, "height").text = str(height)
    ET.SubElement(size, "depth")

    ET.SubElement(root, "segmented").text = "0"

    for bear in bears:
        object = ET.SubElement(root, "object")
        ET.SubElement(object, "name").text = "polar-bear"
        ET.SubElement(object, "truncated").text = "0"
        ET.SubElement(object, "occluded").text = "0"
        ET.SubElement(object, "difficult").text = "0"
        
        bndbox = ET.SubElement(object, "bndbox")
        ET.SubElement(bndbox, "xmin").text = str(bear.xmin)
        ET.SubElement(bndbox, "ymin").text = str(bear.ymin)
        ET.SubElement(bndbox, "xmax").text = str(bear.xmax)
        ET.SubElement(bndbox, "ymax").text = str(bear.ymax)
    
    return ET.ElementTree(root)

def add_bears(background: Image.Image, bears: list[Image.Image]) -> tuple[Image.Image, list[BearData]]:
    res_image = background.copy()
    res_data = []
    for bear in bears:
        x = random.randint(0, res_image.width - bear.width)
        y = random.randint(0, res_image.height - bear.height)
        res_image.paste(bear, (x, y))
        res_data.append(BearData(x, y, x+bear.width, y+bear.height))
    return (res_image, res_data)

bears = list(chain(*map(commit_transposes, bears)))
print("Bear images generated")
print("Background transposing started")
for background in backgrounds: 
    for background in commit_transposes(background):
        # Finally add bears!
        res_image, bear_datas = add_bears(
            background,
            [bears[random.randint(0, len(bears)-1)] for _ in range(0, random.choices([1, 2, 3], [0.5, 0.35, 0.15])[0])]
        )
        # Saving
        filename = str(len([f for f in (cur / "result").iterdir()]))
        res_image.save(cur / f"result/{filename}.png", 'png')
        xml_tree = gen_xml(filename, bear_datas, res_image.width, res_image.height)
        xml_tree.write(cur / f"result/Annotations/{filename}.xml", "UTF8", xml_declaration=False, short_empty_elements=False)
        # Cleanup
        background.close()
        res_image.close()

for bear in bears:
    bear.close()
print("Done!")