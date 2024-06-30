import http.server
import os
import sqlite3
import socketserver
import flask
import base64
from datetime import datetime

NUM_POINTS = 20

app = flask.Flask("cpuram")

@app.route("/chart.js")
def chartjs():
    with open('./chart.js', 'r') as js_file:
        resp = flask.Response(js_file.read())
        resp.headers["Content-Type"] = "text/javascript"
        return resp


def make_chart(label, rows, param_order_in_rows):
    num_points = min(NUM_POINTS, len(rows))
    labels = [f"'{datetime.utcfromtimestamp(rows[i][2]).strftime('%d.%m %H:%M:%S')}'" for i in range(num_points)]
    points = [str(rows[i][param_order_in_rows]) for i in range(num_points)]
    
    return '''
    new Chart(document.getElementById('%s'), {
        type: 'line',
        data: {
          labels: [%s],
          datasets: [{
            label: '%s',
            data: [%s],
            borderWidth: 1
          }]
        },
        options: {
          scales: {
            y: {
              min: 0, max: 1
            }
          }
        }
      });
    ''' % (label, ",".join(labels), label, ",".join(points))
    
@app.route("/")
def root():
    
    auth = flask.request.headers.get("Authorization")
    if auth is None:
        resp = flask.Response()
        resp.headers["WWW-Authenticate"] = "Basic"
        resp.status = 401
        return resp
       
    expect = base64.b64encode("admin:admin".encode("ascii")).decode("ascii")
    if auth != f"Basic {expect}":
        resp = flask.Response()
        resp.headers["WWW-Authenticate"] = "Basic"
        resp.status = 401
        return resp
        
    db_conn = sqlite3.connect("cpuram.db")
    db = db_conn.cursor()
    offset = flask.request.args.get("offset")
    if offset is None:
        offset = 300
    res = db.execute("select cpu, ram, ts from metrics where ts % ? = 0 order by ts desc limit ?", (offset, NUM_POINTS))
    rows = res.fetchall()
    rows.reverse()
    db_conn.close()

    return '''
        <html>
        <head><title>CpuRam</title></head>
        <body>
        <script src="/chart.js"></script>
        <canvas id="cpu"></canvas>
        <br>
        <canvas id="ram"></canvas>
        
        <script>
        %s
        %s
        </script>
        </body>
        </html>''' % (make_chart("cpu", rows, 0), make_chart("ram", rows, 1))

def main():
    host = ""
    port = "8002"
    app.run(host=host, port=port)
    
main()
