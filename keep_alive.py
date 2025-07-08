from flask import Flask, render_template_string
from threading import Thread

def keep_alive(get_uptime, recent_resets):
    app = Flask('')

    @app.route('/')
    def home():
        html = f"""
        <html>
        <head>
            <title>Bot Uptime: {get_uptime()}</title>
            <style>
                body {{ font-family: sans-serif; background: #1e1e1e; color: white; padding: 20px; }}
                h1 {{ color: #00ff99; }}
                pre {{ background: #2e2e2e; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>🤖 Universal Farm HWID Bot</h1>
            <p>✅ Bot is alive!</p>
            <p>🕒 Uptime: <b>{get_uptime()}</b></p>
            <h2>📜 Latest Resets</h2>
            <pre>{chr(10).join(recent_resets) or "No resets yet."}</pre>
        </body>
        </html>
        """
        return render_template_string(html)

    def run():
        app.run(host='0.0.0.0', port=8080)

    t = Thread(target=run)
    t.start()
