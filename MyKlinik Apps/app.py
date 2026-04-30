import requests
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "klinik_rahsia_123"

BASE_URL = "https://myklinik-queue-line-system-default-rtdb.asia-southeast1.firebasedatabase.app/"

def get_today():
    # Paksa timezone Malaysia (+8)
    now = datetime.utcnow() + timedelta(hours=8)
    return now.strftime('%Y-%m-%d')

def get_current_time():
    now = datetime.utcnow() + timedelta(hours=8)
    return now.strftime('%H:%M:%S')

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

        # Simpan pesakit dengan status menunggu_pengesahan (BELUM bagi nombor giliran)
        pesakit_data = {
            'nama': data.get('nama'),
            'no_ic': data.get('no_ic'),
            'no_hp': data.get('no_hp'),
            'whatsapp': data.get('whatsapp'),
            'status': 'menunggu_pengesahan',      # Status penting
            'masa': waktu,
            'tarikh_daftar': today
        }

        # Simpan menggunakan Firebase Push ID (lebih selamat & fleksibel)
        response = requests.post(
            f"{BASE_URL}/harian/{today}/senarai_pesakit.json", 
            json=pesakit_data
        )
        
        new_id = response.json().get('name')   # Ini adalah key unik dari Firebase

        if not new_id:
            return jsonify({'success': False, 'message': 'Gagal menyimpan data'}), 500

        # Pastikan jumlah_giliran dan nombor_sekarang ada
        res_jumlah = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        if res_jumlah.json() is None:
            requests.put(f"{BASE_URL}/harian/{today}/jumlah_giliran.json", json=0)

        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        if res_now.json() is None:
            requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)

        return jsonify({
            'success': True,
            'message': 'Pendaftaran berjaya. Sila tunggu pengesahan staff.',
            'id': new_id,           # ID penting untuk terimaPesakit
            'nama': data.get('nama')
        })

    except Exception as e:
        print("Error daftar:", e)
        return jsonify({'success': False, 'message': 'Ralat semasa mendaftar'}), 500

# ==================== TERIMA PESAKIT & KELUARKAN NO GILIRAN ====================
@app.route('/api/terima_pesakit', methods=['POST'])
def terima_pesakit():
    try:
        data = request.get_json()
        pesakit_id = data.get('id')

        if not pesakit_id:
            return jsonify({'success': False, 'message': 'ID pesakit diperlukan'}), 400

        today = get_today()

        # Ambil data pesakit menggunakan Firebase Push ID
        res = requests.get(f"{BASE_URL}/harian/{today}/senarai_pesakit/{pesakit_id}.json")
        pesakit = res.json()

        if not pesakit:
            return jsonify({'success': False, 'message': 'Pesakit tidak ditemui'}), 404

        if pesakit.get('status') != 'menunggu_pengesahan':
            return jsonify({'success': False, 'message': 'Pesakit sudah diproses atau status tidak betul'}), 400

        # Dapatkan nombor giliran baru
        res_jumlah = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        jumlah_giliran = (res_jumlah.json() or 0) + 1

        # Update jumlah giliran
        requests.put(f"{BASE_URL}/harian/{today}/jumlah_giliran.json", json=jumlah_giliran)

        # Kemaskini data pesakit
        pesakit['status'] = 'menunggu'
        pesakit['no_giliran'] = jumlah_giliran
        pesakit['masa_terima'] = get_current_time()

        # Simpan semula ke Firebase
        requests.put(f"{BASE_URL}/harian/{today}/senarai_pesakit/{pesakit_id}.json", json=pesakit)

        # Pastikan nombor sekarang ada
        if requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json").json() is None:
            requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)

        return jsonify({
            'success': True,
            'no_giliran': jumlah_giliran,
            'nama': pesakit.get('nama', '-')
        })

    except Exception as e:
        print("Error terima pesakit:", e)
        return jsonify({'success': False, 'message': 'Ralat dalaman server'}), 500
		
@app.route('/api/status_live')
def status_live():
    today = get_today()
    try:
        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        
        no_skrg = res_now.json() or 0
        total = res_total.json() or 0

        # Ambil nama pesakit semasa yang sedang dirawat atau menunggu
        nama_semasa = "-"
        if no_skrg > 0:
            res_pesakit = requests.get(f"{BASE_URL}/harian/{today}/senarai_pesakit.json")
            raw_data = res_pesakit.json() or {}

            senarai = []
            if isinstance(raw_data, dict):
                senarai = list(raw_data.values())
            elif isinstance(raw_data, list):
                senarai = raw_data

            for p in senarai:
                if p and p.get('no_giliran') == no_skrg:
                    nama_semasa = p.get('nama', '-')
                    break

        return jsonify({
            'nombor_sekarang': no_skrg,
            'jumlah_giliran': total,
            'nama_pesakit_semasa': nama_semasa
        })

    except Exception as e:
        print("Error status_live:", e)
        return jsonify({
            'nombor_sekarang': 0, 
            'jumlah_giliran': 0, 
            'nama_pesakit_semasa': '-'
        })


