import cv2
import tkinter as tk
from PIL import Image, ImageTk
import datetime
import random
import csv
import os
import threading
import time
from flask import Flask, Response, render_template_string

# Ovozli javob kutubxonasi
import pyttsx3

# Veb sahifa shabloni
WEB_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>🌟 Aqlli Ko'zgu - Web Panel</title>
  <style>
    body { background: #0f0f1a; color: #f0f0f0; font-family: 'Segoe UI', sans-serif; text-align: center; padding: 20px; }
    img { max-width: 95%; border: 3px solid #e94560; border-radius: 12px; margin-bottom: 20px; }
    table { margin: 0 auto; border-collapse: collapse; width: 80%; }
    th, td { padding: 10px; border: 1px solid #333; }
    th { background: #16213e; color: #00d2ff; }
    tr:nth-child(even) { background: #1a1a2e; }
  </style>
</head>
<body>
  <h1>🌟 Aqlli Ko'zgu — Web Ko'rinishi</h1>
  <img src="{{ url_for('video_feed') }}" alt="Jonli Translyatsiya">
  <h2>📊 So'nggi 10 ta Tashrif</h2>
  <table>
    <tr><th>⏰ Vaqt</th><th>🗣 Salom</th><th>💬 Ibora</th></tr>
    {% for row in stats %}
    <tr><td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td></tr>
    {% endfor %}
  </table>
  <p style="margin-top:30px; color:#888;">🌐 Mahalliy IP: http://<b>127.0.0.1:5000</b> yoki tarmoqdagi qurilmadan oching</p>
</body>
</html>
"""

QUOTES = [
    "Bugungi kuningiz ajoyib o'tsin! ✨",
    "Siz kuchli va iqtidorli odamsiz! 💪",
    "Har bir kichik qadam katta natijaga olib boradi. 🚀",
    "Kulimsirang, dunyo yanada chiroyli bo'ladi! 😊",
    "Sizning potensialingiz cheksiz! 🌟"
]

class SmartDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("🌟 Aqlli Interaktiv Displey")
        self.root.geometry("900x650")
        self.root.configure(bg="#0f0f1a")

        # UI elementlari
        self.greeting_label = tk.Label(root, text="", font=("Helvetica", 32, "bold"), fg="#e94560", bg="#0f0f1a")
        self.greeting_label.pack(pady=15)
        self.quote_label = tk.Label(root, text="", font=("Helvetica", 20, "italic"), fg="#f0f0f0", bg="#0f0f1a")
        self.quote_label.pack(pady=10)
        self.time_label = tk.Label(root, text="", font=("Courier", 18), fg="#00d2ff", bg="#0f0f1a")
        self.time_label.pack(pady=5)
        self.video_label = tk.Label(root, bg="#0f0f1a")
        self.video_label.pack(pady=10)

        # Kamera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("⚠️ Kamera topilmadi. USB kamerani ulab qayta ishga tushiring.")
            self.root.quit()
            return

        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_detected = False
        self.last_quote_time = 0
        self.stats_file = "smart_mirror_stats.csv"

        # Ovoz dvigateli
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 140)
        self.speaking = False
        self.speech_cooldown = 0
        self.last_greeting = ""
        self.last_quote = ""

        # Veb-server fon rejimida
        self.flask_thread = threading.Thread(target=self._run_flask, daemon=True)
        self.flask_thread.start()

        self.current_frame = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_loop()
        self.update_time()

    def update_loop(self):
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            self.face_detected = len(faces) > 0

            # Tkinter uchun RGB format
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil.resize((640, 480)))
            self.video_label.config(image=img_tk)
            self.video_label.image = img_tk  # GC uchun saqlash

            self.current_frame = frame
            self.update_greeting()
            self._trigger_voice()

        self.root.after(30, self.update_loop)

    def update_time(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=f"🕒 {now}")
        self.root.after(1000, self.update_time)

    def update_greeting(self):
        hour = datetime.datetime.now().hour
        if self.face_detected:
            if 5 <= hour < 12:
                g, c = "🌅 Xayrli tong!", "#f4d03f"
            elif 12 <= hour < 17:
                g, c = "☀️ Xayrli kun!", "#e67e22"
            else:
                g, c = "🌙 Xayrli kech!", "#8e44ad"
            self.greeting_label.config(text=g, fg=c)

            now_ts = datetime.datetime.now().timestamp()
            if now_ts - self.last_quote_time > 8:
                q = random.choice(QUOTES)
                self.quote_label.config(text=q, fg="#ffffff")
                self.last_quote_time = now_ts
                self.last_greeting = g
                self.last_quote = q
                self._log_visit(g, q)
        else:
            self.greeting_label.config(text="👋 Kameraga qarang...", fg="#6c757d")
            self.quote_label.config(text="", fg="#4a4a5a")

    def _log_visit(self, greeting, quote):
        with open(self.stats_file, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), greeting, quote])

    def _trigger_voice(self):
        now = time.time()
        if self.face_detected and self.last_greeting and now - self.speech_cooldown > 12 and not self.speaking:
            self.speaking = True
            self.speech_cooldown = now
            threading.Thread(target=self._speak, args=(f"{self.last_greeting}. {self.last_quote}",), daemon=True).start()

    def _speak(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"🔊 Ovoz xatosi: {e}")
        finally:
            self.speaking = False

    def _run_flask(self):
        app = Flask(__name__)

        @app.route('/')
        def index():
            stats = []
            if os.path.exists(self.stats_file):
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    stats = list(csv.reader(f))[-10:]
            return render_template_string(WEB_HTML, stats=stats)

        @app.route('/video_feed')
        def video_feed():
            return Response(self._generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')

        # use_reloader=False muhim! Aks holda 2 marta ishga tushadi
        app.run(host='0.0.0.0', port=5000, use_reloader=False)

    def _generate_mjpeg(self):
        while True:
            if self.current_frame is not None:
                _, jpeg = cv2.imencode('.jpg', self.current_frame)
                frame_bytes = jpeg.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)

    def on_close(self):
        self.cap.release()
        cv2.destroyAllWindows()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartDisplay(root)
    root.mainloop()