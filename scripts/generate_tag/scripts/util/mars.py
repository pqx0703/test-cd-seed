import os
import json
import subprocess

MARS_CONFIG_FILE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../mars_use.yaml"))

def get_highest_ones_version():
    out = subprocess.check_output(["mars", "-c", MARS_CONFIG_FILE, 
    "versions", "first", "--repo=ones", "--detail=true", 
    "--order=version", "--desc=true"])
    return json.loads(out)

def get_current_version():
    out = subprocess.check_output(["mars", "-c", MARS_CONFIG_FILE, 
    "versions", "get-current"])
    return json.loads(out)

def set_current_version(version_tag):
    out = subprocess.check_output(["mars", "-c", MARS_CONFIG_FILE, 
    "versions", "set-current", version_tag])
    return out

def get_version(version_key):
    out = subprocess.check_output(["mars", "-c", MARS_CONFIG_FILE, 
    "apollo", "get", "versions", version_key])
    return json.loads(out)

def add_versions(versions):
    out = subprocess.check_output(["mars", "-c", MARS_CONFIG_FILE, 
    "versions", "add-versions", json.dumps(versions)])
    return out
