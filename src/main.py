import glob
import json
from optparse import Values
import sys
import time

from datetime import datetime
from itertools import chain

from os import makedirs, remove
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

CONFLICTS = {
    "Floating islands WIP.png": [
        "Pyramid stone.png"
    ],
    "Great wave.png": [
        "Lonely islands WIP cleaned.png"
    ],
    "Japanese pagoda.png": [
        "Lonely islands WIP cleaned.png",
        "Pyramid stone.png"
    ],
    "Pine forest.png": [
        "Cloud world.png",
        "Lonely islands WIP cleaned.png",
        "Treetops.png"
    ]
}

all_biomes = {}


def main():
    limit = 20 if len(sys.argv) == 1 else int(sys.argv[1])
    testing_dir = _manage_test_dir()
    main_start = time.time()

    _generate(testing_dir, limit)
    while True:
        number_to_reproduce, patches = _check_for_duplicates(testing_dir)
        if number_to_reproduce == 0 or not patches:
            break
        _generate(testing_dir, number_to_reproduce, patches)

    main_end = time.time()
    print(f"{''.join(SEPARATOR)}\nTotal time for {limit} biomes was: {main_end - main_start}")
    print("Uploading to IPFS now")
    # _upload_to_ipfs(testing_dir)

def _manage_test_dir():
    """Creates a directory in which all the biomes and metadata will be
    saved in
    
    Returns:
        os.path: Path of the output directory
    """
    root_test_folder = join(REPO_DIR, "tests")
    if not exists(root_test_folder):
        makedirs(root_test_folder)
    timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d--%H-%M-%S")
    current_test_dir = join(root_test_folder, timestamp)
    makedirs(current_test_dir)
    return current_test_dir


def _get_random_number():
    """Uses a Quantum random number generator to get a random set of
    numbers for each attribute.
    
    Returns:
        background_qrng (int): Random number
        foreground_qrng (int): Random number
        object_qrng (int): Random number
    """
    response = json.loads(requests.get(QRNG_URL).text)
    print(f"... Response: {response}")
    background_qrng = response[0]
    foreground_qrng = response[1]
    object_qrng = response[2]

    return background_qrng, foreground_qrng, object_qrng


def _get_attributes(background_qrng, foreground_qrng, object_qrng):
    """Uses the qrng's provided to determine which attribute it's been
    assigned with, populates the attributes dictionary and returns that
    unless there is a conflict in the pre-determined ruleset.
    
    Args:
        background_qrng (int): Random number
        foreground_qrng (int): Random number
        object_qrng (int): Random number
        
    Returns:
        dict: Dictionary of attributes, default to None if a conflict
    """
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
                
    if attributes["background"] in CONFLICTS and attributes["foreground"] in CONFLICTS[attributes["background"]]:
        print(f"\tBackground: {attributes['background']} clashes with Foreground: {attributes['foreground']}, we'll skip")
        return None

    return attributes


def _generate_image(attributes, testing_dir, number):
    """Creates the image by opening each asset as a byte code and then layers
    them ontop of each other going:
        Background > Foreground > Object
    Once the image has been made in a byte array, it's converted to an actual
    Image where the this is then saved as a PNG file.
    
    Once the image has been saved, we store a hash of the attributes (pre-IPFS)
    to the global biomes dictionary for future de-duplication resolution.
    
    Finally, we then upload the image to IPFS and add the hash of
    the image to the attributes so the metadata can be saved.
    
    Args:
        attributes (dict): Dictionary containing the attributes of the biome
        testing_dir (os.path): Path of the output directory
        number (int): The number this file will be saved as

    TODO:
        IPFS
    """
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
    all_biomes[number] = hash(str(attributes))

    # hash = _push_to_ipfs(image)
    # attributes["hash"] = hash
    

def _save_json(attributes, testing_dir, number):
    """Saves the metadata to a JSON formatted file, but not prefixed with
    the JSON file extension.
    
    Args:
        attributes (dict): Dictionary containing the attributes of the biome
        testing_dir (os.path): Path of the output directory
        number (int): The number this file will be saved as    
    """
    final_path = join(testing_dir, f"{number:0=4d}")
    with open(final_path, "w") as open_file:
        json.dump(attributes, open_file)


