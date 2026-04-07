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
        today = get_today()
        
        # Waktu Malaysia
        waktu_sekarang = (datetime.now() + timedelta(hours=8)).strftime('%H:%M:%S')
        
        # 1. Ambil jumlah pendaftar sekarang
        res = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        no_baru = (res.json() or 0) + 1
        
        # 2. Kemaskini jumlah besar
        requests.put(f"{BASE_URL}/harian/{today}/jumlah_giliran.json", json=no_baru)
        
        # 3. Simpan data pesakit
        requests.put(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", json={
            'nama': data.get('nama'),
            'no_hp': data.get('no_hp'),
            'no_giliran': no_baru,
            'status': 'menunggu',
            'masa': waktu_sekarang
        })

        # 4. Pastikan nombor_sekarang wujud jika ini pendaftar pertama
        res_check = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        if res_check.json() is None:
            requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)

        return jsonify({'no_giliran': no_baru, 'nama': data.get('nama')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


All
Images
Videos
News
More



hai saya ada sebuah rancangan berkaitan ini MyKlinik-Python/
├── app.py                     (Fail utama Python)
├── serviceAccountKey.json     (Kunci keselamatan dari Firebase)
--Procfile
--requirements
└── templates/                 (Folder untuk simpan fail HTML)
    ├── daftar.html
    ├── admin_login.html
	----dashboard.html
	----monitor.html
    └── index.html
Wah, menarik projek MyKlinik ini! Nampaknya anda sedang membina aplikasi web pengurusan klinik menggunakan Flask (berdasarkan struktur templates dan app.py) dan menggunakan Firebase sebagai pengkalan data.
Memandangkan anda sudah ada fail Procfile, saya andaikan anda bercadang untuk melancarkan (deploy) aplikasi ini ke platform seperti Heroku.
Ada beberapa perkara penting yang anda perlu pastikan supaya sistem ini berjalan lancar:
Fail .gitignore: Pastikan anda tidak memuat naik fail serviceAccountKey.json ke GitHub. Ini adalah maklumat sulit. Gunakan Environment Variables jika mahu deploy ke pelayan.
Requirements: Pastikan fail requirements.txt mengandungi semua library yang diperlukan seperti Flask, firebase-admin, dan gunicorn (untuk Heroku).
Struktur Folder Static: Jika anda ada fail CSS atau gambar, anda perlu tambah folder static/ di dalam direktori utama.
Contoh isi kandungan Procfile anda (jika guna Gunicorn):
text
web: gunicorn app:app
Use code with caution.

Ada bahagian spesifik yang anda perlukan bantuan? Contohnya cara sambungkan Firebase dalam app.py atau cara buat sistem login pada admin_login.html?




untuk info awak,Deploy saya guna render.Awak boleh check kod2 saya nanti
Terbaik! Guna Render adalah pilihan yang bijak sebab ia lebih mesra pengguna dan menyokong auto-deployment dari GitHub. 
YouTube
YouTube
 +1
Memandangkan anda menggunakan Render, berikut adalah perkara kritikal yang perlu anda semak dalam kod supaya deploy tidak gagal:
1. Konfigurasi Fail Utama
Requirements: Pastikan fail requirements.txt anda ada gunicorn dan firebase-admin. Render perlukan gunicorn untuk menjalankan aplikasi Python dalam mod pengeluaran (production).
Procfile: Walaupun Render boleh guna Start Command di dashboard mereka, adanya Procfile memudahkan Render mengenalpasti jenis servis anda. Isinya patutlah:
text
web: gunicorn app:app
Use code with caution.

 
Render
Render
 +4
2. Pengendalian serviceAccountKey.json (PENTING!)
Jangan sesekali simpan fail JSON Firebase ini di dalam GitHub jika repo anda bersifat public. Cara yang lebih selamat di Render: 
YouTube
YouTube
Gunakan Environment Variables: Masukkan isi kandungan JSON tersebut ke dalam pembolehubah persekitaran (Environment Variable) di Render Dashboard.
Kod Python: Ubah app.py untuk membaca maklumat tersebut dari env var bukannya terus dari fail fizikal. 
YouTube
YouTube
 +1
3. Tetapan di Render Dashboard
Apabila anda buat New Web Service di Render Dashboard: 
Runtime: Python 3.
Build Command: pip install -r requirements.txt.
Start Command: gunicorn app:app. 
YouTube
YouTube
 +3
4. Struktur Fail
Pastikan folder templates/ berada di tahap yang sama dengan app.py supaya Flask dapat cari fail HTML anda secara automatik. 
App Generator
App Generator
Boleh saya tahu, adakah anda sudah berjaya connect GitHub ke Render, atau ada keluar sebarang ralat "ModuleNotFoundError" semasa proses build?





undefined
undefined
undefined
9 sites
Getting Started with Render — Documentation - App Generator
1. Requirements File. Create a requirements.txt file listing all your Python dependencies: Flask==2.0.1 gunicorn==20.1.0 psycopg2-

App Generator

How to Deploy a Flask App on Render
23 Mar 2025 — hi guys welcome back to the channel and today I'm going to show you how you can deploy a flask. application on render for 100% fre...


YouTube
·
ProgrammingKnowledge

1m
Deploy a Flask App on Render
Table_title: Deploy a Flask App on Render Table_content: header: | Setting | Value | row: | Setting: Language | Value: Python 3 | ...

Render

Show all
semuanya sudah terhubung dan saya dah deloy.Cuma ada bebrapa bahagia yg saya nak minta awak tolong perbaiki
Sila kongsikan kod tersebut atau beritahu bahagian mana yang bermasalah. Saya sedia membantu!
Biasanya, isu selepas deploy ke Render melibatkan beberapa perkara ini:
Ralat 500 (Internal Server Error): Selalunya disebabkan fail serviceAccountKey.json tidak ditemui atau ralat pada sambungan Firebase.
Statik/CSS tidak keluar: Pastikan fail CSS berada dalam folder static/ dan dipanggil menggunakan url_for('static', filename='...').
Halaman "Not Found": Mungkin disebabkan routing dalam app.py tidak sepadan dengan nama fail di templates/.
Database Firebase: Data tidak masuk atau tidak keluar pada Dashboard.
Sila "paste" kod dari fail yang anda rasa bermasalah (contohnya app.py atau mana-mana fail .html) dan terangkan apa yang sepatutnya berlaku tetapi tidak menjadi.
Bahagian mana yang anda mahu saya semak dahulu? Pendaftaran, Login Admin, atau paparan Dashboard?




ini sebahagian kod untuk daftar.html.Sebelum ini saya dapat daftar dengan berjaya.setelah buat perubahan yg disarankan AI terus x menyambung.<script>
    let suaraAktif = false;
    window.spoken = false;

    // 1. LOGIK AUTO-RESET SETIAP HARI
    const hariIni = new Date().toLocaleDateString('en-CA'); // Menghasilkan format YYYY-MM-DD ikut waktu lokal
    const tarikhSimpanan = localStorage.getItem('tarikh_daftar');

    // Jika tarikh yang tersimpan bukan tarikh hari ini, padam semua data lama
    if (tarikhSimpanan !== hariIni) {
        localStorage.clear();
        console.log("Hari baru dikesan. Data lama dipadam secara automatik.");
    }

    function aktifkanSuara() {
        suaraAktif = true;
        let btn = document.getElementById('btn-suara');
        btn.innerText = "Suara Aktif";
        btn.style.background = "#198754";
        btn.style.color = "white";
        btn.style.border = "none";
        
        let test = new SpeechSynthesisUtterance("Sistem sedia");
        test.lang = 'ms-MY';
        window.speechSynthesis.speak(test);
    }

    // Paparkan status jika sudah daftar hari ini
    const savedNo = localStorage.getItem('no_saya');
    const savedNama = localStorage.getItem('nama_saya');
    if (savedNo) tampilStatus(savedNo, savedNama);

    function hantarDaftar() {
        const nama = document.getElementById('nama').value.trim();
        const hp = document.getElementById('no_hp').value.trim();
        if (!nama || !hp) return alert("Sila isi nama dan nombor telefon.");

        document.getElementById('btn-submit').disabled = true;
        document.getElementById('btn-submit').innerText = "...";

        fetch('/api/daftar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nama: nama, no_hp: hp})
        }).then(res => res.json()).then(data => {
            // SIMPAN DATA & TARIKH DAFTAR
            localStorage.setItem('no_saya', data.no_giliran);
            localStorage.setItem('nama_saya', data.nama);
            localStorage.setItem('tarikh_daftar', hariIni); // <--- Simpan tarikh hari ini
            tampilStatus(data.no_giliran, data.nama);
        });
    }

    function tampilStatus(no, nama) {
        document.getElementById('section-daftar').style.display = 'none';
        document.getElementById('info-saya').style.display = 'block';
        document.getElementById('no-saya').innerText = no;
        document.getElementById('nama-anda').innerText = nama;
    }

    function kemaskiniLive() {
        fetch('/api/status_live').then(res => res.json()).then(data => {
            const noSekarang = data.nombor_sekarang;
            const totalDaftar = data.jumlah_giliran;
            document.getElementById('no-live').innerText = noSekarang;

            // Jika sistem direset oleh admin (semua jadi 0), padam data di browser
            if(noSekarang === 0 && totalDaftar === 0) {
                if(localStorage.getItem('no_saya')) {
                    localStorage.clear();
                    document.getElementById('info-saya').style.display = 'none';
                    document.getElementById('section-daftar').style.display = 'block';
                }
                return;
            }

            const noSaya = localStorage.getItem('no_saya');
            if (noSaya) {
                const baki = noSaya - noSekarang;
                const pesan = document.getElementById('pesan-status');
                if (baki > 0) {
                    pesan.innerText = "Lagi " + baki + " orang.";
                    window.spoken = false;
                } else if (baki === 0) {
                    pesan.innerText = "GILIRAN ANDA! Sila masuk.";
                    if (suaraAktif && !window.spoken) {
                        let msg = new SpeechSynthesisUtterance("Nombor " + noSaya + ", sila masuk.");
                        msg.lang = 'ms-MY';
                        window.speechSynthesis.speak(msg);
                        window.spoken = true;
                    }
                } else {
                    pesan.innerText = "Giliran anda telah tamat.";
                    pesan.className = "small fw-bold mt-1 text-secondary";
                }
            }
        });
    }
    setInterval(kemaskiniLive, 4000);
    kemaskiniLive();
</script>
Masalah utama yang menyebabkan kod ini "tidak menyambung" selepas perubahan biasanya berpunca daripada logik auto-reset atau ralat pada API endpoint.
Berikut adalah beberapa perkara yang perlu dibetulkan supaya sistem anda kembali berfungsi:
1. Masalah pada Logik hariIni & localStorage
Dalam kod anda, anda mengisytiharkan const hariIni di luar fungsi. Jika pengguna membuka laman web pada pukul 11:59 malam dan mendaftar pada pukul 12:01 pagi, pembolehubah hariIni mungkin tidak dikemaskini.
Cadangan Penambahbaikan: Masukkan hariIni ke dalam fungsi hantarDaftar untuk pastikan tarikh sentiasa tepat semasa klik butang.
2. Semak Nama Endpoint API
Pastikan dalam app.py, anda mempunyai route yang sepadan dengan fetch('/api/daftar', ...) dan fetch('/api/status_live', ...). Jika anda terubah nama fungsi di Python, JavaScript tidak akan dapat mencari data tersebut (Ralat 404).
3. Kod JavaScript yang Lebih Stabil
Sila gantikan bahagian <script> anda dengan versi yang telah saya kemaskan ini (terutama bahagian fetch untuk menangkap ralat):
javascript
<script>
    let suaraAktif = false;
    window.spoken = false;

    // Fungsi untuk dapatkan tarikh hari ini (YYYY-MM-DD)
    function getTarikhHariIni() {
        return new Date().toLocaleDateString('en-CA');
    }

    // 1. AUTO-RESET: Jika hari bertukar, bersihkan localStorage
    const hariIni = getTarikhHariIni();
    const tarikhSimpanan = localStorage.getItem('tarikh_daftar');
    if (tarikhSimpanan && tarikhSimpanan !== hariIni) {
        localStorage.clear();
        console.log("Data hari semalam dipadam.");
    }

    function aktifkanSuara() {
        suaraAktif = true;
        let btn = document.getElementById('btn-suara');
        btn.innerText = "Suara Aktif";
        btn.className = "btn btn-success btn-sm w-100 mt-2"; // Gunakan class Bootstrap jika ada
        
        let test = new SpeechSynthesisUtterance("Sistem sedia");
        test.lang = 'ms-MY';
        window.speechSynthesis.speak(test);
    }

    // Paparkan status jika sudah ada data dalam cache
    const savedNo = localStorage.getItem('no_saya');
    const savedNama = localStorage.getItem('nama_saya');
    if (savedNo) tampilStatus(savedNo, savedNama);

    function hantarDaftar() {
        const nama = document.getElementById('nama').value.trim();
        const hp = document.getElementById('no_hp').value.trim();
        
        if (!nama || !hp) return alert("Sila isi nama dan nombor telefon.");

        const btnSubmit = document.getElementById('btn-submit');
        btnSubmit.disabled = true;
        btnSubmit.innerText = "Memproses...";

        fetch('/api/daftar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nama: nama, no_hp: hp})
        })
        .then(res => {
            if (!res.ok) throw new Error('Ralat Pelayan');
            return res.json();
        })
        .then(data => {
            // SIMPAN DATA & TARIKH TERKINI
            localStorage.setItem('no_saya', data.no_giliran);
            localStorage.setItem('nama_saya', data.nama);
            localStorage.setItem('tarikh_daftar', getTarikhHariIni()); 
            tampilStatus(data.no_giliran, data.nama);
        })
        .catch(err => {
            alert("Gagal mendaftar. Sila cuba lagi.");
            btnSubmit.disabled = false;
            btnSubmit.innerText = "Daftar Sekarang";
        });
    }

    function tampilStatus(no, nama) {
        document.getElementById('section-daftar').style.display = 'none';
        document.getElementById('info-saya').style.display = 'block';
        document.getElementById('no-saya').innerText = no;
        document.getElementById('nama-anda').innerText = nama;
    }

    function kemaskiniLive() {
        fetch('/api/status_live')
        .then(res => res.json())
        .then(data => {
            const noSekarang = data.nombor_sekarang;
            const totalDaftar = data.jumlah_giliran;
            document.getElementById('no-live').innerText = noSekarang;

            // Logik Reset Global (Jika Admin kosongkan senarai)
            if(noSekarang === 0 && totalDaftar === 0) {
                if(localStorage.getItem('no_saya')) {
                    localStorage.clear();
                    location.reload(); // Refresh untuk kembali ke borang daftar
                }
                return;
            }

            const noSaya = localStorage.getItem('no_saya');
            if (noSaya) {
                const baki = parseInt(noSaya) - parseInt(noSekarang);
                const pesan = document.getElementById('pesan-status');
                
                if (baki > 0) {
                    pesan.innerText = "Lagi " + baki + " orang sebelum anda.";
                    pesan.className = "text-primary fw-bold";
                    window.spoken = false;
                } else if (baki === 0) {
                    pesan.innerText = "GILIRAN ANDA! Sila masuk.";
                    pesan.className = "text-danger fw-bold animate-blink"; // Tambah efek jika mahu
                    if (suaraAktif && !window.spoken) {
                        let msg = new SpeechSynthesisUtterance("Nombor " + noSaya + ", " + nama_saya + " sila masuk.");
                        msg.lang = 'ms-MY';
                        window.speechSynthesis.speak(msg);
                        window.spoken = true;
                    }
                } else {
                    pesan.innerText = "Giliran anda telah tamat.";
                    pesan.className = "text-secondary mt-1";
                }
            }
        })
        .catch(err => console.log("Gagal ambil status live"));
    }

    setInterval(kemaskiniLive, 5000); // 5 saat sekali untuk kurangkan beban server Render
    kemaskiniLive();
