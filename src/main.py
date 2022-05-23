import glob
import json
import sys
import time

from datetime import datetime

from os import makedirs
from os.path import (
    dirname,
    exists,
    join
)

import numpy
import pandas
import requests

from blend_modes import normal
from PIL import Image

GET_FILE_NAMES = lambda path: glob.glob(path)
QRNG_URL = "http://www.randomnumberapi.com/api/v1.0/random?min=1&max=65535&count=3"
SEPARATOR = ["-"] * 60

REPO_DIR = dirname(dirname(__file__))
ROOT_DIR = dirname(REPO_DIR)
BIOME_DIR = join(ROOT_DIR, "Bizzare-Biomes-Assets/ZILponds")

BACKGROUD_DIR = join(BIOME_DIR, "Environment background")
FOREGROUND_DIR = join(BIOME_DIR, "Environment foreground")
OBJECTS_DIR = join(BIOME_DIR, "Objects")

BACKGROUND_DF = pandas.read_csv(join(BACKGROUD_DIR, "numbers.csv"))
FOREGROUND_DF = pandas.read_csv(join(FOREGROUND_DIR, "numbers.csv"))
OBJECTS_DF = pandas.read_csv(join(OBJECTS_DIR, "numbers.csv"))

ATTRIBUTE_TYPES = {
    "background": {
        "data": BACKGROUND_DF,
        "qrng": None
    },
    "foreground": {
        "data": FOREGROUND_DF,
        "qrng": None
    },
    "object": {
        "data": OBJECTS_DF,
        "qrng": None
    }
}


def main():
    limit = int(sys.argv[1]) if sys.argv[1] else 20
    testing_dir = _manage_test_dir()
    main_start = time.time()
    for i in range(1, limit + 1):
        start = time.time()
        print("----- New Biome -----")
        background_qrng, foreground_qrng, object_qrng = _get_random_number()
        attributes = _get_attributes(
            background_qrng,
            foreground_qrng,
            object_qrng
        )
        print(f"\tGot the following attributes: {attributes}")
            
        _generate_photoshop_image(attributes, testing_dir, i)
        _save_json(attributes, testing_dir, i)
        end = time.time()
        print(f"\tTook {end - start}")
    main_end = time.time()
    print(f"{''.join(SEPARATOR)}\nTotal time for {limit} biomes was: {main_end - main_start}")

def _manage_test_dir():
    root_test_folder = join(REPO_DIR, "tests")
    if not exists(root_test_folder):
        makedirs(root_test_folder)
    timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d--%H-%M-%S")
    current_test_dir = join(root_test_folder, timestamp)
    makedirs(current_test_dir)
    return current_test_dir


def _get_random_number():
    response = json.loads(requests.get(QRNG_URL).text)
    print(f"... Response: {response}")
    background_qrng = response[0]
    foreground_qrng = response[1]
    object_qrng = response[2]

    return background_qrng, foreground_qrng, object_qrng


def _get_attributes(background_qrng, foreground_qrng, object_qrng):
    attributes = {
        "background": None,
        "foreground": None,
        "object": None
    }

    ATTRIBUTE_TYPES["background"]["qrng"] = background_qrng
    ATTRIBUTE_TYPES["foreground"]["qrng"] = foreground_qrng
    ATTRIBUTE_TYPES["object"]["qrng"] = object_qrng

    for attribute_type, data in ATTRIBUTE_TYPES.items():
        for _, row in data["data"].iterrows():
            f = int(row.loc["f"])
            c = int(row.loc["c"])
            if ( data["qrng"] >= f and data["qrng"] <= c ):
                attributes[attribute_type] = row.loc["asset"]

    return attributes


def _generate_photoshop_image(attributes, testing_dir, number):
    background_path = join(BACKGROUD_DIR, attributes["background"])
    foreground_path = join(FOREGROUND_DIR, attributes["foreground"])
    object_path = join(OBJECTS_DIR, attributes["object"])

    background_image = numpy.array(Image.open(background_path)).astype(float)
    foreground_image = numpy.array(Image.open(foreground_path)).astype(float)
    object_image = numpy.array(Image.open(object_path)).astype(float)

    final_image = normal(background_image, foreground_image, 1)
    final_image = normal(final_image, object_image, 1)

    blended_image = numpy.uint8(final_image)
    blended_image_raw = Image.fromarray(blended_image)

    final_path = join(testing_dir, f"{number:0=4d}.png")
    blended_image_raw.save(final_path, "PNG")


def _save_json(attributes, testing_dir, number):
    final_path = join(testing_dir, f"{number:0=4d}-M.json")
    with open(final_path, "w") as open_file:
        json.dump(attributes, open_file)