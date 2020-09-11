# -*- coding: utf-8 -*-
import os
from util.load_config import load_config

ALL_REPOS = [
    'ones-project-web',
    'bang-api',
    'wiki-web',
    'wiki-api',
    'ones-devops',
    'audit-log-sync',
    'ones-third-importer',
    'ones-demo',
    'ones-cmd-proxy-service',
    'ones-mapper-attachments',
    'web-gateway',
    'ones-crm'
]

BUMP_TYPES = [
    'patch',
    'minor',
    'prerelease',
    'prepatch',
    'preminor',
    'major',
    'premajor',
]

config = load_config(os.path.join(
    os.path.dirname(__file__), "../release_config_use.json"))
