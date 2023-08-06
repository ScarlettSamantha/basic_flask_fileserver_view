# Flask File Server

This is a simple file server built with Flask and Bootstrap. It serves files over HTTP and also provides a basic web interface for navigating directories. The server uses HTTP Basic Authentication and logs each request to a log file. 

The application is Dockerized and can be easily set up using Docker Compose. 

## Running the Server

1. Install the dependencies:

```bash
pip install flask flask_httpauth gunicorn
```

2. Copy `config.json.sample` to `config.json` and update the configuration according to your needs.

3. Run the server:

```bash
gunicorn -w 4 server:app
```

The server will run on `localhost:8000`.

Alternatively, you can run the server using Docker:

1. Build the Docker image:

```bash
docker-compose build
```

2. Run the Docker container:

```bash
docker-compose up
```

The server will run on `localhost:8000`.

## Configuration

The server's behavior can be configured by modifying the `config.json` file. The following options are available:

- `follow_symlinks`: Determines whether the server will follow symbolic links. If set to `false`, any symbolic links will be ignored.
- `root_dirs`: A list of directories that will be served by the file server.
- `file_handlers`: A dictionary mapping file extensions to the names of `FileTypeHandler` subclasses that will handle those file types.
- `auth`: A dictionary with a `username` and `password` that will be used for HTTP Basic Authentication.

## File Type Handlers

The server uses different `FileTypeHandler` subclasses to handle different file types. Each handler subclass must implement a `handle()` method that takes no arguments and returns a Flask response. The `DefaultFileHandler` subclass is used for all file types that do not have a specific handler.

Handlers for specific file types can be registered in the `file_handlers` section of the `config.json` file.

## Systemd service

The server can be run as a systemd service. A sample service file is included in the repository. You may need to modify the `User`, `WorkingDirectory`, and `ExecStart` options in this file to match your setup.

## Logging

The server logs each request to `logs/access.log`. The log includes the URL, HTTP method, and IP address of each request.

## Docker

The server can be run in a Docker container. Two volumes are defined in the `docker-compose.yml` file that map to directories on the host machine. These directories are used as the root directories for the file server. You may need to modify the `device` options in the `docker-compose.yml` file and the `root_dirs` option in the `config.json` file to match your setup.