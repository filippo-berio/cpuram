import http.server
import os
import sqlite3
import socketserver
import flask
import base64
from datetime import datetime

NUM_POINTS = 100

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
          animation: { duration: 0 },
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
    interval = flask.request.args.get("interval")
    if not interval:
        interval = flask.request.args.get("intervalSelect")
    if not interval:
        interval = 300
    res = db.execute("select cpu, ram, ts + 5*3600 from metrics where ts % ? = 0 order by ts desc limit ?", (interval, NUM_POINTS))
    rows = res.fetchall()
    rows.reverse()
    db_conn.close()

    return '''
        <html>
        <head><title>CpuRam</title></head>
        <body>
        <script src="/chart.js"></script>
        <form action="/">
        <input type="number" name="interval">
        <select name="intervalSelect">
            <option value="">choose interval</option>
            <option value="60">1 minute</option>
            <option value="300">5 minutes</option>
            <option value="900">15 minutes</option>
            <option value="1800">30 minutes</option>
            <option value="3600">1 hour</option>
        </select>
        <button type="submit">set interval</button>
        
        </form>
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
    host = os.getenv("HOST")
    if host is None:
        print("$HOST not specified")
        exit(1)
    port = os.getenv("PORT")
    if port is None:
        print("$PORT not specified")
        exit(1)
    app.run(host=host, port=int(port))
    
main()
