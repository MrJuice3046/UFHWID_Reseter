# keep_alive.py
from flask import Flask, render_template_string, jsonify
from threading import Thread

app = Flask(__name__)

get_uptime_callback = None
get_recent_resets_callback = None

@app.route('/')
def home():
    return render_template_string("""
        <html>
        <head>
            <title>Bot Uptime - <span id="uptime">Loading...</span></title>
            <style>
                body { font-family: Arial; background: #111; color: #0f0; padding: 20px; }
                .log { margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1> Bot is running!</h1>
            <p> Uptime: <span id="uptime-display">Loading...</span></p>
            <div class="log">
                <h3> Recent HWID Resets:</h3>
                <ul id="log"></ul>
            </div>
            <script>
                async function updateStatus() {
                    const res = await fetch('/status');
                    const data = await res.json();
                    document.getElementById("uptime").textContent = data.uptime;
                    document.getElementById("uptime-display").textContent = data.uptime;
                    const log = document.getElementById("log");
                    log.innerHTML = "";
                    data.recent_resets.forEach(entry => {
                        const li = document.createElement("li");
                        li.textContent = entry;
                        log.appendChild(li);
                    });
                }
                setInterval(updateStatus, 1000);
                updateStatus();
            </script>
        </body>
        </html>
    """)

@app.route('/status')
def status():
    return jsonify({
        "uptime": get_uptime_callback(),
        "recent_resets": get_recent_resets_callback()
    })

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive(uptime_cb, reset_cb):
    global get_uptime_callback, get_recent_resets_callback
    get_uptime_callback = uptime_cb
    get_recent_resets_callback = reset_cb
    thread = Thread(target=run)
    thread.start()
