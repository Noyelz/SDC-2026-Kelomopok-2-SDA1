"""
SDC Dashboard — Flask Backend
REST API untuk dashboard monitoring & evaluasi sertifikasi tenaga kerja pariwisata.
"""

from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from werkzeug.security import check_password_hash
import sqlite3
import json
import os
import pickle
import pandas as pd
import numpy as np
from functools import wraps

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

app.secret_key = os.environ.get('SECRET_KEY', 'sdc_super_secret_key_2026')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'sdc.db')

# ══════════════════════════════════════════════════════
#  ML MODELS
# ══════════════════════════════════════════════════════
try:
    with open('sdc_model.pkl', 'rb') as f:
        course_model_artifacts = pickle.load(f)
    print("Course recommendation model loaded successfully.")
except Exception as e:
    print(f"Warning: Failed to load course model: {e}")
    course_model_artifacts = None

try:
    with open('sdc_model_tindakan.pkl', 'rb') as f:
        tindakan_model_artifacts = pickle.load(f)
    print("Manager action recommendation model loaded successfully.")
except Exception as e:
    print(f"Warning: Failed to load manager action model: {e}")
    tindakan_model_artifacts = None

# ══════════════════════════════════════════════════════
#  DATABASE HELPERS
# ══════════════════════════════════════════════════════
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') not in ['manager', 'supadmin']:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'supadmin':
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

def get_pegawai_with_kinerja(conn, pegawai_id=None, divisi=None):
    query = '''
        SELECT * FROM pegawai
    '''
    conditions = []
    params = []

    if pegawai_id:
        conditions.append('id_pegawai = ?')
        params.append(pegawai_id)
    if divisi and divisi != 'all':
        conditions.append('divisi = ?')
        params.append(divisi)

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' ORDER BY id_pegawai'
    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        d = dict(row)
        d['kinerja'] = [
            d.pop('kinerja_q1_2024'), d.pop('kinerja_q2_2024'), d.pop('kinerja_q3_2024'),
            d.pop('kinerja_q4_2024'), d.pop('kinerja_q1_2025'), d.pop('kinerja_q2_2025')
        ]
        # Map fields for backwards compatibility with JS if needed
        d['id'] = d['id_pegawai']
        d['nama'] = d['nama_pegawai']
        d['sertifikat'] = d['status_sertifikat']
        d['status'] = d['status_sertifikat'] # simplify
        d['preScore'] = d['pre_score']
        d['postScore'] = d['post_score']
        
        result.append(d)

    return result

def avg(arr):
    return sum(arr) / len(arr) if arr else 0

# ══════════════════════════════════════════════════════
#  ROUTES — Authentication
# ══════════════════════════════════════════════════════
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('index'))
        return render_template('login.html', admin_mode=False)
    
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Rate limit check can be added here
    
    conn = get_db()
    cursor = conn.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        if user['role'] == 'supadmin':
            return render_template('login.html', admin_mode=False, error='Admin tidak dapat login dari halaman ini.')
            
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['role'] = user['role']
        session['pegawai_id'] = user['pegawai_id']
        session['nama'] = user['nama']
        
        return redirect(url_for('index'))
    
    return render_template('login.html', admin_mode=False, error='Email atau password salah')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ══════════════════════════════════════════════════════
#  ROUTES — Pages
# ══════════════════════════════════════════════════════
@app.route('/')
@login_required
def index():
    return render_template('index.html', session=session)