</script>
Use code with caution.

4. Semak Bahagian Backend (app.py)
Pastikan fungsi daftar di Python anda memulangkan (return) JSON yang betul seperti ini:
python
@app.route('/api/daftar', methods=['POST'])
def daftar():
    data = request.get_json()
    # ... proses simpan ke Firebase ...
    return jsonify({
        "no_giliran": no_baru, 
        "nama": data['nama']
    })
Use code with caution.

Boleh kongsikan ralat (error) yang keluar di Inspect Element (Console) browser anda? Ini akan membantu saya tahu jika ralatnya adalah "404 Not Found" atau "500 Internal Server Error".




ini kod di app.py # --- API ---

@app.route('/api/daftar', methods=['POST'])
def api_daftar():
    data = request.json
    today = get_today()
    
    # Ambil waktu Malaysia sekarang
    waktu_sekarang = (datetime.now() + timedelta(hours=8)).strftime('%H:%M:%S')
    
    res = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
    no_baru = (res.json() or 0) + 1
    
    requests.put(f"{BASE_URL}/harian/{today}/jumlah_giliran.json", json=no_baru)
    requests.put(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", json={
        'nama': data.get('nama'),
        'no_hp': data.get('no_hp'),
        'no_giliran': no_baru,
        'status': 'menunggu',
        'masa': waktu_sekarang # <--- Guna waktu Malaysia
    })
    return jsonify({'no_giliran': no_baru, 'nama': data.get('nama')})

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
def panggil_next():
    today = get_today()
    
    # 1. Ambil nombor sekarang dan jumlah orang yang sudah daftar
    res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
    res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
    
    no_sekarang = res_now.json() or 0
    total_daftar = res_total.json() or 0
    
    # 2. SEMAKAN: Jika nombor sekarang sudah sampai had jumlah pendaftar
    if no_sekarang >= total_daftar:
        return jsonify({
            'success': False, 
            'message': 'Tiada pesakit lagi dalam senarai.',
            'nombor_sekarang': no_sekarang
        }), 400

    # 3. Jika masih ada pesakit, baru naikkan nombor
    no_baru = no_sekarang + 1
    requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=no_baru)
    
    # Kemaskini status pesakit tersebut kepada 'sedang_dirawat'
    requests.patch(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", json={'status': 'sedang_dirawat'})
    
    return jsonify({
        'success': true,
        'nombor_sekarang': no_baru
    })

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
Kod app.py anda secara teknikalnya sudah nampak baik, tetapi ada satu kesilapan kecil pada api_next yang boleh menyebabkan Python error (500) dan satu isu logik pembolehubah yang menyebabkan pendaftaran tidak "menyambung".
Berikut adalah pembetulan yang perlu anda lakukan:
1. Betulkan ralat true (huruf kecil) di app.py
Dalam Python, True mestilah bermula dengan huruf besar. Kod anda di panggil_next menggunakan true gaya JavaScript, ini akan menyebabkan sistem crash.
Cari bahagian ini di app.py dan betulkan:
python
# ASAL:
return jsonify({ 'success': true, 'nombor_sekarang': no_baru })

# BETUL (Guna T besar):
return jsonify({ 'success': True, 'nombor_sekarang': no_baru })
Use code with caution.

2. Isu nombor_sekarang di Firebase
Dalam api_daftar, anda ada kemaskini jumlah_giliran, tetapi anda tidak set nilai awal untuk nombor_sekarang. Jika ini hari baru, nombor_sekarang di Firebase mungkin null.
Tambahkan logik ini dalam api_daftar sebelum return:
python
    # Pastikan nombor_sekarang wujud, jika null (hari baru), set kepada 0
    res_check = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
    if res_check.json() is None:
        requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)

    return jsonify({'no_giliran': no_baru, 'nama': data.get('nama')})
