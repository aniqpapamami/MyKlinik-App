import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# URL Database anda - PASTIKAN URL INI BETUL
# Nota: Wajib ada /.json di hujung URL untuk cara ini berfungsi
BASE_URL = "https://myklinik-queue-line-system-default-rtdb.asia-southeast1.firebasedatabase.app"

@app.route('/')
def index():
    return render_template('daftar.html')

@app.route('/status_page')
def status_page():
    return render_template('status.html')

@app.route('/admin_page')
def admin_page():
    return render_template('admin.html')

# API: DAFTAR PESAKIT
@app.route('/api/daftar', methods=['POST'])
def daftar_pesakit():
    nama = request.json.get('nama')
    
    # 1. Ambil jumlah giliran terkini
    res = requests.get(f"{BASE_URL}/jumlah_giliran.json")
    jumlah_sekarang = res.json() or 0
    no_baru = jumlah_sekarang + 1
    
    # 2. Simpan nombor baru & data pesakit
    requests.put(f"{BASE_URL}/jumlah_giliran.json", json=no_baru)
    requests.put(f"{BASE_URL}/senarai_pesakit/{no_baru}.json", json={
        'nama': nama,
        'no_giliran': no_baru,
        'status': 'menunggu'
    })
    
    return jsonify({'no_giliran': no_baru, 'nama': nama})

# API: PANGGIL SETERUSNYA (ADMIN)
@app.route('/api/next', methods=['POST'])
def panggil_next():
    res = requests.get(f"{BASE_URL}/nombor_sekarang.json")
    no_sekarang = res.json() or 0
    no_baru = no_sekarang + 1
    
    requests.put(f"{BASE_URL}/nombor_sekarang.json", json=no_baru)
    return jsonify({'nombor_sekarang': no_baru})

# API: AMBIL STATUS LIVE
@app.route('/api/status_live')
def status_live():
    res = requests.get(f"{BASE_URL}/nombor_sekarang.json")
    no_sekarang = res.json() or 0
    return jsonify({'nombor_sekarang': no_sekarang})

if __name__ == '__main__':
    app.run(debug=True)