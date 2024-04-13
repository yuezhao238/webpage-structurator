import json
import pickle
import os


def read_pickle(file_path):
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    return data


def dump_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def prepare_path(config):
    if not os.path.exists(config.bbox_path):
        os.makedirs(config.bbox_path)
    if not os.path.exists(config.screenshots):
        os.makedirs(config.screenshots)
    if not os.path.exists(config.annotations):
        os.makedirs(config.annotations)
