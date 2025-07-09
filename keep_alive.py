from flask import Flask, render_template_string, jsonify
from threading import Thread

app = Flask(__name__)

get_uptime_callback = lambda: "Unknown"
get_recent_resets_callback = lambda: []

@app.route('/')
def home():
    return render_template_string("""
    <html>
    <head>
        <title>Bot Status</title>
        <style>
            body {
                background-color: #2C2F33;
                color: #FFFFFF;
                font-family: Arial, sans-serif;
                padding: 20px;
            }
            .container {
                max-width: 700px;
                margin: auto;
            }
            .embed {
                background-color: #23272A;
                border-left: 5px solid #43B581;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 5px;
                box-shadow: 0 0 5px #000;
            }
            h1, h2 {
                color: #43B581;
            }
            .uptime {
                font-size: 1.2em;
                margin-bottom: 20px;
            }
            .log-entry {
                margin-bottom: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1> Universal Farm HWID Bot</h1>
            <div class="uptime"> Uptime: <span id="uptime">Loading...</span></div>
            <h2> Recent HWID Resets</h2>
            <div id="logs"></div>
        </div>
        <script>
            async function fetchStatus() {
                try {
                    const res = await fetch("/status");
                    const data = await res.json();
                    document.getElementById("uptime").textContent = data.uptime;

                    const logsContainer = document.getElementById("logs");
                    logsContainer.innerHTML = "";
                    data.recent_resets.forEach(entry => {
                        const div = document.createElement("div");
                        div.className = "embed log-entry";
                        div.textContent = entry;
                        logsContainer.appendChild(div);
                    });
                } catch (err) {
                    console.error("Failed to load status:", err);
                }
            }

            fetchStatus();
            setInterval(fetchStatus, 3000);
        </script>
    </body>
    </html>
    """)

@app.route('/status')
def status():
    try:
        uptime = str(get_uptime_callback())
        resets = get_recent_resets_callback()
        if not isinstance(resets, list):
            resets = [str(r) for r in resets]
        return jsonify({
            "uptime": uptime,
            "recent_resets": resets[-30:]  # ✅ Only return last 30 resets
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive(uptime_cb, reset_cb):
    global get_uptime_callback, get_recent_resets_callback
    get_uptime_callback = uptime_cb or (lambda: "Unknown")
    get_recent_resets_callback = reset_cb or (lambda: [])
    thread = Thread(target=run)
    thread.start()
