import http.server
import os
import sqlite3
import socketserver
import flask

app = flask.Flask("cpuram")
db_conn = sqlite3.connect("cpuram.db")
db = db_conn.cursor()

@app.route("/")
def root():
    return f'''
    <html>
    <head><title>CpuRam</title></head>
    <body><i>nice</i></body>
    </html>'''

def main():
    host = ""
    port = "8002"
    app.run(host=host, port=port)
main()