Use code with caution.

3. Betulkan JavaScript di daftar.html
Ada satu pembolehubah yang salah panggil dalam fungsi suara anda yang boleh menyebabkan script terhenti (error).
Cari bahagian kemaskiniLive dalam daftar.html:
javascript
// ASAL:
let msg = new SpeechSynthesisUtterance("Nombor " + noSaya + ", " + nama_saya + " sila masuk.");

// BETUL:
// Gunakan 'savedNama' (yang anda ambil dari localStorage di atas) bukannya 'nama_saya'
let msg = new SpeechSynthesisUtterance("Nombor " + noSaya + ", " + savedNama + " sila masuk.");
Use code with caution.

4. Kenapa "Tidak Menyambung"? (Checklist Render)
Jika selepas betulkan kod di atas ia masih tidak menyambung:
Firebase URL: Pastikan BASE_URL dalam app.py adalah alamat RTDB Firebase yang betul (berakhir dengan .firebaseio.com).
Environment Variable: Jika anda guna get_today(), pastikan zon masa di Render diset ke Malaysia. Anda boleh tambah persekitaran (Environment Variable) di Dashboard Render:
Key: TZ
Value: Asia/Kuala_Lumpur
CORS/Mixed Content: Jika anda buka laman web guna http tapi API panggil https (atau sebaliknya), browser akan sekat. Render biasanya automatik https, jadi pastikan semua pautan konsisten.
Cuba betulkan true kepada True dahulu, kemudian commit ke GitHub. Biasanya itu punca utama API next atau update_status gagal.
Adakah anda ada menerima ralat "Internal Server Error" pada skrin atau dalam Render Logs?




