"""
SDC Dashboard — Flask Backend
REST API untuk dashboard monitoring & evaluasi sertifikasi tenaga kerja pariwisata.
"""

from flask import Flask, jsonify, request, render_template
import sqlite3
import json
import os

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'sdc.db')


# ══════════════════════════════════════════════════════
#  DATABASE HELPERS
# ══════════════════════════════════════════════════════

def get_db():
    """Get a database connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


def get_pegawai_with_kinerja(conn, pegawai_id=None, divisi=None):
    """Fetch pegawai joined with kinerja data, with optional filters."""
    query = '''
        SELECT p.id, p.nama, p.jabatan, p.divisi, p.sertifikat, p.status,
               p.tanggal, p.pre_score AS preScore, p.post_score AS postScore,
               k.q1_2024, k.q2_2024, k.q3_2024, k.q4_2024, k.q1_2025, k.q2_2025
        FROM pegawai p
        LEFT JOIN kinerja_periodik k ON p.id = k.pegawai_id
    '''
    conditions = []
    params = []

    if pegawai_id:
        conditions.append('p.id = ?')
        params.append(pegawai_id)
    if divisi and divisi != 'all':
        conditions.append('p.divisi = ?')
        params.append(divisi)

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' ORDER BY p.id'

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        d = dict(row)
        d['kinerja'] = [
            d.pop('q1_2024'), d.pop('q2_2024'), d.pop('q3_2024'),
            d.pop('q4_2024'), d.pop('q1_2025'), d.pop('q2_2025')
        ]
        result.append(d)

    return result


# ══════════════════════════════════════════════════════
#  BUSINESS LOGIC (ported from JavaScript)
# ══════════════════════════════════════════════════════

def avg(arr):
    """Calculate average of a list."""
    return sum(arr) / len(arr) if arr else 0


def get_flag(p):
    """Determine flag status for a pegawai."""
    kenaikan = p['postScore'] - p['preScore']
    kin_naik = avg(p['kinerja'][3:]) - avg(p['kinerja'][:3])
    if kenaikan >= 20 and kin_naik >= 0.4 and p['status'] == 'Aktif':
        return 'siap'
    if kenaikan < 15 or kin_naik < 0:
        return 'remedial'
    if abs(kin_naik) < 0.2:
        return 'stagnan'
    return 'monitor'


def get_rekomen(p):
    """Get recommendation based on flag."""
    flag = get_flag(p)
    if flag == 'siap':
        return 'Daftarkan ke LSP Pariwisata; kandidat sertifikasi lanjutan'
    if flag == 'remedial':
        return 'Ikutkan pelatihan ulang; jadwalkan bimbingan intensif'
    if flag == 'stagnan':
        return 'Evaluasi faktor eksternal; konsultasi dengan supervisor'
    return 'Pantau 1 kuartal ke depan; pertimbangkan coaching'


# ══════════════════════════════════════════════════════
#  ROUTES — Pages
# ══════════════════════════════════════════════════════

@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template('index.html')


# ══════════════════════════════════════════════════════
#  ROUTES — REST API
# ══════════════════════════════════════════════════════

@app.route('/api/pegawai')
def api_pegawai():
    """Get all pegawai with optional divisi filter."""
    divisi = request.args.get('divisi', 'all')
    conn = get_db()
    try:
        data = get_pegawai_with_kinerja(conn, divisi=divisi)
        return jsonify(data)
    finally:
        conn.close()


@app.route('/api/pegawai/<pegawai_id>')
def api_pegawai_detail(pegawai_id):
    """Get a single pegawai by ID."""
    conn = get_db()
    try:
        data = get_pegawai_with_kinerja(conn, pegawai_id=pegawai_id)
        if not data:
            return jsonify({'error': 'Pegawai tidak ditemukan'}), 404
        return jsonify(data[0])
    finally:
        conn.close()


@app.route('/api/kpi')
def api_kpi():
    """Get KPI summary data."""
    divisi = request.args.get('divisi', 'all')
    conn = get_db()
    try:
        pegawai = get_pegawai_with_kinerja(conn, divisi=divisi)
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
    finally:
        conn.close()


@app.route('/api/ranking')
def api_ranking():
    """Get top 5 / bottom 5 pegawai by post-training kinerja."""
    rank_type = request.args.get('type', 'top')
    divisi = request.args.get('divisi', 'all')
    conn = get_db()
    try:
        pegawai = get_pegawai_with_kinerja(conn, divisi=divisi)
        for p in pegawai:
            p['avgKin'] = round(avg(p['kinerja'][3:]), 2)

        pegawai.sort(key=lambda p: p['avgKin'], reverse=True)

        if rank_type == 'top':
            result = pegawai[:5]
        else:
            result = list(reversed(pegawai))[:5]

        return jsonify(result)
    finally:
        conn.close()


@app.route('/api/tren')
def api_tren():
    """Get tren kinerja per divisi."""
    divisi_filter = request.args.get('divisi', 'all')
    conn = get_db()
    try:
        pegawai = get_pegawai_with_kinerja(conn, divisi=divisi_filter)
        divisi_list = ['Akomodasi', 'F&B', 'Tur & Perjalanan']
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
    finally:
        conn.close()


@app.route('/api/interpretasi')
def api_interpretasi():
    """Get flagging & recommendation data."""
    divisi = request.args.get('divisi', 'all')
    conn = get_db()
    try:
        pegawai = get_pegawai_with_kinerja(conn, divisi=divisi)
        counts = {'siap': 0, 'remedial': 0, 'stagnan': 0, 'monitor': 0}
        details = []

        for p in pegawai:
            flag = get_flag(p)
            counts[flag] += 1
            kenaikan = p['postScore'] - p['preScore']
            kin_naik = avg(p['kinerja'][3:]) - avg(p['kinerja'][:3])
            tren = '↑ Membaik' if kin_naik >= 0.4 else ('↓ Menurun' if kin_naik < 0 else '→ Tidak banyak berubah')

            details.append({
                'nama': p['nama'],
                'jabatan': p['jabatan'],
                'divisi': p['divisi'],
                'kenaikan': kenaikan,
                'tren': tren,
                'flag': flag,
                'rekomen': get_rekomen(p)
            })

        return jsonify({'counts': counts, 'details': details})
    finally:
        conn.close()


@app.route('/api/courses/<jabatan>')
def api_courses(jabatan):
    """Get courses for a specific jabatan."""
    conn = get_db()
    try:
        cursor = conn.execute(
            'SELECT * FROM course_catalog WHERE jabatan = ? ORDER BY id',
            (jabatan,)
        )
        rows = cursor.fetchall()

        if not rows:
            # Fallback default course
            return jsonify([{
                'title': 'Pelatihan Kompetensi Dasar Pariwisata',
                'provider': 'BNSP / LSP Pariwisata',
                'level': 'Dasar',
                'durasi': '1 bulan',
                'mode': 'Tatap Muka',
                'tags': ['Layanan Tamu', 'Etika', 'SOP'],
                'tipe': 'recommended',
                'alasan': 'Tingkatkan kompetensi inti sesuai standar industri pariwisata Indonesia.'
            }])

        result = []
        for row in rows:
            d = dict(row)
            d['tags'] = json.loads(d['tags'])
            del d['id']
            del d['jabatan']
            result.append(d)
        return jsonify(result)
    finally:
        conn.close()


@app.route('/api/career-path/<jabatan>')
def api_career_path(jabatan):
    """Get career path for a specific jabatan."""
    conn = get_db()
    try:
        cursor = conn.execute(
            'SELECT tahap, target, program, durasi, prioritas FROM career_paths WHERE jabatan = ? ORDER BY id',
            (jabatan,)
        )
        rows = cursor.fetchall()

        if not rows:
            # Fallback default career path
            return jsonify([
                {'tahap': 'I', 'target': 'Sertifikasi Kompetensi BNSP sesuai jabatan',
                 'program': 'LSP Pariwisata Nasional', 'durasi': '1-2 bulan', 'prioritas': 'Tinggi'},
                {'tahap': 'II', 'target': 'Pelatihan Layanan Pelanggan Lanjutan',
                 'program': 'LPK Pariwisata Indonesia', 'durasi': '3 minggu', 'prioritas': 'Sedang'},
                {'tahap': 'III', 'target': 'Sertifikasi ASEAN Tourism Standard',
                 'program': 'ASEAN Tourism Forum', 'durasi': '2 bulan', 'prioritas': 'Sedang'},
                {'tahap': 'IV', 'target': 'Pengembangan Kompetensi Manajerial',
                 'program': 'Program Internal / Eksternal', 'durasi': '6-12 bulan', 'prioritas': 'Jangka Panjang'},
            ])

        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


# ══════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════

if __name__ == '__main__':
    # Auto-init database if it doesn't exist
    if not os.path.exists(DB_PATH):
        print('Database belum ada, menginisialisasi...')
        from database.init_db import init_db
        init_db()

    app.run(debug=True, port=5000)
