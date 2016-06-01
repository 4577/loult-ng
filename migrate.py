#!/usr/bin/python2
#-*- encoding: Utf-8 -*-
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

class CookieServer(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', 'http://loult.family')
        self.send_header('Access-Control-Allow-Methods', 'OPTIONS, GET')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', 'http://loult.family')
        self.send_header('Access-Control-Allow-Methods', 'OPTIONS, GET')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
        self.wfile.write(self.headers.get('Cookie'))

HTTPServer(('0.0.0.0', 49301), CookieServer).serve_forever()
