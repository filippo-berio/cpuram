import http.server
import os
import sqlite3
import socketserver
import flask
import base64
from datetime import datetime
from flask import send_file

NUM_POINTS = 100

app = flask.Flask("cpuram")

@app.route("/favicon.png")
def favicon():
    return send_file("./favicon.png", "image/png")
    with open('./favicon.png', 'r') as file:
        resp = flask.Response(file.read())
        resp.headers["Content-Type"] = "image/png"
        return resp

@app.route("/chart.js")
def chartjs():
    with open('./chart.js', 'r') as js_file:
        resp = flask.Response(js_file.read())
        resp.headers["Content-Type"] = "text/javascript"
        return resp

def ts_to_dt(ts):
    return f"'{datetime.utcfromtimestamp(ts).strftime('%d.%m %H:%M:%S')}'"
    
def make_chart(label, rows, interval, param_order_in_rows, avg=False):
    interval = int(interval)
    num_points = min(NUM_POINTS, len(rows) // interval)
    
    labels =  []
    points = []
    r = len(rows)-1
    while r >= 0 and len(labels) < num_points:
        labels.append(ts_to_dt(rows[r][2]))
        sum = 0
        if avg:
            for i in range(interval):
                sum += rows[r][param_order_in_rows]
                r -= 1
            points.append(str(sum/interval))
        else:
            points.append(str(rows[r][param_order_in_rows]))
            r -= interval
    
    labels.reverse()
    points.reverse()
    
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
          plugins: {
            customCanvasBackgroundColor: {
              color: '#222222',
            }
          },
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
    interval_select = flask.request.args.get("intervalSelect")
    interval = flask.request.args.get("interval")
    if interval:
        interval_select = None
    
    interval_sql = interval
    if not interval_sql:
        interval_sql = interval_select
    if not interval_sql:
        interval_sql = 300
        
    res = db.execute("select cpu, ram, ts + 5*3600 from metrics order by ts desc limit ?", (int(interval_sql) * NUM_POINTS, ))
    rows = res.fetchall()
    rows.reverse()
    db_conn.close()

    mode = flask.request.args.get("mode")
    if not mode:
        mode = "avg"
    modes = ["avg", "absolute"]
    mode_html = ""
    for m in modes:
        checked = ""
        if mode == m:
            checked = "checked"
        mode_html += f'<label for="{m}">{m}</label><input type="radio" {checked} name="mode" id="{m}" value="{m}">'
  
    interval_options = {
        60: "1 minute",
        300: "5 minutes",
        900: "15 minutes",
        1800: "30 minutes",
        3600: "1 hour",
    }
    options_html = ""
    for v, t in interval_options.items():
        selected = ""
        if str(v) == str(interval_select):
            selected = "selected"
        options_html += f"<option value='{v}' {selected}>{t}</option>"
        
    return '''
        <html>
        <head>
        <title>CpuRam</title>
        <link rel="icon" type="image/png" href="/favicon.png"/>
        </head>
        <body style="background-color:#222222; color:#FFFFFF">
        <script src="/chart.js"></script>
        <form action="/">
            %s
            
            <input type="number" name="interval" value="%s">
            <select name="intervalSelect">
                <option value="">choose interval</option>
                %s
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
        </html>''' % (mode_html, interval, options_html, 
            make_chart("cpu", rows, interval_sql, 0, mode=="avg"), 
            make_chart("ram", rows, interval_sql, 1, mode=="avg"))

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