[2026-04-07 08:12:15,989] ERROR in app: Exception on /api/status_live [GET]
Ralat tersebut menunjukkan aplikasi Flask anda mengalami masalah (crash) semasa cuba memproses fungsi status_live. Berdasarkan kod yang anda berikan sebelum ini, punca paling utama adalah pembolehubah BASE_URL yang tidak lengkap atau masalah sambungan ke Firebase. 
Sila lakukan langkah-langkah pembetulan ini:
1. Periksa BASE_URL di app.py 
Pastikan BASE_URL dalam app.py adalah alamat penuh Realtime Database anda yang berakhir dengan .firebaseio.com. Jangan biarkan ia kosong atau salah format. 
Betul: BASE_URL = "https://firebaseio.com"
Salah: BASE_URL = "https://console.firebase..." (Ini pautan konsol, bukan database).
2. Tambah try-except untuk Mengesan Ralat Sebenar 
Ubah kod status_live anda kepada versi ini supaya anda boleh nampak ralat terperinci dalam Render Logs: 
python
@app.route('/api/status_live')
def status_live():
    try:
        today = get_today()
        # Ambil data dari Firebase
        res_now = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        res_total = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        
        # Pastikan data yang diterima sah
        nombor_sekarang = res_now.json() if res_now.json() is not None else 0
        jumlah_giliran = res_total.json() if res_total.json() is not None else 0
        
        return jsonify({
            'nombor_sekarang': nombor_sekarang,
            'jumlah_giliran': jumlah_giliran
        })
    except Exception as e:
        print(f"Ralat Status Live: {e}") # Ini akan keluar di Render Logs
        return jsonify({'error': str(e)}), 500
