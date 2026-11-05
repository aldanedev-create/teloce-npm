"""Build and serve the Three.js Teloce-NPM example without a web framework."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from teloce.build import build_project

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"


class ExampleHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def do_GET(self):
        if self.path == "/":
            body = (ROOT / "templates" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


if __name__ == "__main__":
    build_project(ROOT, out_dir=DIST, options={"clean": True, "shared_runtime": True})
    server = ThreadingHTTPServer(("127.0.0.1", 8775), ExampleHandler)
    print("Three.js example running at http://127.0.0.1:8775")
    server.serve_forever()