@app.route('/supadmin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET':
        if session.get('role') == 'supadmin':
            return redirect(url_for('index'))
        return render_template('login.html', admin_mode=True)
        
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = get_db()
    cursor = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'supadmin'", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['role'] = user['role']
        session['pegawai_id'] = user['pegawai_id']
        session['nama'] = user['nama']
        return redirect(url_for('index'))
        
    return render_template('login.html', admin_mode=True, error='Kredensial admin salah')

# ══════════════════════════════════════════════════════
#  ROUTES — REST API
# ══════════════════════════════════════════════════════
@app.route('/api/me')
@login_required
def api_me():
    return jsonify({
        'id': session.get('user_id'),
        'email': session.get('email'),
        'role': session.get('role'),
        'pegawai_id': session.get('pegawai_id'),
        'nama': session.get('nama')
    })

@app.route('/api/pegawai')
@login_required
def api_pegawai():
    divisi = request.args.get('divisi', 'all')
    
    # Pegawai can only see their own data unless they are a manager/admin
    if session.get('role') == 'pegawai':
        pegawai_id = session.get('pegawai_id')
        conn = get_db()
        data = get_pegawai_with_kinerja(conn, pegawai_id=pegawai_id)
        conn.close()
        return jsonify(data)
        
    conn = get_db()
    data = get_pegawai_with_kinerja(conn, divisi=divisi)
    conn.close()
    return jsonify(data)

@app.route('/api/ml/recommend/<pegawai_id>')
@login_required
def api_ml_recommend(pegawai_id):
    if not course_model_artifacts:
        return jsonify({"error": "Model not loaded"}), 500
        
    # Check permissions
    if session.get('role') == 'pegawai' and session.get('pegawai_id') != pegawai_id:
        return jsonify({"error": "Unauthorized"}), 403
        
    conn = get_db()
    pegawai = get_pegawai_with_kinerja(conn, pegawai_id=pegawai_id)
    
    if not pegawai:
        conn.close()
        return jsonify({"error": "Not found"}), 404
        
    p = pegawai[0]
    
    # Fetch all courses
    cursor = conn.execute("SELECT * FROM course_catalog")
    courses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    df_course = pd.DataFrame(courses)
    
    # Extract features for model
    skill_dict = {
        "komunikasi": p['skill_komunikasi'],
        "layanan_tamu": p['skill_layanan_tamu'],
        "penguasaan_teknis": p['skill_penguasaan_teknis'],
        "kepatuhan_sop": p['skill_kepatuhan_sop'],
        "kepemimpinan": p['skill_kepemimpinan'],
        "bahasa_asing": p['skill_bahasa_asing'],
        "problem_solving": p['skill_problem_solving'],
        "digital_literacy": p['skill_digital_literacy']
    }
    
    model = course_model_artifacts["model"]
    preprocessor = course_model_artifacts["preprocessor"]
    skill_cols_ = course_model_artifacts["skill_cols"]
    feat_names_ = course_model_artifacts["feature_names"]
    
    row = {}
    for sc in skill_cols_:
        key = sc.replace("skill_", "")
        row[sc] = skill_dict.get(key, 3.0)

    row["pre_score"]   = p['pre_score']
    row["post_score"]  = p['post_score']
    row["delta_score"] = p['post_score'] - p['pre_score']

    q = p['kinerja']
    row["avg_kinerja_pre"]  = round(sum(q[:3]) / 3, 3)
    row["avg_kinerja_post"] = round(sum(q[3:]) / 3, 3)
    row["delta_kinerja"]    = round(row["avg_kinerja_post"] - row["avg_kinerja_pre"], 3)
    row["avg_skill"]        = round(sum(row[sc] for sc in skill_cols_) / len(skill_cols_), 3)

    row["divisi"]            = p['divisi']
    row["status_sertifikat"] = p['status_sertifikat']

    # Convert to dataframe
    X_input = pd.DataFrame([row])
    
    # Add missing columns if any based on feature names
    for col in feat_names_:
        if col not in X_input.columns:
            X_input[col] = 0
            
    X_input = X_input[feat_names_]
    X_proc  = preprocessor.transform(X_input)

    label_id = int(model.predict(X_proc)[0])
    proba = model.predict_proba(X_proc)[0]
    
    # Build response
    label_name = ["Komunikasi & Layanan", "Teknis & Kepatuhan SOP", "Kepemimpinan", "Sertifikasi Lanjutan & Pengembangan Karir"][label_id]
    confidence = round(proba[label_id] * 100, 1)
    
    # Get recommended courses
    df_rec = df_course[df_course["label_kategori"] == label_id].head(3)
    rec_courses = df_rec.to_dict('records')
    
    return jsonify({
        "label_id": label_id,
        "label_name": label_name,
        "confidence": confidence,
        "courses": rec_courses
    })

@app.route('/api/ml/tindakan/<pegawai_id>')
@manager_required
def api_ml_tindakan(pegawai_id):
    if not tindakan_model_artifacts:
        return jsonify({"error": "Model not loaded"}), 500
        
    conn = get_db()
    pegawai = get_pegawai_with_kinerja(conn, pegawai_id=pegawai_id)
    conn.close()
    
    if not pegawai:
        return jsonify({"error": "Not found"}), 404
        
    p = pegawai[0]
    
    skill_dict = {
        "komunikasi": p['skill_komunikasi'],
        "layanan_tamu": p['skill_layanan_tamu'],
        "penguasaan_teknis": p['skill_penguasaan_teknis'],
        "kepatuhan_sop": p['skill_kepatuhan_sop'],
        "kepemimpinan": p['skill_kepemimpinan'],
        "bahasa_asing": p['skill_bahasa_asing'],
        "problem_solving": p['skill_problem_solving'],
        "digital_literacy": p['skill_digital_literacy']
    }
    
    model = tindakan_model_artifacts["model"]
    prep = tindakan_model_artifacts["preprocessor"]
    skill_cols_ = tindakan_model_artifacts["skill_cols"]
    kinerja_cols_ = tindakan_model_artifacts["kinerja_cols"]
    feat_names_ = tindakan_model_artifacts["feature_names"]
    
    row = {}
    for sc in skill_cols_:
        row[sc] = skill_dict.get(sc.replace("skill_", ""), 3.0)
    for i, kc in enumerate(kinerja_cols_):
        row[kc] = p['kinerja'][i]

    row["pre_score"]   = p['pre_score']
    row["post_score"]  = p['post_score']
    row["delta_score"] = p['post_score'] - p['pre_score']

    avg_skill = float(np.mean([row[sc] for sc in skill_cols_]))
    row["avg_skill"] = round(avg_skill, 3)

    q = p['kinerja']
    avg_awal  = round(sum(q[:3]) / 3, 3)
    avg_akhir = round(sum(q[3:]) / 3, 3)
    delta_kin = round(avg_akhir - avg_awal, 3)
    row["avg_kinerja_awal"]  = avg_awal
    row["avg_kinerja_akhir"] = avg_akhir
    row["delta_kinerja"]     = delta_kin
    row["is_sudden_drop"]    = int(avg_awal >= 3.0 and delta_kin <= -0.20)

    row["divisi"]            = p['divisi']
    row["status_sertifikat"] = p['status_sertifikat']

    X_input = pd.DataFrame([row])
    
    for col in feat_names_:
        if col not in X_input.columns:
            X_input[col] = 0
            
    X_input = X_input[feat_names_]
    X_proc  = prep.transform(X_input)

    label_id = int(model.predict(X_proc)[0])
    proba = model.predict_proba(X_proc)[0]
    
    label_name = [
        "Coaching Intensif", 
        "Pengawasan & Evaluasi Ketat", 
        "Pertahankan & Stabilkan", 
        "Percepatan Karir", 
        "Retensi & Konseling (Sudden Drop)"
    ][label_id]
    
    confidence = round(proba[label_id] * 100, 1)
    
    return jsonify({
        "label_id": label_id,
        "label_name": label_name,
        "confidence": confidence
    })

@app.route('/api/kpi')
@manager_required
def api_kpi():
    divisi = request.args.get('divisi', 'all')
    conn = get_db()
    pegawai = get_pegawai_with_kinerja(conn, divisi=divisi)
    conn.close()
    
    total = len(pegawai)
    aktif = sum(1 for p in pegawai if p['status'] == 'Aktif')
    pct = round(aktif / total * 100) if total else 0
    rata_kenaikan = round(sum(p['postScore'] - p['preScore'] for p in pegawai) / total) if total else 0

    remedial = sum(1 for p in pegawai if (p['postScore'] - p['preScore']) < 15)
    stagnan = sum(1 for p in pegawai if abs(avg(p['kinerja'][3:]) - avg(p['kinerja'][:3])) < 0.2)

    return jsonify({
        'total': total,
        'aktif': aktif,
        'pct': pct,
        'rataKenaikan': rata_kenaikan,
        'flagged': remedial + stagnan,
        'remedial': remedial,
        'stagnan': stagnan
    })

@app.route('/api/ranking')
@manager_required
def api_ranking():
    rank_type = request.args.get('type', 'top')
    divisi = request.args.get('divisi', 'all')
    conn = get_db()
    pegawai = get_pegawai_with_kinerja(conn, divisi=divisi)
    conn.close()
    
    for p in pegawai:
        p['avgKin'] = round(avg(p['kinerja'][3:]), 2)

    pegawai.sort(key=lambda p: p['avgKin'], reverse=True)

    if rank_type == 'top':
        result = pegawai[:5]
    else:
        result = list(reversed(pegawai))[:5]

    return jsonify(result)

@app.route('/api/tren')
@login_required
def api_tren():
    divisi_filter = request.args.get('divisi', 'all')
    conn = get_db()
    pegawai = get_pegawai_with_kinerja(conn, divisi=divisi_filter)
    conn.close()
    
    divisi_list = ['Akomodasi', 'Food & Beverage', 'Tur & Perjalanan']
    result = {}

    for d in divisi_list:
        emps = [p for p in pegawai if p['divisi'] == d]
        if not emps:
            continue
        avg_kinerja = []
        for qi in range(6):
            avg_val = round(avg([p['kinerja'][qi] for p in emps]), 2)
            avg_kinerja.append(avg_val)
        result[d] = avg_kinerja

    return jsonify(result)

@app.route('/api/courses')
@login_required
def api_courses():
    conn = get_db()
    cursor = conn.execute('SELECT * FROM course_catalog ORDER BY id_course')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/interpretasi')
@manager_required
def api_interpretasi():
    divisi = request.args.get('divisi', 'all')
    conn = get_db()
    pegawai = get_pegawai_with_kinerja(conn, divisi=divisi)
    conn.close()
    
    # Using pre-calculated labels from the DB for the dashboard summary
    # label_tindakan: 0: Coaching Intensif, 1: Pengawasan, 2: Pertahankan, 3: Percepatan Karir, 4: Retensi
    counts = {'coaching': 0, 'pengawasan': 0, 'pertahankan': 0, 'percepatan': 0, 'retensi': 0}
    mapping = {0: 'coaching', 1: 'pengawasan', 2: 'pertahankan', 3: 'percepatan', 4: 'retensi'}
    
    details = []
    for p in pegawai:
        flag = mapping.get(p['label_tindakan'], 'pertahankan')
        counts[flag] += 1
        kenaikan = p['postScore'] - p['preScore']
        kin_naik = avg(p['kinerja'][3:]) - avg(p['kinerja'][:3])
        tren = '↑ Membaik' if kin_naik >= 0.4 else ('↓ Menurun' if kin_naik < 0 else '→ Tidak banyak berubah')

        details.append({
            'id': p['id_pegawai'],
            'nama': p['nama'],
            'jabatan': p['jabatan'],
            'divisi': p['divisi'],
            'kenaikan': kenaikan,
            'tren': tren,
            'flag': flag,
            'label_tindakan_nama': p['label_tindakan_nama'],
            'label_rekomendasi_nama': p['label_rekomendasi_nama']
        })

    return jsonify({'counts': counts, 'details': details})

# ══════════════════════════════════════════════════════
#  ROUTES — Admin API
# ══════════════════════════════════════════════════════
@app.route('/api/admin/users')
@admin_required
def api_admin_users():
    conn = get_db()
    cursor = conn.execute('SELECT id, email, role, nama, pegawai_id FROM users')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(users)

@app.route('/supadmin')
@admin_required
def supadmin():
    return render_template('admin.html')

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def api_admin_edit_role(user_id):
    data = request.json
    new_role = data.get('role')
    if new_role not in ['pegawai', 'manager', 'supadmin']:
        return jsonify({'error': 'Invalid role'}), 400
    
    conn = get_db()
    conn.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Role updated successfully'})

if __name__ == '__main__':
    # Auto-init database if it doesn't exist
    if not os.path.exists(DB_PATH):
        print('Database belum ada, menginisialisasi...')
        import subprocess
        subprocess.run(['python', 'database/init_db.py'])

    app.run(host='0.0.0.0', debug=True, port=5000)