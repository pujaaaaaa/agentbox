"""
AgentBox - The Local-First AI Flight Recorder
Zero Dependencies. 100% Local SQLite. Include Token & Financial Tracking
"""

import os
import sqlite3
import json
import time
import inspect
from functools import wraps
from http.server import BaseHTTPRequestHandler, HTTPServer

class AgentBoxLogger:
    def __init__(self, db_path="agentbox_logs.db"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, db_path)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                agent_name TEXT,
                prompt TEXT,
                output TEXT,
                latency_seconds REAL,
                status TEXT
            )
        ''')
       
        # SCHEMA UPGRADE ENGINE: Dynamically add tracking columns if they don't exist
        try:
            cursor.execute("ALTER TABLE ai_logs ADD COLUMN input_tokens INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE ai_logs ADD COLUMN output_tokens INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE ai_logs ADD COLUMN cost_usd REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass  # Columns already provisioned in previous runs
           
        conn.commit()
        conn.close()

    def log_execution(self, agent_name, prompt, output, latency, status, input_tokens=0, output_tokens=0, cost_usd=0.0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
       
        if isinstance(output, (dict, list)):
            output = json.dumps(output, indent=2)
           
        cursor.execute('''
            INSERT INTO ai_logs (timestamp, agent_name, prompt, output, latency_seconds, status, input_tokens, output_tokens, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (time.time(), agent_name, str(prompt), str(output), latency, status, input_tokens, output_tokens, cost_usd))
        conn.commit()
        conn.close()

logger = AgentBoxLogger()

def record_agent(name="Unnamed_Agent"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            prompt = kwargs.get('prompt', args[0] if args else "No prompt found")
            status = "SUCCESS"
            output = ""
           
            input_tokens = 0
            output_tokens = 0
            cost_usd = 0.0
           
            try:
                output = func(*args, **kwargs)
                return output
            except Exception as e:
                status = f"ERROR: {str(e)}"
                output = "Execution Failed."
                raise e
            finally:
                latency = round(time.time() - start_time, 2)
               
                # --- REFLECTION METADATA HARVESTER ENGINE ---
                found_monitor = None
                # Method A: Search named arguments
                for val in kwargs.values():
                    if hasattr(val, 'monitor'):
                        found_monitor = val.monitor
                        break
                # Method B: Search standard arguments
                if not found_monitor:
                    for arg in args:
                        if hasattr(arg, 'monitor'):
                            found_monitor = arg.monitor
                            break
                # Method C: Reflectively scan parent execution context
                if not found_monitor:
                    try:
                        frame = inspect.currentframe()
                        caller_globals = frame.f_back.f_globals
                        for val in caller_globals.values():
                            if hasattr(val, 'monitor'):
                                found_monitor = val.monitor
                                break
                    except Exception:
                        pass
               
                # If an agent framework monitor is localized, dissect its tracking fields
                if found_monitor:
                    input_tokens = getattr(found_monitor, 'total_input_token_count', 0) or getattr(found_monitor, 'input_tokens', 0)
                    output_tokens = getattr(found_monitor, 'total_output_token_count', 0) or getattr(found_monitor, 'output_tokens', 0)
                   
                    # Cost Index Matrix: Blended industry standard ($2.50 / 1M Input, $10.00 / 1M Output)
                    cost_usd = (input_tokens * 0.0000025) + (output_tokens * 0.000010)
                    cost_usd = round(cost_usd, 6)

                logger.log_execution(name, prompt, output, latency, status, input_tokens, output_tokens, cost_usd)
                print(f"[AgentBox] Logged analytical metrics for '{name}' successfully.")
               
        return wrapper
    return decorator

# --- DASHBOARD SERVER ---
class UIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
           
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_file = os.path.join(base_dir, "agentbox_logs.db")
           
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, agent_name, prompt, output, latency_seconds, status, input_tokens, output_tokens, cost_usd FROM ai_logs ORDER BY timestamp DESC LIMIT 50")
            rows = cursor.fetchall()
            conn.close()

            html = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <title>AgentBox UI</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif; background-color: #f8f9fa; margin: 40px; color: #212529; }}
                    .container {{ max-width: 900px; margin: auto; }}
                    .card {{ background: white; padding: 20px; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; border-left: 5px solid #0d6efd; }}
                    .error {{ border-left: 5px solid #dc3545; }}
                    pre {{ background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }}
                    .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }}
                    .badge-success {{ background: #d1e7dd; color: #0f5132; }}
                    .badge-error {{ background: #f8d7da; color: #842029; }}
                    .analytics-strip {{ font-size: 0.9em; margin-bottom: 12px; color: #495057; background: #e9ecef; padding: 10px; border-radius: 4px; border: 1px solid #ced4da; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✈️ AgentBox Flight Recorder</h1>
                    <p>Local AI Agent Logs | <strong>Zero Cloud Dependencies</strong></p>
                    <hr>
            """
            if not rows:
                html += "<p style='color: #666;'>No AI logs captured yet.</p>"
           
            for row in rows:
                time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row[0]))
                is_success = row[5] == "SUCCESS"
                card_style = "card" if is_success else "card error"
                badge_style = "badge badge-success" if is_success else "badge badge-error"
               
                inp_tok = row[6]
                out_tok = row[7]
                tot_tok = inp_tok + out_tok
                financials = row[8]
               
                html += f"""
                <div class="{card_style}">
                    <div style="margin-bottom: 10px;">
                        <strong>Agent:</strong> {row[1]} |
                        <strong>Time:</strong> {time_str} |
                        <strong>Duration:</strong> {row[4]}s |
                        <span class="{badge_style}">{row[5]}</span>
                    </div>
                   
                    <div class="analytics-strip">
                        📊 <strong>Token Consumption:</strong> {inp_tok} In / {out_tok} Out (<strong>{tot_tok} Total</strong>) |
                        💸 <strong>Estimated Run Cost:</strong> <span style="color: #198754; font-weight: bold;">${financials:.5f}</span>
                    </div>

                    <strong>Input Arguments / Context:</strong>
                    <pre>{row[2]}</pre>
                    <strong>Execution Strategy / Output:</strong>
                    <pre>{row[3]}</pre>
                </div>
                """
            html += "</div></body></html>"
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_dashboard(port=8888):
    server = HTTPServer(("127.0.0.1", port), UIHandler)
    print(f"✈️ AgentBox Dashboard is spinning up at http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_dashboard(port=8888)
