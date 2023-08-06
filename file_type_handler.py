from abc import ABC, abstractmethod
from flask import render_template, send_from_directory
import os
import io

class FileTypeHandler(ABC):  # Base class for file handlers
    def __init__(self, file_server, file_path):  # FileServer instance is passed to the handler
        self.file_server = file_server
        self.file_path = file_path

    @abstractmethod
    def handle(self):
        pass

    @property
    def icon(self):
        return "fas fa-file"

class DefaultFileHandler(FileTypeHandler):
    def handle(self):
        if os.path.getsize(self.file_path) == 0:
            return ("File is empty", 204)  # return HTTP 204 No Content status code
        else:
            return send_from_directory(self.file_server.BASE_DIR, self.file_path, as_attachment=True)

    @property
    def icon(self):
        return "fas fa-file"

class TextFileHandler(FileTypeHandler):
    def handle(self):
        with io.open(self.file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return render_template('text_view.html', content=content)

    @property
    def icon(self):
        return "fas fa-file-alt"

class ImageFileHandler(FileTypeHandler):
    def handle(self):
        return render_template('image_view.html', image_path=self.file_path)

    @property
    def icon(self):
        return "fas fa-image"