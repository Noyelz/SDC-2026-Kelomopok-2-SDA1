"""
SDC Dashboard — Database Initialization & Seed Script
Membuat database SQLite dan mengisi data 20 pegawai beserta
course catalog dan career paths.
"""

import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'sdc.db')


def get_db_path():
    return DB_PATH


def create_tables(conn):
    """Buat semua tabel yang dibutuhkan."""
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pegawai (
            id TEXT PRIMARY KEY,
            nama TEXT NOT NULL,
            jabatan TEXT NOT NULL,
            divisi TEXT NOT NULL,
            sertifikat TEXT NOT NULL,
            status TEXT NOT NULL,
            tanggal TEXT,
            pre_score INTEGER NOT NULL,
            post_score INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kinerja_periodik (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pegawai_id TEXT NOT NULL,
            q1_2024 REAL NOT NULL,
            q2_2024 REAL NOT NULL,
            q3_2024 REAL NOT NULL,
            q4_2024 REAL NOT NULL,
            q1_2025 REAL NOT NULL,
            q2_2025 REAL NOT NULL,
            FOREIGN KEY (pegawai_id) REFERENCES pegawai(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jabatan TEXT NOT NULL,
            title TEXT NOT NULL,
            provider TEXT NOT NULL,
            level TEXT NOT NULL,
            durasi TEXT NOT NULL,
            mode TEXT NOT NULL,
            tags TEXT NOT NULL,
            tipe TEXT NOT NULL,
            alasan TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS career_paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jabatan TEXT NOT NULL,
            tahap TEXT NOT NULL,
            target TEXT NOT NULL,
            program TEXT NOT NULL,
            durasi TEXT NOT NULL,
            prioritas TEXT NOT NULL
        )
    ''')

    conn.commit()


def seed_pegawai(conn):
    """Seed 20 data pegawai dan kinerja periodik."""
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute('SELECT COUNT(*) FROM pegawai')
    if cursor.fetchone()[0] > 0:
        print('Data pegawai sudah ada, skip seeding.')
        return

    pegawai_data = [
        # ── Akomodasi (7 orang) ──
        ('EMP001', 'Budi Santoso', 'Front Desk Officer', 'Akomodasi',
         'Sertifikat Kantor Depan', 'Aktif', '2025-03-15', 55, 82,
         [3.2, 3.4, 3.5, 4.0, 4.2, 4.3]),
        ('EMP002', 'Dewi Rahayu', 'Housekeeping Supervisor', 'Akomodasi',
         'Sertifikat Tata Graha', 'Aktif', '2025-01-20', 68, 91,
         [3.7, 3.8, 3.9, 4.5, 4.6, 4.7]),
        ('EMP003', 'Reza Firmansyah', 'Front Desk Officer', 'Akomodasi',
         'Sertifikat Kantor Depan', 'Belum', None, 48, 63,
         [2.9, 3.0, 3.0, 3.2, 3.1, 3.3]),
        ('EMP004', 'Sari Wulandari', 'Guest Relations Officer', 'Akomodasi',
         'Sertifikat GRO', 'Kadaluarsa', '2023-06-10', 70, 84,
         [3.9, 4.0, 4.0, 4.1, 3.9, 3.8]),
        ('EMP005', 'Hendri Kusuma', 'Concierge', 'Akomodasi',
         'Sertifikat Concierge', 'Aktif', '2025-04-02', 62, 87,
         [3.4, 3.5, 3.6, 4.2, 4.3, 4.4]),
        ('EMP006', 'Lestari Ningtyas', 'Housekeeping Attendant', 'Akomodasi',
         'Sertifikat Tata Graha', 'Aktif', '2025-02-10', 58, 79,
         [3.1, 3.2, 3.3, 3.8, 3.9, 4.0]),
        ('EMP007', 'Agus Prasetyo', 'Front Desk Officer', 'Akomodasi',
         'Sertifikat Kantor Depan', 'Belum', None, 44, 57,
         [2.7, 2.8, 2.7, 2.9, 2.8, 2.9]),

        # ── Food & Beverage (7 orang) ──
        ('EMP008', 'Ahmad Fauzi', 'F&B Attendant', 'F&B',
         'Sertifikat F&B Service', 'Aktif', '2025-02-28', 60, 85,
         [3.3, 3.4, 3.6, 4.1, 4.2, 4.3]),
        ('EMP009', 'Putri Maharani', 'F&B Attendant', 'F&B',
         'Sertifikat F&B Service', 'Aktif', '2025-02-28', 65, 88,
         [3.5, 3.6, 3.7, 4.3, 4.4, 4.5]),
        ('EMP010', 'Hendra Wijaya', 'F&B Attendant', 'F&B',
         'Sertifikat F&B Service', 'Belum', None, 43, 56,
         [2.6, 2.7, 2.6, 2.8, 2.7, 2.8]),
        ('EMP011', 'Yuni Astuti', 'Bartender', 'F&B',
         'Sertifikat Bartending', 'Aktif', '2025-03-05', 72, 93,
         [3.9, 4.0, 4.1, 4.6, 4.7, 4.8]),
        ('EMP012', 'Suryo Wibowo', 'Chef de Partie', 'F&B',
         'Sertifikat Culinary', 'Aktif', '2024-12-20', 74, 92,
         [4.0, 4.1, 4.2, 4.7, 4.8, 4.9]),
        ('EMP013', 'Mega Puspita', 'Barista', 'F&B',
         'Sertifikat Barista', 'Kadaluarsa', '2023-08-15', 51, 66,
         [3.0, 3.0, 3.1, 3.3, 3.2, 3.2]),
        ('EMP014', 'Danu Setiawan', 'F&B Supervisor', 'F&B',
         'Sertifikat F&B Service', 'Aktif', '2025-01-08', 66, 89,
         [3.6, 3.7, 3.8, 4.3, 4.4, 4.5]),

        # ── Tur & Perjalanan (6 orang) ──
        ('EMP015', 'Maya Kusuma', 'Tour Guide', 'Tur & Perjalanan',
         'Sertifikat Pemandu Wisata', 'Aktif', '2024-12-05', 73, 94,
         [3.9, 4.1, 4.2, 4.6, 4.7, 4.8]),
        ('EMP016', 'Dimas Prakoso', 'Travel Consultant', 'Tur & Perjalanan',
         'Sertifikat Agen Perjalanan', 'Aktif', '2025-01-15', 67, 88,
         [3.6, 3.7, 3.9, 4.3, 4.4, 4.5]),
        ('EMP017', 'Rina Agustina', 'Tour Guide', 'Tur & Perjalanan',
         'Sertifikat Pemandu Wisata', 'Kadaluarsa', '2022-11-20', 50, 65,
         [2.9, 3.0, 3.1, 3.3, 3.2, 3.3]),
        ('EMP018', 'Bayu Anggara', 'Tour Leader', 'Tur & Perjalanan',
         'Sertifikat Pemandu Wisata', 'Aktif', '2025-03-22', 64, 86,
         [3.5, 3.6, 3.7, 4.2, 4.3, 4.4]),
        ('EMP019', 'Nita Permata', 'Travel Consultant', 'Tur & Perjalanan',
         'Sertifikat Agen Perjalanan', 'Aktif', '2024-11-30', 69, 90,
         [3.7, 3.8, 3.9, 4.4, 4.5, 4.6]),
        ('EMP020', 'Fajar Nugroho', 'Tour Guide', 'Tur & Perjalanan',
         'Sertifikat Pemandu Wisata', 'Belum', None, 46, 60,
         [2.8, 2.9, 2.8, 3.0, 2.9, 3.0]),
    ]

    for p in pegawai_data:
        emp_id, nama, jabatan, divisi, sertifikat, status, tanggal, pre, post, kinerja = p
        cursor.execute('''
            INSERT INTO pegawai (id, nama, jabatan, divisi, sertifikat, status, tanggal, pre_score, post_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (emp_id, nama, jabatan, divisi, sertifikat, status, tanggal, pre, post))

        cursor.execute('''
            INSERT INTO kinerja_periodik (pegawai_id, q1_2024, q2_2024, q3_2024, q4_2024, q1_2025, q2_2025)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (emp_id, *kinerja))

    conn.commit()
    print(f'Seeded {len(pegawai_data)} pegawai.')


def seed_courses(conn):
    """Seed course catalog per jabatan."""
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM course_catalog')
    if cursor.fetchone()[0] > 0:
        print('Data course sudah ada, skip seeding.')
        return

    catalog = {
        'Front Desk Officer': [
            {'title': 'Certified Front Office Manager (CFOM)', 'provider': 'ASEAN Tourism Standard',
             'level': 'Lanjutan', 'durasi': '3 bulan', 'mode': 'Blended Learning',
             'tags': ['Reservasi', 'Check-in/out', 'Complaint Handling'], 'tipe': 'priority',
             'alasan': 'Nilai post-test Anda masih di bawah 80 — kursus ini menargetkan gap di area SOP check-in dan penanganan tamu VIP.'},
            {'title': 'Hospitality English for Front Desk', 'provider': 'BNSP / LPK Pariwisata',
             'level': 'Menengah', 'durasi': '6 minggu', 'mode': 'Online',
             'tags': ['Komunikasi', 'Bahasa Inggris', 'Guest Service'], 'tipe': 'recommended',
             'alasan': 'Kemampuan komunikasi multi-bahasa adalah kompetensi utama Front Desk Officer yang akan meningkatkan skor kinerja Anda.'},
            {'title': 'Revenue Management Dasar', 'provider': 'Perhimpunan Hotel Indonesia',
             'level': 'Dasar', 'durasi': '2 minggu', 'mode': 'Online',
             'tags': ['Pricing', 'Occupancy', 'Revenue'], 'tipe': 'optional',
             'alasan': 'Pemahaman revenue management membuka jalur karir ke posisi Front Office Supervisor.'},
        ],
        'Housekeeping Supervisor': [
            {'title': 'Certified Housekeeping Executive (CHE)', 'provider': 'ASEAN Tourism Standard',
             'level': 'Lanjutan', 'durasi': '2 bulan', 'mode': 'Blended',
             'tags': ['Manajemen Tim', 'Kualitas Kamar', 'Inventaris'], 'tipe': 'recommended',
             'alasan': 'Sebagai supervisor, sertifikasi CHE adalah validasi kompetensi manajerial yang akan memperkuat posisi Anda.'},
            {'title': 'Green Housekeeping & Sustainability', 'provider': 'BNSP Pariwisata',
             'level': 'Menengah', 'durasi': '3 minggu', 'mode': 'Online',
             'tags': ['Lingkungan', 'Efisiensi', 'Eco-Hotel'], 'tipe': 'recommended',
             'alasan': 'Tren industri hotel bintang 4-5 mengarah pada standar keberlanjutan — nilai tambah di pasar kerja.'},
        ],
        'Housekeeping Attendant': [
            {'title': 'Sertifikasi Tata Graha BNSP', 'provider': 'LSP Pariwisata / BNSP',
             'level': 'Dasar-Menengah', 'durasi': '1 bulan', 'mode': 'Tatap Muka',
             'tags': ['Pembersihan Kamar', 'Linen', 'Standar Hygiene'], 'tipe': 'priority',
             'alasan': 'Anda belum memiliki sertifikasi resmi. Sertifikasi BNSP adalah syarat wajib untuk kenaikan jenjang jabatan.'},
            {'title': 'Customer Service Excellence', 'provider': 'LPK Pariwisata Indonesia',
             'level': 'Dasar', 'durasi': '2 minggu', 'mode': 'Online',
             'tags': ['Pelayanan', 'Komunikasi', 'Etika'], 'tipe': 'recommended',
             'alasan': 'Kinerja layanan tamu Anda dapat ditingkatkan melalui kursus dasar ini.'},
        ],
        'Bartender': [
            {'title': 'Certified Bartender International (WSET Level 2)', 'provider': 'WSET School',
             'level': 'Lanjutan', 'durasi': '2 bulan', 'mode': 'Intensif',
             'tags': ['Mixology', 'Wine & Spirits', 'Service'], 'tipe': 'recommended',
             'alasan': 'WSET Level 2 adalah standar internasional yang diakui hotel bintang 5 — meningkatkan daya saing Anda secara signifikan.'},
            {'title': 'Flair Bartending & Mixology Kreatif', 'provider': 'Indonesian Bartenders Association',
             'level': 'Menengah', 'durasi': '1 bulan', 'mode': 'Tatap Muka',
             'tags': ['Flair', 'Kreativitas', 'Cocktail'], 'tipe': 'optional',
             'alasan': 'Diversifikasi skill dengan flair bartending membuka peluang di rooftop bar dan resort premium.'},
        ],
        'Chef de Partie': [
            {'title': 'Certified Culinary Professional (CCP)', 'provider': 'American Culinary Federation',
             'level': 'Lanjutan', 'durasi': '3 bulan', 'mode': 'Blended',
             'tags': ['Teknik Memasak', 'Menu Planning', 'HACCP'], 'tipe': 'recommended',
             'alasan': 'CCP adalah sertifikasi global yang memperkuat kredensial Anda di level chef senior.'},
            {'title': 'Food Safety & HACCP Management', 'provider': 'BNSP / Kemenkes',
             'level': 'Wajib', 'durasi': '2 minggu', 'mode': 'Online',
             'tags': ['Food Safety', 'Sanitasi', 'Regulasi'], 'tipe': 'priority',
             'alasan': 'Pembaruan sertifikasi HACCP adalah kewajiban regulasi — pastikan Anda selalu memiliki sertifikat yang valid.'},
        ],
        'Barista': [
            {'title': 'SCA Barista Skills (Foundation)', 'provider': 'Specialty Coffee Association',
             'level': 'Dasar', 'durasi': '1 bulan', 'mode': 'Tatap Muka',
             'tags': ['Espresso', 'Latte Art', 'Brewing'], 'tipe': 'priority',
             'alasan': 'Sertifikat SCA adalah standar industri kafe premium — dengan sertifikat ini Anda eligible untuk posisi Head Barista.'},
            {'title': 'Coffee Tasting & Sensory Skills', 'provider': 'Indonesian Specialty Coffee',
             'level': 'Menengah', 'durasi': '3 minggu', 'mode': 'Workshop',
             'tags': ['Cupping', 'Origin', 'Profile'], 'tipe': 'optional',
             'alasan': 'Menguasai sensory skills meningkatkan kemampuan rekomendasi kopi kepada pelanggan.'},
        ],
        'F&B Attendant': [
            {'title': 'Sertifikasi Pramusaji BNSP', 'provider': 'LSP Pariwisata / BNSP',
             'level': 'Dasar', 'durasi': '1 bulan', 'mode': 'Tatap Muka',
             'tags': ['Serving Technique', 'Menu Knowledge', 'Table Set'], 'tipe': 'priority',
             'alasan': 'Sertifikasi resmi BNSP adalah syarat wajib untuk naik ke posisi Senior Attendant atau Captain Waiter.'},
            {'title': 'Wine & Beverage Pairing Dasar', 'provider': 'Perhimpunan F&B Indonesia',
             'level': 'Dasar', 'durasi': '2 minggu', 'mode': 'Workshop',
             'tags': ['Wine', 'Beverage', 'Pairing'], 'tipe': 'recommended',
             'alasan': 'Pengetahuan minuman meningkatkan kemampuan upselling dan kepuasan tamu.'},
        ],
        'F&B Supervisor': [
            {'title': 'Certified Food & Beverage Manager (CFBM)', 'provider': 'ASEAN Tourism Standard',
             'level': 'Lanjutan', 'durasi': '2 bulan', 'mode': 'Blended',
             'tags': ['Manajemen Tim', 'Cost Control', 'SOP'], 'tipe': 'recommended',
             'alasan': 'Sebagai supervisor, CFBM memvalidasi kompetensi manajerial Anda secara regional.'},
            {'title': 'Service Excellence & Guest Experience', 'provider': 'LPK Hospitality Indonesia',
             'level': 'Menengah', 'durasi': '3 minggu', 'mode': 'Blended',
             'tags': ['Service Design', 'Guest Journey', 'Leadership'], 'tipe': 'optional',
             'alasan': 'Meningkatkan kemampuan desain pengalaman tamu dari perspektif supervisor.'},
        ],
        'Tour Guide': [
            {'title': 'Resertifikasi Pemandu Wisata BNSP', 'provider': 'LSP Pariwisata / BNSP',
             'level': 'Menengah', 'durasi': '2 minggu', 'mode': 'Tatap Muka',
             'tags': ['Guiding', 'Interpretasi', 'Regulasi'], 'tipe': 'priority',
             'alasan': 'Sertifikat Anda perlu diperbarui — resertifikasi adalah langkah prioritas pertama.'},
            {'title': 'Eco-Tourism & Sustainable Guiding', 'provider': 'Kemenpar / ASEAN',
             'level': 'Lanjutan', 'durasi': '1 bulan', 'mode': 'Blended',
             'tags': ['Eco-Tourism', 'Sustainability', 'Nature'], 'tipe': 'recommended',
             'alasan': 'Pariwisata berkelanjutan adalah tren global — kompetensi ini sangat dicari.'},
        ],
        'Travel Consultant': [
            {'title': 'Certified Travel Counsellor (CTC)', 'provider': 'ASEAN Tourism Standard',
             'level': 'Lanjutan', 'durasi': '2 bulan', 'mode': 'Blended',
             'tags': ['Konsultasi', 'Itinerary', 'Customer Service'], 'tipe': 'recommended',
             'alasan': 'CTC memvalidasi kemampuan konsultasi perjalanan Anda secara profesional.'},
            {'title': 'Digital Marketing for Travel', 'provider': 'LPK Pariwisata Digital',
             'level': 'Menengah', 'durasi': '3 minggu', 'mode': 'Online',
             'tags': ['Digital Marketing', 'Social Media', 'SEO'], 'tipe': 'optional',
             'alasan': 'Pemasaran digital menjadi kompetensi penting untuk travel consultant modern.'},
        ],
        'Tour Leader': [
            {'title': 'Certified Tour Leader (CTL)', 'provider': 'Kemenpar / ASEAN Tourism',
             'level': 'Lanjutan', 'durasi': '1.5 bulan', 'mode': 'Blended',
             'tags': ['Leadership', 'Crisis Management', 'Logistics'], 'tipe': 'recommended',
             'alasan': 'CTL memvalidasi kompetensi kepemimpinan tur dan manajemen logistik perjalanan.'},
            {'title': 'First Aid & Emergency Response', 'provider': 'Palang Merah Indonesia',
             'level': 'Wajib', 'durasi': '1 minggu', 'mode': 'Tatap Muka',
             'tags': ['First Aid', 'Emergency', 'Safety'], 'tipe': 'priority',
             'alasan': 'Sertifikat First Aid adalah kewajiban keselamatan untuk tour leader.'},
        ],
        'Guest Relations Officer': [
            {'title': 'Certified Guest Service Professional (CGSP)', 'provider': 'AHLA / ASEAN Tourism',
             'level': 'Lanjutan', 'durasi': '1.5 bulan', 'mode': 'Blended',
             'tags': ['Guest Experience', 'CRM', 'Complaint Resolution'], 'tipe': 'priority',
             'alasan': 'CGSP secara langsung meningkatkan skor NPS dan Guest Satisfaction Index — indikator utama kinerja GRO.'},
            {'title': 'Cross-Cultural Communication', 'provider': 'LPK Pariwisata Internasional',
             'level': 'Menengah', 'durasi': '3 minggu', 'mode': 'Online',
             'tags': ['Budaya', 'Komunikasi', 'Empati'], 'tipe': 'recommended',
             'alasan': 'Melayani tamu dari berbagai latar budaya adalah inti pekerjaan GRO.'},
        ],
        'Concierge': [
            {'title': "Certified Concierge (Les Clefs d'Or)", 'provider': "Union Internationale des Concierges d'Hotels",
             'level': 'Prestisius', 'durasi': 'Keanggotaan + Ujian', 'mode': 'Tatap Muka',
             'tags': ['Networking', 'Lokal Knowledge', 'VIP Service'], 'tipe': 'recommended',
             'alasan': "Keanggotaan Les Clefs d'Or adalah penghargaan tertinggi di profesi concierge."},
            {'title': 'Luxury Hospitality & VIP Protocol', 'provider': 'ASEAN Tourism Standard',
             'level': 'Lanjutan', 'durasi': '1 bulan', 'mode': 'Blended',
             'tags': ['VIP', 'Protokol', 'Luxury'], 'tipe': 'optional',
             'alasan': 'Penguasaan protokol VIP adalah nilai tambah utama Anda dibandingkan concierge di hotel lain.'},
        ],
    }

    count = 0
    for jabatan, courses in catalog.items():
        for c in courses:
            cursor.execute('''
                INSERT INTO course_catalog (jabatan, title, provider, level, durasi, mode, tags, tipe, alasan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (jabatan, c['title'], c['provider'], c['level'], c['durasi'], c['mode'],
                  json.dumps(c['tags']), c['tipe'], c['alasan']))
            count += 1

    conn.commit()
    print(f'Seeded {count} courses.')


def seed_career_paths(conn):
    """Seed career paths per jabatan."""
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM career_paths')
    if cursor.fetchone()[0] > 0:
        print('Data career paths sudah ada, skip seeding.')
        return

    paths = {
        'Front Desk Officer': [
            ('I', 'Penguasaan SOP Front Office Standar ASEAN', 'Pelatihan Internal + CFOM Modul 1', '1 bulan', 'Tinggi'),
            ('II', 'Sertifikasi Front Office BNSP', 'LSP Pariwisata Nasional', '2 bulan', 'Tinggi'),
            ('III', 'Kemampuan Revenue Management Dasar', 'PHI Online Course', '2 minggu', 'Sedang'),
            ('IV', 'Kenaikan ke Front Office Supervisor', 'On-the-job Training + CFOM Penuh', '6-12 bulan', 'Jangka Panjang'),
        ],
        'Tour Guide': [
            ('I', 'Resertifikasi Pemandu Wisata BNSP', 'LSP Pariwisata Nasional', '2 minggu', 'Urgent'),
            ('II', 'Lisensi Pemandu Alam (LNG)', 'Kemenpar + BNSP', '1 bulan', 'Tinggi'),
            ('III', 'Kemampuan Storytelling & Interpretasi', 'Indonesian Heritage Tourism', '2 minggu', 'Sedang'),
            ('IV', 'Sertifikasi Tour Leader Internasional', 'ASEAN Tourism CTM', '2 bulan', 'Jangka Panjang'),
        ],
        'F&B Attendant': [
            ('I', 'Sertifikasi Pramusaji BNSP', 'LSP Pariwisata / BNSP', '1 bulan', 'Urgent'),
            ('II', 'Pengetahuan Wine & Beverage Dasar', 'Perhimpunan F&B Indonesia', '2 minggu', 'Sedang'),
            ('III', 'Kenaikan ke Captain Waiter', 'On-the-job + Internal Training', '6 bulan', 'Sedang'),
            ('IV', 'Sertifikasi F&B Supervisor', 'ASEAN Tourism / CFBM', '2 bulan', 'Jangka Panjang'),
        ],
    }

    count = 0
    for jabatan, steps in paths.items():
        for step in steps:
            cursor.execute('''
                INSERT INTO career_paths (jabatan, tahap, target, program, durasi, prioritas)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (jabatan, *step))
            count += 1

    conn.commit()
    print(f'Seeded {count} career path steps.')


def init_db():
    """Initialize database: create tables and seed all data."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        create_tables(conn)
        seed_pegawai(conn)
        seed_courses(conn)
        seed_career_paths(conn)
        print(f'Database berhasil diinisialisasi di: {DB_PATH}')
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
