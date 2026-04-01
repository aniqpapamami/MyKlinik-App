import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = "klinik_rahsia_123"

# URL Database anda
BASE_URL = "https://firebasedatabase.app"

# Fungsi helper untuk dapatkan tarikh hari ini
def get_today():
    return datetime.now().strftime('%Y-%m-%d')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/daftar')
def daftar():
    return render_template('daftar.html')

@app.route('/status_page')
def status_page():
    return render_template('daftar.html') # Kita gabungkan dalam daftar.html

# --- ADMIN ROUTES ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == "admin" and password == "klinik123":
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('dashboard.html')

@app.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

# --- API UNTUK DATA (DATABASE) ---

@app.route('/api/daftar', methods=['POST'])
def api_daftar():
    nama = request.json.get('nama')
    today = get_today()
    
    # 1. Ambil & Naikkan jumlah giliran HARIAN
    res = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
    jumlah_sekarang = res.json() or 0
    no_baru = jumlah_sekarang + 1
    
    # 2. Simpan data ke folder tarikh hari ini
    requests.put(f"{BASE_URL}/harian/{today}/jumlah_giliran.json", json=no_baru)
    requests.put(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", json={
        'nama': nama,
        'no_giliran': no_baru,
        'status': 'menunggu',
        'masa': datetime.now().strftime('%H:%M:%S')
    })
    
    return jsonify({'no_giliran': no_baru, 'nama': nama})

@app.route('/api/next', methods=['POST'])
def panggil_next():
    today = get_today()
    res = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
    no_sekarang = res.json() or 0
    no_baru = no_sekarang + 1
    
    requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=no_baru)
    return jsonify({'nombor_sekarang': no_baru})

@app.route('/api/status_live')
def status_live():
    today = get_today()
    res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
    res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
    
    return jsonify({
        'nombor_sekarang': res_now.json() or 0,
        'jumlah_giliran': res_total.json() or 0
    })

@app.route('/api/stats_mingguan')
def stats_mingguan():
    # Mengambil data dari folder 'harian' untuk bina graf
    res = requests.get(f"{BASE_URL}/harian.json")
    data_harian = res.json() or {}
    
    # Format data untuk Chart.js
    labels = list(data_harian.keys())[-7:] # Ambil 7 hari terakhir
    counts = [data_harian[day].get('jumlah_giliran', 0) for day in labels]
    
    return jsonify({'labels': labels, 'counts': counts})

if __name__ == '__main__':
    app.run(debug=True)