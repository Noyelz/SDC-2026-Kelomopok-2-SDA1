"""
SDC Dashboard — Database Initialization & Seed Script
Membuat database SQLite dan mengisi data pegawai, course catalog dari CSV file,
serta mengenerate user login untuk pegawai, manajer, dan admin.
"""

import sqlite3
import os
import csv
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'sdc.db')
PEGAWAI_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_pegawai.csv')
COURSE_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data_course.csv')

def get_db_path():
    return DB_PATH

def create_tables(conn):
    """Buat semua tabel yang dibutuhkan."""
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('DROP TABLE IF EXISTS pegawai')
    cursor.execute('DROP TABLE IF EXISTS course_catalog')
    cursor.execute('DROP TABLE IF EXISTS kinerja_periodik')
    cursor.execute('DROP TABLE IF EXISTS career_paths')

    cursor.execute('''
        CREATE TABLE pegawai (
            id_pegawai TEXT PRIMARY KEY,
            nama_pegawai TEXT NOT NULL,
            jabatan TEXT NOT NULL,
            divisi TEXT NOT NULL,
            status_sertifikat TEXT NOT NULL,
            pre_score INTEGER NOT NULL,
            post_score INTEGER NOT NULL,
            kinerja_q1_2024 REAL,
            kinerja_q2_2024 REAL,
            kinerja_q3_2024 REAL,
            kinerja_q4_2024 REAL,
            kinerja_q1_2025 REAL,
            kinerja_q2_2025 REAL,
            skill_komunikasi REAL,
            skill_layanan_tamu REAL,
            skill_penguasaan_teknis REAL,
            skill_kepatuhan_sop REAL,
            skill_kepemimpinan REAL,
            skill_bahasa_asing REAL,
            skill_problem_solving REAL,
            skill_digital_literacy REAL,
            label_rekomendasi INTEGER,
            label_rekomendasi_nama TEXT,
            label_tindakan INTEGER,
            label_tindakan_nama TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'pegawai',
            pegawai_id TEXT,
            nama TEXT NOT NULL,
            FOREIGN KEY (pegawai_id) REFERENCES pegawai(id_pegawai)
        )
    ''')

    cursor.execute('''
        CREATE TABLE course_catalog (
            id_course TEXT PRIMARY KEY,
            nama_course TEXT NOT NULL,
            provider TEXT,
            level TEXT,
            mode TEXT,
            durasi TEXT,
            label_kategori INTEGER,
            label_kategori_nama TEXT,
            skill_target_utama TEXT,
            min_skill_komunikasi REAL,
            min_skill_layanan_tamu REAL,
            min_skill_penguasaan_teknis REAL,
            min_skill_kepatuhan_sop REAL,
            min_skill_kepemimpinan REAL,
            min_skill_bahasa_asing REAL,
            min_skill_problem_solving REAL,
            min_skill_digital_literacy REAL,
            deskripsi TEXT
        )
    ''')

    conn.commit()

def generate_email(nama, existing_emails):
    """Generate email Kemenpar dari nama"""
    parts = nama.lower().split()
    if len(parts) >= 2:
        base_email = f"{parts[0]}.{parts[-1]}@kemenpar.go.id"
    else:
        base_email = f"{parts[0]}@kemenpar.go.id"
    
    # Handle duplicates
    email = base_email
    counter = 1
    while email in existing_emails:
        username, domain = base_email.split('@')
        email = f"{username}{counter}@{domain}"
        counter += 1
        
    existing_emails.add(email)
    return email

