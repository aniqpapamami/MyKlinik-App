import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime,timedelta
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

# --- API SISTEM ---

@app.route('/api/daftar', methods=['POST'])
def api_daftar():
    try:
        data = request.json
        today = get_today()
        waktu = (datetime.now() + timedelta(hours=8)).strftime('%H:%M:%S')
        
        res = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        no_baru = (res.json() or 0) + 1
        
        requests.put(f"{BASE_URL}/harian/{today}/jumlah_giliran.json", json=no_baru)
        requests.put(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", json={
            'nama': data.get('nama'),
			'no_ic': data.get('no_ic'),
            'no_hp': data.get('no_hp'),
            'no_giliran': no_baru,
            'status': 'menunggu',
            'masa': waktu
        })
        
        # Set nombor_sekarang ke 0 jika belum ada (hari baru)
        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        if res_now.json() is None:
            requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)

        return jsonify({'no_giliran': no_baru, 'nama': data.get('nama')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status_live')
def status_live():
    today = get_today()
    res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
    res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
    return jsonify({
        'nombor_sekarang': res_now.json() or 0,
        'jumlah_giliran': res_total.json() or 0
    })

@app.route('/api/next', methods=['POST'])
def api_next():
    today = get_today()
    res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
    res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
    
    no_skrg = res_now.json() or 0
    total = res_total.json() or 0
    
    if no_skrg >= total:
        return jsonify({'success': False, 'message': 'Tiada pesakit lagi.'})

    no_baru = no_skrg + 1
    requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=no_baru)
    requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", json={'status': 'sedang_dirawat'})
    return jsonify({'success': True, 'no': no_baru})

@app.route('/api/kemaskini_status', methods=['POST'])
def kemaskini_status():
    data = request.json
    today = get_today()
    requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{data['no_giliran']}.json", 
                   json={'status': data['status']})
    return jsonify({'success': True})

@app.route('/api/get_senarai_tarikh/<tarikh>')
def get_senarai_tarikh(tarikh):
    res = requests.get(f"{BASE_URL}/harian/{tarikh}/senarai_pesakit.json")
    return jsonify(res.json() or {})
	
@app.route('/api/padam_pesakit', methods=['POST'])
def padam_pesakit():
    try:
        data = request.json
        no = data.get('no_giliran')
        today = get_today()
        
        if not no:
            return jsonify({'success': False, 'message': 'Nombor giliran tidak dikesan'}), 400

        # Padam rekod pesakit tersebut sahaja di Firebase
        res = requests.delete(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no}.json")
        
        if res.status_code == 200:
            return jsonify({'success': True, 'message': f'Pesakit No {no} telah dipadam.'})
        else:
            return jsonify({'success': False, 'message': 'Gagal memadam dari Firebase'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)