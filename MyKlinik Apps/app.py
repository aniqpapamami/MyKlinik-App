import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "klinik_rahsia_123"   # Tukar kepada password yang lebih kuat di production

# === URL FIREBASE ANDA ===
BASE_URL = "https://myklinik-queue-line-system-default-rtdb.asia-southeast1.firebasedatabase.app/"

def get_today():
    """Dapatkan tarikh Malaysia (UTC+8)"""
    return (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d')

def get_current_time():
    return (datetime.now() + timedelta(hours=8)).strftime('%H:%M:%S')

# ==================== ROUTES UTAMA ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/daftar')
def daftar():
    return render_template('daftar.html')

@app.route('/monitor')
def monitor():
    return render_template('monitor.html')

# ==================== ADMIN ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == "admin" and password == "klinik123":
            session['admin_logged_in'] = True
            return redirect('/dashboard')
        else:
            return redirect('/admin/login?error=1')
    
    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

# ==================== API ====================

@app.route('/api/daftar', methods=['POST'])
def api_daftar():
    try:
        data = request.get_json()
        today = get_today()
        waktu = get_current_time()

        # Dapatkan nombor giliran seterusnya
        res = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        no_baru = (res.json() or 0) + 1

        # Simpan jumlah giliran
        requests.put(f"{BASE_URL}/harian/{today}/jumlah_giliran.json", json=no_baru)

        # Simpan data pesakit
        requests.put(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", json={
            'nama': data.get('nama'),
            'no_ic': data.get('no_ic'),
            'no_hp': data.get('no_hp'),
            'no_giliran': no_baru,
            'status': 'menunggu',
            'masa': waktu
        })

        # Pastikan nombor_sekarang wujud (untuk hari baru)
        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        if res_now.json() is None:
            requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)

        return jsonify({
            'success': True,
            'no_giliran': no_baru,
            'nama': data.get('nama')
        })

    except Exception as e:
        print("Error daftar:", e)
        return jsonify({'success': False, 'message': 'Ralat semasa mendaftar'}), 500


@app.route('/api/status_live')
def status_live():
    today = get_today()
    try:
        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")

        return jsonify({
            'nombor_sekarang': res_now.json() or 0,
            'jumlah_giliran': res_total.json() or 0
        })
    except:
        return jsonify({'nombor_sekarang': 0, 'jumlah_giliran': 0})


@app.route('/api/next', methods=['POST'])
def api_next():
    today = get_today()
    try:
        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")

        no_skrg = res_now.json() or 0
        total = res_total.json() or 0

        if no_skrg >= total:
            return jsonify({'success': False, 'message': 'Tiada pesakit menunggu lagi.'})

        no_baru = no_skrg + 1

        # Update nombor sekarang
        requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=no_baru)
        
        # Update status pesakit tersebut
        requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", 
                      json={'status': 'sedang_dirawat'})

        return jsonify({'success': True})

    except Exception as e:
        print("Error next:", e)
        return jsonify({'success': False, 'message': 'Ralat panggil nombor'}), 500


@app.route('/api/kemaskini_status', methods=['POST'])
def kemaskini_status():
    try:
        data = request.get_json()
        today = get_today()
        no_giliran = data.get('no_giliran')
        status = data.get('status')

        if not no_giliran or status not in ['selesai', 'tidak_hadir']:
            return jsonify({'success': False, 'message': 'Data tidak sah'}), 400

        requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_giliran}.json",
                       json={'status': status})

        return jsonify({'success': True})

    except Exception as e:
        print("Error kemaskini status:", e)
        return jsonify({'success': False, 'message': 'Ralat kemaskini status'}), 500


@app.route('/api/get_senarai_tarikh/<tarikh>')
def get_senarai_tarikh(tarikh):
    try:
        res = requests.get(f"{BASE_URL}/harian/{tarikh}/senarai_pesakit.json")
        data = res.json() or {}
        
        # Pastikan return list (bukan object) supaya frontend tak error
        if isinstance(data, dict):
            senarai = list(data.values())
            # Filter None
            senarai = [item for item in senarai if item is not None]
            return jsonify(senarai)
        
        return jsonify([])
    except Exception as e:
        print("Error get senarai:", e)
        return jsonify([])


# ==================== RUN ====================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)