@app.route('/api/next', methods=['POST'])
def api_next():
    today = get_today()
    try:
        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        no_skrg = res_now.json() or 0

        # Ambil semua pesakit
        res = requests.get(f"{BASE_URL}/harian/{today}/senarai_pesakit.json")
        raw_data = res.json() or {}

        senarai = []
        if isinstance(raw_data, dict):
            for key, value in raw_data.items():
                if value and isinstance(value, dict):
                    value['firebase_id'] = key
                    senarai.append(value)
        elif isinstance(raw_data, list):
            senarai = [item for item in raw_data if item is not None]

        # Cari pesakit seterusnya yang status = 'menunggu'
        next_no = no_skrg + 1
        pesakit_next = None
        for p in senarai:
            if p.get('no_giliran') == next_no and p.get('status') in ['menunggu', 'menunggu_pengesahan']:
                pesakit_next = p
                break

        if not pesakit_next:
            return jsonify({'success': False, 'message': 'Tiada pesakit menunggu lagi.'})

        # Update nombor sekarang
        requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=next_no)

        # Update status pesakit
        firebase_id = pesakit_next.get('firebase_id')
        requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{firebase_id}.json", 
                      json={'status': 'sedang_dirawat'})

        print(f"[NEXT] Berjaya panggil nombor {next_no} - {pesakit_next.get('nama')}")

        return jsonify({
            'success': True,
            'nombor_sekarang': next_no,
            'nama': pesakit_next.get('nama', '-')
        })

    except Exception as e:
        print("Error next:", e)
        return jsonify({'success': False, 'message': 'Ralat memanggil nombor'}), 500


@app.route('/api/kemaskini_status', methods=['POST'])
def kemaskini_status():
    try:
        data = request.get_json()
        today = get_today()
        no_giliran = data.get('no_giliran')
        status_baru = data.get('status')

        if not no_giliran or not status_baru:
            return jsonify({'success': False, 'message': 'Data tidak lengkap'}), 400

        # Ambil semua pesakit
        res = requests.get(f"{BASE_URL}/harian/{today}/senarai_pesakit.json")
        raw_data = res.json() or {}

        updated = False

        if isinstance(raw_data, dict):
            for key, value in raw_data.items():
                if value and isinstance(value, dict) and value.get('no_giliran') == no_giliran:
                    requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{key}.json", 
                                  json={'status': status_baru})
                    updated = True
                    break

        if not updated:
            # Cuba cara lama (kalau masih guna key nombor)
            requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_giliran}.json", 
                          json={'status': status_baru})

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

        if isinstance(raw_data, dict):
            for key, value in raw_data.items():
                if value and isinstance(value, dict):
                    value['id'] = key
                    senarai.append(value)
        elif isinstance(raw_data, list):
            for item in raw_data:
                if item is not None and isinstance(item, dict):
                    senarai.append(item)

        # Susun mengikut no_giliran jika ada
        senarai.sort(key=lambda x: int(x.get('no_giliran', 0)))
        
        # TAMBAHAN BAIKI: Buat response + header anti-cache
        response = jsonify(senarai)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response  # <-- Guna yang ni je

    except Exception as e:
        print(f"[ERROR] get_senarai_tarikh {tarikh}: {e}")
        return jsonify([])
		
# ==================== API UNTUK URUS CAROUSEL IKLan (VERSI DIPERBAIKI) ====================

