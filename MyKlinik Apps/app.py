from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# Setup Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://myklinik-queue-line-system-default-rtdb.asia-southeast1.firebasedatabase.app'
})

@app.route('/')
def home():
    return render_template('daftar.html')

@app.route('/status_page')
def status_page():
    return render_template('status.html')

@app.route('/admin_page')
def admin_page():
    return render_template('admin.html')

# API: Ambil Nombor (Untuk daftar.html)
@app.route('/api/daftar', methods=['POST'])
def daftar_pesakit():
    nama = request.json.get('nama')
    ref_jumlah = db.reference('jumlah_giliran')
    no_baru = (ref_jumlah.get() or 0) + 1
    ref_jumlah.set(no_baru)
    
    db.reference(f'senarai_pesakit/{no_baru}').set({
        'nama': nama,
        'no_giliran': no_baru,
        'status': 'menunggu'
    })
    return jsonify({'no_giliran': no_baru, 'nama': nama})

# API: Panggil Seterusnya (Untuk admin.html)
@app.route('/api/next', methods=['POST'])
def panggil_next():
    ref_sekarang = db.reference('nombor_sekarang')
    no_skrg = (ref_sekarang.get() or 0) + 1
    ref_sekarang.set(no_skrg)
    return jsonify({'nombor_sekarang': no_skrg})

# API: Get Status Live (Untuk status.html)
@app.route('/api/status_live')
def status_live():
    no_sekarang = db.reference('nombor_sekarang').get() or 0
    return jsonify({'nombor_sekarang': no_sekarang})

if __name__ == '__main__':
    app.run(debug=True)
	