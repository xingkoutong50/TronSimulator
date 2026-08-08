from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hello World - Test OK!")

server = HTTPServer(('127.0.0.1', 8082), Handler)
print("Server running on http://127.0.0.1:8082")
server.serve_forever()