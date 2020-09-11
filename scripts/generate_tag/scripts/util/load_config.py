import json
import os


class ConfigCache(object):
    def __init__(self):
        self._cache = {}

    def __call__(self, config_file):
        if config_file in self._cache:
            return self._cache[config_file]
        path = os.path.abspath(config_file)
        with open(path, "r") as f:
            config = json.load(f)
            self._cache[path] = config
            return config
        return None


load_config = ConfigCache()


def generate_repo_info_mapping(config):
    return config["REPO_MAP"]