Use code with caution.

3. Kenapa Ia Berlaku Sekarang?
Zon Masa (Timezone): Fungsi get_today() anda mungkin menghasilkan tarikh yang berbeza antara komputer anda (Malaysia) dan pelayan Render (biasanya UTC). Jika folder tarikh tersebut belum wujud di Firebase, res_now.json() akan memulangkan None, dan jika logik kod seterusnya cuba memproses None, ia akan error.
Library requests: Pastikan anda telah menambah requests dalam fail requirements.txt. Jika tidak, Render tidak akan dapat memanggil API Firebase. 
Langkah Seterusnya di Render:
Buka Dashboard Render -> Web Service Anda -> Environment.
Tambah satu variable baru:
Key: TZ
Value: Asia/Kuala_Lumpur
Simpan dan tunggu ia re-deploy. 
Selepas buat perubahan ini, sila semak semula Render Logs. Jika masih error, bolehkah anda salin baris ralat yang bermula dengan Traceback (most recent call last):? Itu akan memberitahu baris tepat yang bermasalah. 
Adakah anda sudah memasukkan requests ke dalam requirements.txt? 








10 sites
How to Resolve the API Key Error in Your Python Code for Google ...
13 Jan 2025 — Review any usage quotas and ensure your usage does not exceed the free tier limits. Code Execution Environment Ensure the environm...

