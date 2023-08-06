import os
import math
import importlib
from pathlib import Path
from config_manager import ConfigManager
from file_type_handler import FileTypeHandler
import io
import datetime
from os.path import dirname, abspath, join

class FileServer:
    def __init__(self, mount_folder_relative_from_file: Path = None) -> None:
        self.BASE_DIRS = []
        base_path = os.path.dirname(__file__)
        for dir in ConfigManager.get_root_dirs():
            dir = f'{base_path}/{dir}'
            self.BASE_DIRS.append(Path(dir).resolve())
        self.FILE_HANDLERS = {}
        if mount_folder_relative_from_file is None:
            self.mount_folder = f'{abspath(dirname(__file__))}/.mounts/'
        else:
            self.mount_folder = f'{abspath(dirname(__file__))}/{mount_folder_relative_from_file}'
            
    def get_mount_folder(self) -> str:
        return self.mount_folder

    def get_abs_path(self, req_path: str):
        # This is in a subfunction because I might want to split some logic in the future
        def construct_req_path(req_path: str):
            basedir = self.mount_folder
            if req_path.__len__() == 0:
                return Path(basedir)
            return Path(abspath(f'{basedir}/{req_path}'))
        constructed_path_object = construct_req_path(req_path=req_path)
        return constructed_path_object
            

    def get_dir_contents(self, abs_path: Path):
        items = []
        for item in abs_path.iterdir():
            # @todo Meaby make this a object in the future.
            items.append({
                'name': item.name, 
                'path': item.name, 
                'is_file': item.is_file(), 
                'size': self.convert_size(self.get_file_size(item)), 
                'mod_date': self.get_modification_time(item)
                })
        return items
    
    def get_file_handler(self, req_path: str):
        rel_path = Path(req_path)
        for base_dir in self.BASE_DIRS:
            abs_path = (base_dir / rel_path).resolve()
            if abs_path.is_file() and os.path.getsize(abs_path) > 0:
                _, ext = os.path.splitext(req_path)
                handler_class = self.FILE_HANDLERS.get(ext, FileTypeHandler)  # Use FileTypeHandler as default
                return handler_class(self, req_path)  # Pass self (instance of FileServer) to handler
        return None

    def load_file_handlers(self, handlers_config: dict):
        for ext, handler_name in handlers_config.items():
            HandlerClass = getattr(importlib.import_module("file_type_handler"), handler_name)
            self.FILE_HANDLERS[ext] = HandlerClass
            
    def get_file_size(self, file_path):
        return os.path.getsize(file_path)

    def get_modification_time(self, file_path):
        timestamp = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(timestamp)
    
    def convert_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s%s" % (s, size_name[i])