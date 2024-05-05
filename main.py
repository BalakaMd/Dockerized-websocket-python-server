import mimetypes
import socket
import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote_plus
from http.server import HTTPServer, BaseHTTPRequestHandler
from pymongo import MongoClient

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent
jinja = Environment(loader=FileSystemLoader(BASE_DIR.joinpath("templates")))

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['messages_db']
collection = db['messages']


class Framework(BaseHTTPRequestHandler):
    def do_GET(self):
        router = urlparse(self.path).path
        match router:
            case "/":
                self.send_html("index.html")
            case "/message":
                self.send_html("message.html")
            case _:
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
        server_address = ('localhost', 5000)
        sock.sendto(data.encode(), server_address)


def run_http_server(server_class=HTTPServer, handler_class=Framework):
    server_address = ("", 3000)
    httpd = server_class(server_address, handler_class)
    print("HTTP Server running on port 3000")
    httpd.serve_forever()


def run_socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 5000)
    sock.bind(server_address)
    print("Socket Server running on port 5000")

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