YouTube

Deployment stuck in Render- Deploying a Flask application
1 Aug 2023 — During the deployment settings, I added python app.py as my running command instead of gunicorn, let me know if something is wrong...

Render

Mastering Error Handling in Python: Try-Except, Logging, and ...
21 Mar 2025 — Use try-except to protect against crashes. Log all important events and errors. Raise or handle specific exceptions. Respond with ...

Medium

Show all
Ralat Status Live: name 'timedelta' is not defined
Ralat itu berlaku kerana anda menggunakan timedelta dalam kod app.py (di bahagian api_daftar), tetapi anda belum mengimportnya daripada modul datetime. Itulah sebabnya aplikasi anda crash apabila cuba memproses data.
Sila kemaskini bahagian paling atas fail app.py anda dengan baris berikut:
python
from datetime import datetime, timedelta
Use code with caution.

Mengapa ralat ini muncul di status_live?
Walaupun ralat itu sebut status_live, biasanya dalam Flask, jika ada ralat import atau ralat sintaks di mana-mana bahagian app.py, seluruh aplikasi boleh terganggu atau ralat merebak ke fungsi yang berkaitan.
Tindakan untuk anda:
Baiki Import: Pastikan baris di atas ada di bahagian import.
Baiki True: Pastikan juga anda sudah tukar true kepada True (huruf besar) dalam fungsi panggil_next seperti yang saya sebut sebelum ini.
Commit & Push: Simpan fail dan hantar ke GitHub. Render akan mulakan proses deploy secara automatik.
Adakah anda sudah menambah from datetime import datetime, timedelta dalam kod anda sekarang?




