import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "klinik_rahsia_123"

# URL DATABASE FIREBASE ANDA
BASE_URL = "https://myklinik-queue-line-system-default-rtdb.asia-southeast1.firebasedatabase.app/"

def get_today():
    # Mengambil tarikh Malaysia (UTC+8)
    return (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/daftar')
def daftar():
    return render_template('daftar.html')

@app.route('/monitor')
def monitor():
    return render_template('monitor.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == "admin" and request.form.get('password') == "klinik123":
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

# --- API ---

@app.route('/api/daftar', methods=['POST'])
def api_daftar():
    try:
        data = request.json
        if not data or 'nama' not in data:
            return jsonify({'error': 'Data tidak lengkap'}), 400
            
        today = get_today()
        
        # 1. Ambil jumlah (Guna .json di hujung URL)
        res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        jumlah = res_total.json()
        no_baru = (jumlah if jumlah is not None else 0) + 1
        
        # 2. Simpan data (Gunakan PUT)
        requests.put(f"{BASE_URL}/harian/{today}/jumlah_giliran.json", json=no_baru)
        
        # 3. Simpan butiran pesakit
        waktu = (datetime.now() + timedelta(hours=8)).strftime('%H:%M:%S')
        requests.put(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", json={
            'nama': data.get('nama'),
            'no_hp': data.get('no_hp'),
            'no_giliran': no_baru,
            'status': 'menunggu',
            'masa': waktu
        })

        # 4. Pastikan nombor_sekarang ada
        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        if res_now.json() is None:
            requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)

        return jsonify({'no_giliran': no_baru, 'nama': data.get('nama')})
        
    except Exception as e:
        print(f"Ralat Daftar: {e}") # Tengok ralat ni di Render Logs
        return jsonify({'error': 'Gagal mendaftar di server'}), 500

@app.route('/api/status_live')
def status_live():
    try:
        today = get_today()
        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        
        return jsonify({
            'nombor_sekarang': res_now.json() or 0,
            'jumlah_giliran': res_total.json() or 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/next', methods=['POST'])
def panggil_next():
    try:
        today = get_today()
        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        
        no_sekarang = res_now.json() or 0
        total_daftar = res_total.json() or 0
        
        if no_sekarang >= total_daftar:
            return jsonify({
                'success': False, 
                'message': 'Tiada pesakit lagi dalam senarai.',
                'nombor_sekarang': no_sekarang
            }), 400

        no_baru = no_sekarang + 1
        requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=no_baru)
        requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", json={'status': 'sedang_dirawat'})
        
        return jsonify({
            'success': True, # Pastikan T besar
            'nombor_sekarang': no_baru
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_status', methods=['POST'])
def update_status():
    data = request.json
    no = data.get('no_giliran')
    stat = data.get('status')
    today = get_today()
    requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no}.json", json={'status': stat})
    return jsonify({'success': True})

@app.route('/api/get_senarai_hari_ini')
def get_senarai():
    today = get_today()
    res = requests.get(f"{BASE_URL}/harian/{today}/senarai_pesakit.json")
    return jsonify(res.json() or {})
	
@app.route('/api/get_senarai_tarikh/<tarikh>')
def get_senarai_tarikh(tarikh):
    # tarikh akan diterima dalam format YYYY-MM-DD dari frontend
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    res = requests.get(f"{BASE_URL}/harian/{tarikh}/senarai_pesakit.json")
    return jsonify(res.json() or {})	

if __name__ == '__main__':
    app.run(debug=True)