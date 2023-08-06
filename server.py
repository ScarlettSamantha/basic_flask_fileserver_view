from flask import Flask, render_template, send_from_directory, request, abort, Response
from flask_httpauth import HTTPBasicAuth
from config_manager import ConfigManager
import logging
import os
import atexit
import traceback
from datetime import datetime
from pathlib import Path
from typing import Union

# Load filters
from helpers.filters import sort_files_and_dirs, add_icons

class App:
    def __init__(self):
        from file_server import FileServer
        
        self.app = Flask(__name__)
        self.auth = HTTPBasicAuth()
        self.config_manager = ConfigManager()

        self.error_log = None
        self.access_log = None
        self.base_path = os.path.dirname(__file__)
        
        # Order matters here.
        self.register_config()
        self.setup_logging()
        self.register_pid_file()
        self.file_server = FileServer()
        self.register_file_handlers()
        self.register_filters()
        
        self.setup_utility_routes()
        self.setup_routes()
    
        self.access_log.info("Sucessfully initialized the application, ready for incomming connections")
    
    def register_filters(self):
        self.app.jinja_env.filters['sort_files_and_dirs'] = sort_files_and_dirs
        self.app.jinja_env.filters['add_icons'] = add_icons
        
    def register_file_handlers(self):
        self.file_server.load_file_handlers(self.config_manager.config['file_handlers'])
        
    def register_config(self):
        os.makedirs('logs', exist_ok=True)
        self.config_manager.load_config(self.base_path + '/config.json')

    def register_pid_file(self):
        config = self.config_manager
        pid_file = config.config['pid_file']
        if isinstance(pid_file, str):
            self.error_log.info(f"Started pid file: {str(pid_file)}")
            def create_pid_file():
                with open(pid_file, 'w') as f:
                    f.write(str(os.getpid()))

            def remove_pid_file():
                os.remove(pid_file)
                
            create_pid_file()
            atexit.register(remove_pid_file)
        else:
            self.error_log.info(f"Started without pid file on pid {pid_file}")

    def setup_logging(self):

        # Create a formatter
        log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(module)s:%(message)s')

        def setup_accesslog(self):
            # Set up access log
            self.access_log = logging.getLogger('access')
            self.access_log.setLevel(logging.INFO)
            access_handler = logging.FileHandler('logs/access.log')
            access_handler.setFormatter(log_formatter)  # Set the formatter for the access log
            self.access_log.addHandler(access_handler)

        def setup_errorlog(self):
            # Set up error log
            self.error_log = logging.getLogger('error')
            self.error_log.setLevel(logging.ERROR)
            error_handler = logging.FileHandler('logs/error.log')
            error_handler.setFormatter(log_formatter)  # Set the formatter for the error log
            self.error_log.addHandler(error_handler)

        setup_accesslog(self)
        setup_errorlog(self)

    def setup_utility_routes(self):
        @self.app.errorhandler(Exception)
        def handle_exception(e: Exception) -> tuple[str, int]:
            # Log the error
            exc_type, exc_value, exc_traceback = type(e), e, e.__traceback__
            if hasattr(e, 'code') and e.code == 404:
                return 'file not found', 404
            tb_str = traceback.format_exception(exc_type, exc_value, exc_traceback)
            traceback_str = "".join(tb_str)
            # Log the traceback
            self.error_log.error(f"Traceback: {traceback_str}")
            # return error message
            return 'Internal Server Error', 500
        
        @self.auth.verify_password
        def verify_password(username: str, password: str) -> bool:
            return (username == self.config_manager.config['auth']['username'] and 
                    password == self.config_manager.config['auth']['password'])
            
        @self.app.before_request
        def log_request_info():
            self.access_log.info(f'URL: {request.url} Method: {request.method} IP: {request.remote_addr}')
        
    def setup_routes(self):
        @self.app.route('/', defaults={'req_path': ''})
        @self.app.route('/<path:req_path>')
        @self.auth.login_required
        def dir_listing(req_path: str):
            return self.handle_dir_listing(req_path)

        @self.app.route('/download/<path:req_path>')
        @self.auth.login_required
        def download(req_path: str):
            return self.handle_download(req_path)

    def _resolve_abs_path(self, req_path: str) -> Path:
        if not req_path:
            return Path(os.path.abspath(os.path.join(os.path.dirname(__file__), self.file_server.get_mount_folder())))
        return self.file_server.get_abs_path(req_path)

    def _get_parent_directory_link(self, abs_path: Path) -> str:
        parent_directory = abs_path.parent
        return '' if parent_directory.name == Path(os.path.dirname(self.file_server.get_mount_folder())).name else parent_directory.name

    def _add_parent_directory_to_list(self, abs_path: Path, files_and_dirs: list) -> None:
        parent_directory = abs_path.parent
        path_link = self._get_parent_directory_link(abs_path)
        files_and_dirs.insert(0, {
            'name': '..',
            'path': path_link,
            'is_file': False,
            'size': '4.0KB',
            'last_modified': datetime.fromtimestamp(parent_directory.stat().st_mtime)
        })

    def handle_dir_listing(self, req_path: str) -> Union[str, tuple[str, int]]:
        abs_path = self._resolve_abs_path(req_path)
        
        if not abs_path.exists():
            abort(404)
        
        if abs_path.is_file():
            return self.file_server.get_file_handler(str(abs_path)).handle()
        
        files_and_dirs = self.file_server.get_dir_contents(abs_path)
        self._add_parent_directory_to_list(abs_path, files_and_dirs)
        
        return render_template('index.html', files_and_dirs=files_and_dirs, current_path=req_path, os=os)

    def _validate_file_for_download(self, abs_path: Path) -> None:
        """Validate if the file can be downloaded."""
        if (isinstance(abs_path, bool) and abs_path == False) or not abs_path.exists() or not abs_path.is_file():
            abort(404)

    def _send_empty_file(self, abs_path: Path) -> Response:
        """Send an empty file."""
        with open(abs_path, 'rb') as f:
            content = f.read()
        return Response(content, content_type='application/octet-stream', headers={'Content-Disposition': f'attachment; filename={abs_path.name}'})

    def _send_regular_file(self, req_path: str) -> Response:
        """Send a regular, non-empty file."""
        directory = self.file_server.get_mount_folder()
        file = req_path
        return send_from_directory(directory, file, as_attachment=True)

    def handle_download(self, req_path: str) -> Response:
        abs_path = self.file_server.get_abs_path(req_path)
        self._validate_file_for_download(abs_path)
        
        if abs_path.stat().st_size == 0:
            return self._send_empty_file(abs_path)
        
        return self._send_regular_file(req_path)

    def run(self):
        self.app.run(debug=bool(self.config_manager.config['debug']))

app_instance = App()
app = app_instance.app

if __name__ == '__main__':
    app_instance.run()