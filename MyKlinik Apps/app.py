import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "klinik_rahsia_123"

BASE_URL = "https://myklinik-queue-line-system-default-rtdb.asia-southeast1.firebasedatabase.app/"

def get_today():
    return (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d')

def get_current_time():
    return (datetime.now() + timedelta(hours=8)).strftime('%H:%M:%S')

# ==================== HELPER ====================
def reset_harian_jika_perlu(today):
    """Reset hanya jika benar-benar tiada pesakit"""
    try:
        res = requests.get(f"{BASE_URL}/harian/{today}/senarai_pesakit.json")
        data = res.json()
        
        # Jika tiada data atau semua nilai None
        if not data or all(v is None for v in data.values()):
            requests.put(f"{BASE_URL}/harian/{today}/jumlah_giliran.json", json=0)
            requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)
            print(f"[RESET] Hari {today} telah direset.")
    except:
        pass

# ==================== ROUTES ====================

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

        reset_harian_jika_perlu(today)

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
        
        # Pastikan nombor_sekarang wujud
        if requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json").json() is None:
            requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)

        return jsonify({'success': True, 'no_giliran': no_baru, 'nama': data.get('nama')})

    except Exception as e:
        print("Error daftar:", e)
        return jsonify({'success': False, 'message': 'Ralat semasa mendaftar'}), 500
		
@app.route('/api/status_live')
def status_live():
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
    try:
        data = request.get_json()
        today = get_today()
        no = data.get('no_giliran')
        status = data.get('status')

        if not no or status not in ['selesai', 'tidak_hadir']:
            return jsonify({'success': False, 'message': 'Data tidak sah'}), 400

        requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{data['no_giliran']}.json",
                       json={'status': data['status']})
        return jsonify({'success': True})

    except Exception as e:
        print("Error kemaskini status:", e)
        return jsonify({'success': False, 'message': 'Ralat kemaskini status'}), 500
# ==================== FUNGSI PALING PENTING ====================
@app.route('/api/get_senarai_tarikh/<tarikh>')
def get_senarai_tarikh(tarikh):
    try:
        res = requests.get(f"{BASE_URL}/harian/{tarikh}/senarai_pesakit.json")
        data = res.json() or {}

        # Tukar object Firebase kepada array (penting untuk dashboard)
        if isinstance(data, dict):
            senarai = [item for item in data.values() if item is not None]
            # Susun mengikut no_giliran
            senarai.sort(key=lambda x: x.get('no_giliran', 0))
            return jsonify(senarai)
        
        return jsonify([])
    except Exception as e:
        print("Error get senarai:", e)
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)		

