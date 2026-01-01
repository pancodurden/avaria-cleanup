import os
import platform
import json
import time
import webbrowser # YENİ: Tarayıcı açmak için
from threading import Timer # YENİ: Zamanlama için
from flask import Flask, render_template, Response, stream_with_context

# static_folder ve template_folder yollarını PyInstaller uyumlu hale getiriyoruz
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)

# --- BU KISIM AYNI KALIYOR (MOTOR) ---
class SistemTemizleyici:
    def __init__(self):
        self.sistem = platform.system()
        self.islemci = platform.processor()
        self.kullanici_yolu = os.path.expanduser('~')
        self.hedef_yollar = self.adresleri_belirle()

    def adresleri_belirle(self):
        yollar = []
        if self.sistem == "Windows":
            yollar = [
                os.getenv('TEMP'),
                os.path.join(os.getenv('SystemRoot'), 'Temp'),
                os.path.join(os.getenv('SystemRoot'), 'Prefetch'),
            ]
        elif self.sistem == "Darwin": # macOS
            yollar = [
                os.path.join(self.kullanici_yolu, 'Library/Caches'),
                os.path.join(self.kullanici_yolu, 'Library/Logs'),
                '/private/var/tmp',
            ]
        elif self.sistem == "Linux":
            yollar = [
                os.path.join(self.kullanici_yolu, '.cache'),
                '/tmp',
                '/var/tmp'
            ]
        return yollar

    def toplam_dosya_sayisi_bul(self):
        sayac = 0
        for yol in self.hedef_yollar:
            if os.path.exists(yol):
                for kok, _, dosyalar in os.walk(yol):
                    sayac += len(dosyalar)
        return sayac if sayac > 0 else 1

motor = SistemTemizleyici()

@app.route('/')
def ana_sayfa():
    return render_template('index.html')

@app.route('/stream/tara')
def stream_tara():
    def generate():
        toplam_dosya = motor.toplam_dosya_sayisi_bul()
        islenen_dosya = 0
        toplam_boyut = 0
        
        yield f"data: {json.dumps({'tip': 'info', 'os': f'{motor.sistem}'})}\n\n"

        for yol in motor.hedef_yollar:
            if os.path.exists(yol):
                for kok, _, dosyalar in os.walk(yol):
                    for dosya in dosyalar:
                        dosya_yolu = os.path.join(kok, dosya)
                        try:
                            boyut = os.path.getsize(dosya_yolu)
                            toplam_boyut += boyut
                        except:
                            boyut = 0

                        islenen_dosya += 1
                        yuzde = (islenen_dosya / toplam_dosya) * 100
                        
                        data = {
                            "tip": "progress",
                            "dosya": dosya,
                            "yuzde": round(yuzde, 1),
                            "toplam_gb": round(toplam_boyut / (1024**3), 3)
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                        time.sleep(0.002) 

        yield f"data: {json.dumps({'tip': 'done'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/temizle')
def api_temizle():
    silinen_sayisi = 0
    toplam_alan = 0
    for yol in motor.hedef_yollar:
        if os.path.exists(yol):
            for kok, _, dosyalar in os.walk(yol):
                for dosya in dosyalar:
                    try:
                        dosya_yolu = os.path.join(kok, dosya)
                        boyut = os.path.getsize(dosya_yolu)
                        os.remove(dosya_yolu)
                        silinen_sayisi += 1
                        toplam_alan += boyut
                    except: pass
    
    gb_kazanc = toplam_alan / (1024**3)
    return json.dumps({'silinen': silinen_sayisi, 'kazanc': round(gb_kazanc, 3)})

# --- FİNAL AYARLARI (YENİ) ---
def tarayiciyi_ac():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    # 1 saniye sonra tarayıcıyı aç diyoruz
    Timer(1, tarayiciyi_ac).start()
    # Debug False olmalı yoksa uygulama açılmaz!
    app.run(port=5000, debug=False)