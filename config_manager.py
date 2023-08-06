import json

class ConfigManager:
    config = {}

    @classmethod
    def load_config(cls, filename: str):
        with open(filename, 'r') as f:
            cls.config = json.load(f)

    @classmethod
    def get_root_dirs(cls):
        return cls.config['root_dirs']