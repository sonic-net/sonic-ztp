'''
Copyright 2019 Broadcom. The term "Broadcom" refers to Broadcom Inc.
and/or its subsidiaries.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import multiprocessing
import sys
import os

if sys.version_info[0] == 3:
    import http.server
    from http.server import BaseHTTPRequestHandler, HTTPServer
else:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class Data:
    def set(self, port=2000, timeout=0, text='', http_error_code=None):
        self.port = port
        self.timeout = timeout
        self.text = text
        self.http_error_code = http_error_code

data = Data()

class myHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if data.timeout is not None and data.timeout > 0:
            time.sleep(data.timeout + 5)
        if data.http_error_code is not None:
            self.send_response(data.http_error_code)
        else:
            self.send_response(200)
        self.end_headers()
        self.wfile.write(data.text.encode('utf-8'))

    def log_message(self, format, *args):
        return

class HttpServer:

    def func(self, port, timeout, text):
        self.server = HTTPServer(('', port), myHandler)
        self.server.serve_forever()

    def start(self, port=2000, timeout=None, text='', http_error_code=None):
        data.set(port, timeout, text, http_error_code)
        self.keep_running = True
        self.process = multiprocessing.Process(target=self.func, args=(port, timeout, text))
        self.process.start()

    def stop(self):
        self.keep_running = False
        self.process.terminate()
        self.process.join()

## Create a symlink file.py to file
def createPySymlink(plugin_file):
    plugin_file_py = plugin_file.replace('-', '_') + '.py'
    if os.path.isfile(plugin_file_py) is False:
        os.symlink(plugin_file, plugin_file_py)
