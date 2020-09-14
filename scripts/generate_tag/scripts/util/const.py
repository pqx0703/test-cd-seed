# -*- coding: utf-8 -*-
import os
from util.load_config import load_config

config = load_config(os.path.join(
    os.path.dirname(__file__), "../release_config_use.json"))

ALL_REPOS = list(config["REPO_MAP"].keys())

BUMP_TYPES = [
    'patch',
    'minor',
    'prerelease',
    'prepatch',
    'preminor',
    'major',
    'premajor',
]
