from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
import os
import json

app = Flask(__name__)

# GANTIKAN 'KOD_RAHSIA_DATABASE' dengan kod yang anda salin di Langkah 1
# GANTIKAN URL dengan URL database anda yang betul
if not firebase_admin._apps:
    cred = credentials.InternalServiceAccountCredentials() # Ini sekadar placeholder
    firebase_admin.initialize_app(None, {
        'databaseURL': 'https://myklinik-queue-line-system-default-rtdb.asia-southeast1.firebasedatabase.app',
        'databaseAuthVariableOverride': None
    })

# Fungsi alternatif untuk akses database menggunakan Secret
def get_db_ref(path):
    # GANTIKAN Teks di bawah dengan Secret dari Firebase Langkah 1
    SECRET = gR5AQrjY7m8ZXbTUO1ZXFR2PJ0GPlcSWrWCvshJF 
    return db.reference(path, url='https://myklinik-queue-line-system-default-rtdb.asia-southeast1.firebasedatabase.app' + SECRET)

# --- UBAH FUNGSI API ANDA ---

@app.route('/api/daftar', methods=['POST'])
def daftar_pesakit():
    nama = request.json.get('nama')
    ref_jumlah = get_db_ref('jumlah_giliran') # Guna fungsi baru
    no_baru = (ref_jumlah.get() or 0) + 1
    ref_jumlah.set(no_baru)
    
    get_db_ref(f'senarai_pesakit/{no_baru}').set({
        'nama': nama,
        'no_giliran': no_baru,
        'status': 'menunggu'
    })
    return jsonify({'no_giliran': no_baru, 'nama': nama})

@app.route('/api/status_live')
def status_live():
    no_sekarang = get_db_ref('nombor_sekarang').get() or 0 # Guna fungsi baru
    return jsonify({'nombor_sekarang': no_sekarang})

@app.route('/')
def home():
    return render_template('daftar.html')

@app.route('/status_page')
def status_page():
    return render_template('status.html')

@app.route('/admin_page')
def admin_page():
    return render_template('admin.html')

# API: Ambil Nombor (Untuk daftar.html)
@app.route('/api/daftar', methods=['POST'])
def daftar_pesakit():
    nama = request.json.get('nama')
    ref_jumlah = db.reference('jumlah_giliran')
    no_baru = (ref_jumlah.get() or 0) + 1
    ref_jumlah.set(no_baru)
    
    db.reference(f'senarai_pesakit/{no_baru}').set({
        'nama': nama,
        'no_giliran': no_baru,
        'status': 'menunggu'
    })
    return jsonify({'no_giliran': no_baru, 'nama': nama})

# API: Panggil Seterusnya (Untuk admin.html)
@app.route('/api/next', methods=['POST'])
def panggil_next():
    ref_sekarang = db.reference('nombor_sekarang')
    no_skrg = (ref_sekarang.get() or 0) + 1
    ref_sekarang.set(no_skrg)
    return jsonify({'nombor_sekarang': no_skrg})

# API: Get Status Live (Untuk status.html)
@app.route('/api/status_live')
def status_live():
    no_sekarang = db.reference('nombor_sekarang').get() or 0
    return jsonify({'nombor_sekarang': no_sekarang})

if __name__ == '__main__':
    app.run(debug=True)
	