def seed_data(conn):
    """Seed data dari CSV dan generate users"""
    cursor = conn.cursor()
    
    existing_emails = set()
    pegawai_password = generate_password_hash("kemenpar123")
    admin_password = generate_password_hash("supadmingacor1")
    
    # 1. Seed Pegawai
    print("Seeding Pegawai...")
    with open(PEGAWAI_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute('''
                INSERT INTO pegawai (
                    id_pegawai, nama_pegawai, jabatan, divisi, status_sertifikat,
                    pre_score, post_score, kinerja_q1_2024, kinerja_q2_2024,
                    kinerja_q3_2024, kinerja_q4_2024, kinerja_q1_2025, kinerja_q2_2025,
                    skill_komunikasi, skill_layanan_tamu, skill_penguasaan_teknis,
                    skill_kepatuhan_sop, skill_kepemimpinan, skill_bahasa_asing,
                    skill_problem_solving, skill_digital_literacy, label_rekomendasi,
                    label_rekomendasi_nama, label_tindakan, label_tindakan_nama
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['id_pegawai'], row['nama_pegawai'], row['jabatan'], row['divisi'], row['status_sertifikat'],
                int(row['pre_score']), int(row['post_score']),
                float(row['kinerja_q1_2024']), float(row['kinerja_q2_2024']), float(row['kinerja_q3_2024']),
                float(row['kinerja_q4_2024']), float(row['kinerja_q1_2025']), float(row['kinerja_q2_2025']),
                float(row['skill_komunikasi']), float(row['skill_layanan_tamu']), float(row['skill_penguasaan_teknis']),
                float(row['skill_kepatuhan_sop']), float(row['skill_kepemimpinan']), float(row['skill_bahasa_asing']),
                float(row['skill_problem_solving']), float(row['skill_digital_literacy']),
                int(row['label_rekomendasi']), row['label_rekomendasi_nama'],
                int(row['label_tindakan']), row['label_tindakan_nama']
            ))
            
            # Generate user account for pegawai
            email = generate_email(row['nama_pegawai'], existing_emails)
            cursor.execute('''
                INSERT INTO users (email, password_hash, role, pegawai_id, nama)
                VALUES (?, ?, 'pegawai', ?, ?)
            ''', (email, pegawai_password, row['id_pegawai'], row['nama_pegawai']))

    # 2. Seed Manager
    print("Seeding Manager & Admin...")
    cursor.execute('''
        INSERT INTO users (email, password_hash, role, pegawai_id, nama)
        VALUES (?, ?, 'manager', NULL, ?)
    ''', ('ahmad.riyadi@kemenpar.go.id', pegawai_password, 'Ahmad Riyadi'))
    
    # 3. Seed SupAdmin
    cursor.execute('''
        INSERT INTO users (email, password_hash, role, pegawai_id, nama)
        VALUES (?, ?, 'supadmin', NULL, ?)
    ''', ('supadmin', admin_password, 'Super Admin'))

    # 4. Seed Course
    print("Seeding Courses...")
    with open(COURSE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute('''
                INSERT INTO course_catalog (
                    id_course, nama_course, provider, level, mode, durasi,
                    label_kategori, label_kategori_nama, skill_target_utama,
                    min_skill_komunikasi, min_skill_layanan_tamu, min_skill_penguasaan_teknis,
                    min_skill_kepatuhan_sop, min_skill_kepemimpinan, min_skill_bahasa_asing,
                    min_skill_problem_solving, min_skill_digital_literacy, deskripsi
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['id_course'], row['nama_course'], row['provider'], row['level'], row['mode'], row['durasi'],
                int(row['label_kategori']), row['label_kategori_nama'], row['skill_target_utama'],
                float(row['min_skill_komunikasi']), float(row['min_skill_layanan_tamu']), float(row['min_skill_penguasaan_teknis']),
                float(row['min_skill_kepatuhan_sop']), float(row['min_skill_kepemimpinan']), float(row['min_skill_bahasa_asing']),
                float(row['min_skill_problem_solving']), float(row['min_skill_digital_literacy']), row['deskripsi']
            ))

    conn.commit()

def reset_db():
    print("Mereset database dan membuat ulang dari CSV...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    try:
        create_tables(conn)
        seed_data(conn)
        print("Database berhasil diinisialisasi ulang!")
    except Exception as e:
        print(f"Error initializing DB: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    reset_db()
