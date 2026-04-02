import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = "klinik_rahsia_123"

# URL Database anda
BASE_URL = "https://myklinik-queue-line-system-default-rtdb.asia-southeast1.firebasedatabase.app/"

@app.route('/')
def index(): return render_template('daftar.html')

@app.route('/admin/dashboard')
def dashboard():
    return render_template('dashboard.html')

# --- API ---
@app.route('/api/daftar', methods=['POST'])
def api_daftar():
    data = request.json
    res = requests.get(f"{BASE_URL}/jumlah_giliran.json")
    no_baru = (res.json() or 0) + 1
    requests.put(f"{BASE_URL}/jumlah_giliran.json", json=no_baru)
    requests.put(f"{BASE_URL}/senarai_pesakit/{no_baru}.json", json={
        'nama': data.get('nama'),
        'no_hp': data.get('no_hp'),
        'no_giliran': no_baru,
        'status': 'menunggu',
        'masa': datetime.now().strftime('%H:%M:%S')
    })
    return jsonify({'no_giliran': no_baru, 'nama': data.get('nama')})

@app.route('/api/status_live')
def status_live():
    res_now = requests.get(f"{BASE_URL}/nombor_sekarang.json")
    res_total = requests.get(f"{BASE_URL}/jumlah_giliran.json")
    return jsonify({'nombor_sekarang': res_now.json() or 0, 'jumlah_giliran': res_total.json() or 0})

@app.route('/api/get_senarai_hari_ini')
def get_senarai():
    res = requests.get(f"{BASE_URL}/senarai_pesakit.json")
    return jsonify(res.json() or {})

@app.route('/api/update_status', methods=['POST'])
def update_status():
    data = request.json
    requests.patch(f"{BASE_URL}/senarai_pesakit/{data.get('no_giliran')}.json", json={'status': data.get('status')})
    return jsonify({'success': True})

@app.route('/api/next', methods=['POST'])
def panggil_next():
    res = requests.get(f"{BASE_URL}/nombor_sekarang.json")
    no_baru = (res.json() or 0) + 1
    requests.put(f"{BASE_URL}/nombor_sekarang.json", json=no_baru)
    requests.patch(f"{BASE_URL}/senarai_pesakit/{no_baru}.json", json={'status': 'sedang_dirawat'})
    return jsonify({'nombor_sekarang': no_baru})

if __name__ == '__main__':
    app.run(debug=True)