from dataclasses import dataclass


@dataclass
class Config:
    url_list: str = ''
    bbox_path: str = 'checkboxes'
    screenshots: str = 'screenshots'
    annotations: str = 'annotations'
    processes: int = 4