@app.route('/api/iklan_carousel', methods=['GET'])
def get_iklan_carousel():
    try:
        res = requests.get(f"{BASE_URL}/iklan_carousel.json")
        data = res.json()

        if not data:
            return jsonify([])

        slides = []
        if isinstance(data, dict):
            for key, value in data.items():
                if value and isinstance(value, dict):
                    value['id'] = key
                    slides.append(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if item and isinstance(item, dict):
                    item['id'] = str(i)
                    slides.append(item)

        slides.sort(key=lambda x: int(x.get('id', 0)))
        return jsonify(slides)

    except Exception as e:
        print("Error get iklan_carousel:", e)
        return jsonify([]), 500


@app.route('/api/iklan_carousel', methods=['POST'])
def tambah_iklan_carousel():
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        color = data.get('color', 'text-primary')
        content = data.get('content', '').strip()
        image_url = data.get('image_url', '').strip()
        video_url = data.get('video_url', '').strip()
        slide_type = data.get('type', 'text')
        duration = int(data.get('duration', 12)) # BARU: default 12s untuk teks/gambar

        if not title:
            return jsonify({'success': False, 'message': 'Tajuk diperlukan'}), 400

        res = requests.get(f"{BASE_URL}/iklan_carousel.json")
        existing = res.json() or {}

        if isinstance(existing, list):
            new_id = len(existing)
        else:
            new_id = max([int(k) for k in existing.keys() if str(k).isdigit()] or [0]) + 1

        new_slide = {
            'type': slide_type,
            'title': title,
            'color': color,
            'content': content,
            'image_url': image_url,
            'video_url': video_url,
            'duration': duration # BARU
        }

        requests.put(f"{BASE_URL}/iklan_carousel/{new_id}.json", json=new_slide)
        return jsonify({'success': True, 'id': new_id})

    except Exception as e:
        print("Error tambah iklan:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/iklan_carousel/<int:slide_id>', methods=['PUT'])
def edit_iklan_carousel(slide_id):
    try:
        data = request.get_json()
        requests.patch(f"{BASE_URL}/iklan_carousel/{slide_id}.json", json={
            'type': data.get('type'),
            'title': data.get('title'),
            'color': data.get('color'),
            'content': data.get('content'),
            'image_url': data.get('image_url'),
            'video_url': data.get('video_url'),
            'duration': int(data.get('duration', 12)) # BARU
        })
        return jsonify({'success': True})
    except Exception as e:
        print("Error edit iklan:", e)
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== ROUTE PENTING INI (UNTUK EDIT) ====================
@app.route('/api/iklan_carousel/<int:slide_id>', methods=['GET'])
def get_single_iklan(slide_id):
    """Dapatkan satu slide untuk fungsi Edit"""
    try:
        res = requests.get(f"{BASE_URL}/iklan_carousel/{slide_id}.json")
        slide = res.json()
        
        if not slide:
            return jsonify({'error': 'Slide tidak ditemui'}), 404
            
        slide['id'] = slide_id
        return jsonify(slide)
        
    except Exception as e:
        print("Error get single iklan:", e)
        return jsonify({'error': 'Gagal memuat slide'}), 500


@app.route('/api/iklan_carousel/<int:slide_id>', methods=['DELETE'])
def padam_iklan_carousel(slide_id):
    try:
        requests.delete(f"{BASE_URL}/iklan_carousel/{slide_id}.json")
        return jsonify({'success': True})
    except Exception as e:
        print("Error padam iklan:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== EXPORT LAPORAN ====================
@app.route('/api/export_excel/<tarikh>')
def export_excel(tarikh):
    try:
        res = requests.get(f"{BASE_URL}/harian/{tarikh}/senarai_pesakit.json")
        raw_data = res.json() or []
        
        senarai = []
        if isinstance(raw_data, list):
            senarai = [i for i in raw_data if i is not None]
        elif isinstance(raw_data, dict):
            senarai = [v for v in raw_data.values() if v is not None]
        
        if not senarai:
            return "Tiada data untuk tarikh ini", 404
        
        df = pd.DataFrame(senarai)
        df = df[['no_giliran', 'nama', 'no_ic', 'no_hp', 'masa', 'status']]
        df.columns = ['No Giliran', 'Nama Pesakit', 'No IC', 'No Telefon', 'Masa Daftar', 'Status']
        df.sort_values('No Giliran', inplace=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Laporan')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'Laporan_Klinik_{tarikh}.xlsx'
        )
    except Exception as e:
        print("Error export excel:", e)
        return "Ralat export Excel", 500

@app.route('/api/export_pdf/<tarikh>')
def export_pdf(tarikh):
    try:
        res = requests.get(f"{BASE_URL}/harian/{tarikh}/senarai_pesakit.json")
        raw_data = res.json() or []
        
        senarai = []
        if isinstance(raw_data, list):
            senarai = [i for i in raw_data if i is not None]
        elif isinstance(raw_data, dict):
            senarai = [v for v in raw_data.values() if v is not None]
        
        if not senarai:
            return "Tiada data untuk tarikh ini", 404
        
        senarai.sort(key=lambda x: int(x.get('no_giliran', 0)))
        
        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        
        # Header
        p.setFont("Helvetica-Bold", 18)
        p.drawString(2*cm, height - 2*cm, f"LAPORAN HARIAN KLINIK")
        p.setFont("Helvetica", 12)
        p.drawString(2*cm, height - 2.7*cm, f"Tarikh: {tarikh}")
        p.drawString(2*cm, height - 3.3*cm, f"Jumlah Pesakit: {len(senarai)}")
        
        # Table header
        y = height - 4.5*cm
        p.setFont("Helvetica-Bold", 9)
        p.drawString(2*cm, y, "No")
        p.drawString(3*cm, y, "Nama")
        p.drawString(8*cm, y, "No IC")
        p.drawString(11.5*cm, y, "Masa")
        p.drawString(13.5*cm, y, "Status")
        p.line(2*cm, y-0.2*cm, 19*cm, y-0.2*cm)
        
        # Table content
        p.setFont("Helvetica", 8)
        y -= 0.6*cm
        for pesakit in senarai:
            if y < 2*cm:  # New page
                p.showPage()
                y = height - 2*cm
                p.setFont("Helvetica", 8)
            
            p.drawString(2*cm, y, str(pesakit.get('no_giliran', '-')))
            p.drawString(3*cm, y, str(pesakit.get('nama', '-'))[:25])
            p.drawString(8*cm, y, str(pesakit.get('no_ic', '-')))
            p.drawString(11.5*cm, y, str(pesakit.get('masa', '-')))
            p.drawString(13.5*cm, y, str(pesakit.get('status', '-')).upper())
            y -= 0.5*cm
        
        p.save()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Laporan_Klinik_{tarikh}.pdf'
        )
    except Exception as e:
        print("Error export pdf:", e)
        return "Ralat export PDF", 500
		
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)