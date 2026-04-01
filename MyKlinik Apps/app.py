import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = "klinik_rahsia_123" # Untuk sistem login

BASE_URL = "https://firebasedatabase.app"

# --- ROUTES AWAM ---

@app.route('/')
def index():
    # Halaman Utama: Info & Promosi
    return render_template('index.html')

@app.route('/daftar')
def daftar():
    # Gabungan Ambil No & Status Live
    return render_template('daftar.html')

# --- ROUTES ADMIN & LOGIN ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Login mudah: Boleh tukar ikut kesesuaian
        if username == "admin" and password == "klinik123":
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('dashboard.html')

# --- API UNTUK DATA & GRAF ---

@app.route('/api/daftar', methods=['POST'])
def api_daftar():
    nama = request.json.get('nama')
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Ambil no baru
    res = requests.get(f"{BASE_URL}/jumlah_giliran.json")
    no_baru = (res.json() or 0) + 1
    requests.put(f"{BASE_URL}/jumlah_giliran.json", json=no_baru)
    
    # Rekodkan pendaftaran harian untuk GRAF
    res_stats = requests.get(f"{BASE_URL}/stats/{today}.json")
    count_today = (res_stats.json() or 0) + 1
    requests.put(f"{BASE_URL}/stats/{today}.json", json=count_today)
    
    return jsonify({'no_giliran': no_baru, 'nama': nama})

@app.route('/api/stats_mingguan')
def stats_mingguan():
    # Ambil data 7 hari terakhir (Simulasi data untuk Graf)
    res = requests.get(f"{BASE_URL}/stats.json")
    stats_data = res.json() or {}
    return jsonify(stats_data)

@app.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)