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

        if requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json").json() is None:
            requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)

        return jsonify({'success': True, 'no_giliran': no_baru, 'nama': data.get('nama')})

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
        requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=no_baru)
        requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", 
                      json={'status': 'sedang_dirawat'})
        return jsonify({'success': True})

    except Exception as e:
        print("Error next:", e)
        return jsonify({'success': False, 'message': 'Ralat memanggil nombor'}), 500


@app.route('/api/kemaskini_status', methods=['POST'])
def kemaskini_status():
    try:
        data = request.get_json()
        today = get_today()
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
        raw_data = res.json()

        print(f"[DEBUG] Tarikh: {tarikh} | Type: {type(raw_data)} | Raw data: {raw_data}")

        if not raw_data:
            print(f"[DEBUG] Tiada data untuk tarikh {tarikh}")
            return jsonify([])

        senarai = []

        # Handle jika Firebase return array (seperti [None, {data}])
        if isinstance(raw_data, list):
            for item in raw_data:
                if item is not None and isinstance(item, dict):
                    senarai.append(item)

        # Handle jika Firebase return object biasa ({"1": {data}})
        elif isinstance(raw_data, dict):
            for key, value in raw_data.items():
                if value is not None and isinstance(value, dict):
                    senarai.append(value)

        # Susun mengikut no_giliran
        senarai.sort(key=lambda x: int(x.get('no_giliran', 0)))

        print(f"[DEBUG] Berjaya ditukar ke array | Jumlah rekod: {len(senarai)}")

        return jsonify(senarai)

    except Exception as e:
        print(f"[ERROR] get_senarai_tarikh {tarikh}: {e}")
        return jsonify([])
		
# ==================== API UNTUK URUS CAROUSEL IKLan ====================

@app.route('/api/iklan_carousel', methods=['GET'])
def get_iklan_carousel():
    """Dapatkan semua slide iklan"""
    today = get_today()  # optional, kalau nak simpan iklan mengikut hari
    try:
        res = requests.get(f"{BASE_URL}/iklan_carousel.json")
        data = res.json()
        if not data:
            return jsonify([])
        
        # Tukar dari object Firebase ke list
        slides = []
        if isinstance(data, dict):
            for key, value in data.items():
                if value and isinstance(value, dict):
                    value['id'] = int(key) if key.isdigit() else key
                    slides.append(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if item:
                    item['id'] = i
                    slides.append(item)
        
        # Susun mengikut id
        slides.sort(key=lambda x: x.get('id', 0))
        return jsonify(slides)
    except Exception as e:
        print("Error get iklan_carousel:", e)
        return jsonify([]), 500


@app.route('/api/iklan_carousel', methods=['POST'])
def tambah_iklan_carousel():
    """Tambah slide baru"""
    try:
        data = request.get_json()
        title = data.get('title')
        color = data.get('color')
        content = data.get('content')

        if not title or not content:
            return jsonify({'success': False, 'message': 'Tajuk dan kandungan diperlukan'}), 400

        # Dapatkan senarai semasa
        res = requests.get(f"{BASE_URL}/iklan_carousel.json")
        existing = res.json() or {}
        
        # Cari ID baru (increment)
        new_id = max([int(k) for k in existing.keys()] or [0]) + 1

        requests.put(f"{BASE_URL}/iklan_carousel/{new_id}.json", json={
            'title': title,
            'color': color or 'text-primary',
            'content': content
        })

        return jsonify({'success': True, 'id': new_id})
    except Exception as e:
        print("Error tambah iklan:", e)
        return jsonify({'success': False, 'message': 'Ralat semasa menambah slide'}), 500


@app.route('/api/iklan_carousel/<int:slide_id>', methods=['PUT'])
def edit_iklan_carousel(slide_id):
    """Edit slide sedia ada"""
    try:
        data = request.get_json()
        requests.patch(f"{BASE_URL}/iklan_carousel/{slide_id}.json", json={
            'title': data.get('title'),
            'color': data.get('color'),
            'content': data.get('content')
        })
        return jsonify({'success': True})
    except Exception as e:
        print("Error edit iklan:", e)
        return jsonify({'success': False, 'message': 'Ralat semasa mengedit slide'}), 500


@app.route('/api/iklan_carousel/<int:slide_id>', methods=['DELETE'])
def padam_iklan_carousel(slide_id):
    """Padam slide"""
    try:
        requests.delete(f"{BASE_URL}/iklan_carousel/{slide_id}.json")
        return jsonify({'success': True})
    except Exception as e:
        print("Error padam iklan:", e)
        return jsonify({'success': False, 'message': 'Ralat semasa memadam slide'}), 500
		
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)