def _check_for_duplicates(testing_dir):
    """We start by reversing the global biome dictionary, previously it was
    storing data as such;
        {
            <biome-id>: <hash-of-attributes>
        }
        for example;
        {
            '0001': '-6635552724647555108',
            '0002': '-6635552724647555108',
            '0003': '6869023552329823000',
            ...
        }
    We've now reversed it so the hash is the key, and stores a set of all
    biomes with that hash, so in this case:
        {
            '-6635552724647555108': {'0001', '0002'},
            '6869023552329823000': {'0003'},
            ...
        }
    With this, we can then detect any duplicates. We keep the first one
    (lowest ordinal), and remove the rest. The ordinals from this are added
    to a patches list, which will be used later to regenerate them.
    
    Args:
        testing_dir (os.path): Path of the output directory
        
    Returns:
        int: Number of biomes needing to be reproduced
        list(int): Ordinals requiring replacement
    """
    number_to_reproduce = 0
    patches = []
    reverse = {}
    for number, meta_hash in all_biomes.items():
        reverse.setdefault(meta_hash, set()).add(number)
    duplicate_biomes = {
        meta_hash: sorted(biomes)
        for meta_hash, biomes in reverse.items()
        if len(biomes) > 1
    }
    if not duplicate_biomes:
        print("No duplicates found")
        return 0, []
    print(f"We've found {len(duplicate_biomes)} duplicates!\n\t{duplicate_biomes}\nClearing this up")
    for meta_hash, biomes in duplicate_biomes.items():
        to_delete = biomes[1:]
        number_to_reproduce += len(to_delete)
        for file in to_delete:
            remove(join(testing_dir, file))
            remove(join(testing_dir, file, ".png"))

        patches.extend([int(ordinal) for ordinal in to_delete])

    print("Cleaned up duplicates")
    return number_to_reproduce, patches


def _generate(testing_dir, number_to_produce, patches=None):
    """The main cheese of this application. It ensures the number of requested
    biomes is made before being marked as complete. During this process, when it
    goes to get the attributes, if they're conflicts, it'll keep retrying until
    it's resolved.
    
    Once it's happy with the attributes randomly selected, it will generate the
    biome, upload to IPFS and save the metadata.
    
    This function is used twice, for the initial generation and when it comes to
    patching duplicates. This is why the patches argument is optional. On initial
    run, the patches is a mask for a list of the requested limit;
        patches = [1, 2, 3, 4, 5, ..., 20] # On initial run
    And then fed through with actual values in a rehydrate post de-duplication;
        patches = [6, 258, 1024] # On a rehydrate
    This ensures that the holes get filled in with the general amount we wish to
    generate.
    
    Args:
        testing_dir (os.path): Path of the output directory
        number_to_produce (int): Number of biomes we're generating
        patches (list:optional): List of any holes we're rehydrating
    """
    print(f"Making {number_to_produce} biome(s)")
    patches = patches if patches else [x for x in range(1, number_to_produce + 1)]
    for patch in patches:
        start = time.time()
        print("----- New Biome -----")
        attributes = {}
        while True:
            background_qrng, foreground_qrng, object_qrng = _get_random_number()
            attributes = _get_attributes(
                background_qrng,
                foreground_qrng,
                object_qrng
            )
            if attributes:
                print(f"\tGot the following attributes: {attributes}")
                break
            else:
                print(f"We had a conflict, getting new attributes")
        _generate_image(attributes, testing_dir, patch)
        _save_json(attributes, testing_dir, patch)
        end = time.time()
        print(f"\tTook {end - start}")


def _upload_to_ipfs(testing_dir, limit):
    """Awaiting pinata to email me """
    for i in range(1, limit+1):
        biome = join(testing_dir, f"{i:0=4d}")
        """
        png = join(biome, ".png")
        hash = requests.post(url, data={
            ...
        })
        meta_data = {}
        with open(biome, encoding="utf-8") as open_file:
            meta_data = json.loads(open_file.read())
        meta_data["hash"] = hash
        with open(biome, "w") as open_file:
            json.dump(meta_data, open_file)
        """
