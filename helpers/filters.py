from typing import List, Dict
import re

    
def sort_files_and_dirs(files_and_dirs: List[Dict], directories_first: bool = True, sort_asc: bool = True) -> List[Dict]:
    # Natural sorting key
    def natural_sort_key(s: str):
        return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
    
    # Adjusting the sorting key to prioritize '..' directory and implement natural sorting
    def sort_key(item):
        name = item['name']
        if name == '..':
            # If sorting in ascending order, we want '..' at the very start
            # If sorting in descending order, we want '..' at the very end
            prefix = -1 if sort_asc else float('inf')
        else:
            prefix = 0
        return (prefix, natural_sort_key(name))

    # Separate directories and files
    directories = [item for item in files_and_dirs if not item['is_file']]
    files = [item for item in files_and_dirs if item['is_file']]

    # Sort directories and files independently using the custom sorting key
    directories.sort(key=sort_key, reverse=not sort_asc)
    files.sort(key=sort_key, reverse=not sort_asc)

    # Concatenate and return the sorted lists based on the 'directories_first' parameter
    if directories_first:
        return directories + files
    else:
        return files + directories
    
def add_icons(items):
    from server import app_instance
    for item in items:
        if item['is_file']:
            file_handler = app_instance.file_server.get_file_handler(item['name'])
            if isinstance(file_handler, bool) and file_handler is False:
                item['icon'] = 'fas fa-folder'
            else:
                if file_handler is None:
                    item['icon'] = 'fas fa-file'
                else:
                    item['icon'] = file_handler.icon
        else:
            item['icon'] = 'fas fa-folder'
    return items