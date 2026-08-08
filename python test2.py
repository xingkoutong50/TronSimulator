import time
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8081

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        html = '''<!DOCTYPE html>
<html>
<head><title>测试</title></head>
<body>
<h1>✅ 测试成功！</h1>
<p>服务器正常运行</p>
<p>时间: {}</p>
</body>
</html>'''.format(time.strftime("%Y-%m-%d %H:%M:%S"))
        self.wfile.write(html.encode('utf-8'))

server = HTTPServer(('0.0.0.0', PORT), Handler)
print(f"服务器运行在 http://127.0.0.1:{PORT}")
server.serve_forever()