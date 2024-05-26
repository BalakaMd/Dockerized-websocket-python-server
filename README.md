# README.md

## Project Overview

This project is a simple web server built using Python's `http.server` module, combined with a UDP socket server and MongoDB for storing messages. The web server serves HTML files and static content, while the socket server receives and processes form data, which is then stored in a MongoDB collection. The project also utilizes Docker for containerization, making it easy to deploy and manage.

## Features

- Serves HTML and static files
- Handles GET and POST requests
- Sends form data via a UDP socket
- Stores received data in a MongoDB database
- Dockerized setup for easy deployment

## Prerequisites

- Python 3.x
- Docker
- Docker Compose
- `pymongo` library

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/BalakaMD/dockerized-websocket-python-server.git
    cd dockerized-websocket-python-server
    ```

2. Ensure Docker and Docker Compose are installed on your machine.

## Usage

1. Create the required HTML files (`index.html`, `message.html`, `error.html`) in the project directory.

2. Build and run the Docker containers:
    ```sh
    docker-compose up --build
    ```

### Docker Setup

This project includes a `Dockerfile` and a `docker-compose.yml` file.

#### Dockerfile

```Dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY . /app

RUN pip install pymongo

CMD ["python", "server.py"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
  db:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongo-data:/data/db

volumes:
  mongo-data:
```

## Code Explanation

### server.py

```python
import mimetypes
import socket
import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote_plus
from http.server import HTTPServer, BaseHTTPRequestHandler
from pymongo import MongoClient

BASE_DIR = Path(__file__).parent

# MongoDB connection
client = MongoClient('mongodb://db:27017/')
db = client['messages_db']
collection = db['messages']

class Framework(BaseHTTPRequestHandler):
    def do_GET(self):
        router = urlparse(self.path).path
        if (router == "/"):
            self.send_html("index.html")
        elif (router == "/message"):
            self.send_html("message.html")
        else:
            file = BASE_DIR.joinpath(router[1:])
            if file.exists():
                self.send_static(file)
            else:
                self.send_html("error.html", 404)

    def do_POST(self):
        size = int(self.headers["Content-Length"])
        data = self.rfile.read(size).decode()
        data = unquote_plus(data)
        self.send_data_to_socket_server(data)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())

    def send_static(self, filename, status=200):
        self.send_response(status)
        mimetype = mimetypes.guess_type(filename)[0] or "text/plain"
        self.send_header("Content-type", mimetype)
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())

    def send_data_to_socket_server(self, data):
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = ('localhost', 5050)
        sock.sendto(data.encode(), server_address)

def run_http_server(server_class=HTTPServer, handler_class=Framework):
    server_address = ("", 3000)
    httpd = server_class(server_address, handler_class)
    print("HTTP Server running on port 3000")
    httpd.serve_forever()

def run_socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 5050)
    sock.bind(server_address)
    print("Socket Server running on port 5050")

    while True:
        data, address = sock.recvfrom(4096)
        data_dict = {k: v for k, v in (item.split('=') for item in data.decode().split('&'))}
        data_dict["date"] = str(datetime.datetime.now())
        collection.insert_one(data_dict)
        print(f"Received {data.decode()} from {address}")

if __name__ == "__main__":
    from multiprocessing import Process

    http_server = Process(target=run_http_server)
    socket_server = Process(target=run_socket_server)

    http_server.start()
    socket_server.start()

    http_server.join()
    socket_server.join()
```

### Running the Project

1. Ensure Docker and Docker Compose are installed and MongoDB is running inside a Docker container.
2. Run the Docker containers:
    ```sh
    docker-compose up --build
    ```
3. The HTTP server will be running on port 3000 and the socket server on port 5050.
