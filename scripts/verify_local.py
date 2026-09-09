"""Offline integration smoke check of the installed wheel's dashboard server."""
import http.client
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from glinx_discovery.server import handler_for, web_dir

payload = json.loads((web_dir() / "demo.json").read_text(encoding="utf-8"))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(payload, 0))
port = server.server_address[1]
server.RequestHandlerClass = handler_for(payload, port)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    for path, expected in (("/",200),("/app.js",200),("/model.js",200),("/styles.css",200),("/favicon.svg",200),("/initial.json",200),("/demo.json",200),("/../pyproject.toml",404),("/scan.json",404)):
        conn=http.client.HTTPConnection("127.0.0.1",port,timeout=5)
        conn.request("GET",path)
        response=conn.getresponse()
        body=response.read()
        assert response.status==expected, (path,response.status)
        if path=="/initial.json":
            assert json.loads(body)["mode"]=="demo"
        conn.close()
    conn=http.client.HTTPConnection("127.0.0.1",port,timeout=5)
    conn.request("GET","/initial.json",headers={"Host":"untrusted.example"})
    response=conn.getresponse()
    assert response.status==403
    response.read()
    conn.close()
    print("PASS: packaged dashboard assets, report routing, path boundaries, and Host validation")
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)
