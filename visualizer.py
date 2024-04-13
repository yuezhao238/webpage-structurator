from PIL import ImageDraw
from copy import deepcopy
from node_processor import leaf_list

def draw_bbox(img, page_structure, color='red'):
    leaf_node_list = leaf_list(page_structure)
    draw = ImageDraw.Draw(img)
    for node in leaf_node_list:
        node = deepcopy(node['boxInfo'])
        draw.rectangle(
            [
                (
                    node['left'], node['top']
                ), 
                (
                    node['left']+node['width'], node['top']+node['height']
                )
            ], 
            outline=color, 
            width=2
        )
    return img