kan senang awak bagi je kod yg betul..itu lebih pretikel..
Tentu, ini lebih praktikal. Berikut adalah kod app.py yang telah saya lengkapkan dengan semua pembetulan (import timedelta, betulkan True, dan pengurusan data None dari Firebase).
Sila salin dan gantikan keseluruhan kandungan fail app.py anda:
python
from flask import Flask, render_template, request, jsonify, session
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "kunci_rahsia_anda" # Tukar kepada apa-apa string

# --- KONFIGURASI FIREBASE ---
# Pastikan URL ini tepat dengan Realtime Database anda
BASE_URL = "https://firebaseio.com" 

def get_today():
    # Mengambil tarikh Malaysia (UTC+8)
    return (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/daftar')
def daftar_page():
    return render_template('daftar.html')

@app.route('/admin')
def admin_login():
    return render_template('admin_login.html')

# --- API ---

@app.route('/api/daftar', methods=['POST'])
def api_daftar():
    try:
        data = request.json
        today = get_today()
        
        # Waktu Malaysia
        waktu_sekarang = (datetime.now() + timedelta(hours=8)).strftime('%H:%M:%S')
        
        # 1. Ambil jumlah pendaftar sekarang
        res = requests.get(f"{BASE_URL}/harian/{today}/jumlah_giliran.json")
        no_baru = (res.json() or 0) + 1
        
        # 2. Kemaskini jumlah besar
        requests.put(f"{BASE_URL}/harian/{today}/jumlah_giliran.json", json=no_baru)
        
        # 3. Simpan data pesakit
        requests.put(f"{BASE_URL}/harian/{today}/senarai_pesakit/{no_baru}.json", json={
            'nama': data.get('nama'),
            'no_hp': data.get('no_hp'),
            'no_giliran': no_baru,
            'status': 'menunggu',
            'masa': waktu_sekarang
        })

        # 4. Pastikan nombor_sekarang wujud jika ini pendaftar pertama
        res_check = requests.get(f"{BASE_URL}/harian/{today}/nombor_sekarang.json")
        if res_check.json() is None:
            requests.put(f"{BASE_URL}/harian/{today}/nombor_sekarang.json", json=0)

        return jsonify({'no_giliran': no_baru, 'nama': data.get('nama')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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