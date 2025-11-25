import sqlite3
import hashlib

# --- ALGORITMA KEAMANAN ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# --- ALGORITMA DATABASE ---
def create_usertable():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, email TEXT, password TEXT)')
    conn.commit()
    conn.close()

def add_userdata(username, email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO userstable(username, email, password) VALUES (?,?,?)', (username, email, password))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username, password))
    data = c.fetchall()
    conn.close()
    return data

def view_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    conn.close()
    return data

# === TAMBAHAN BARU UNTUK ADMIN ===

# 1. Menghapus User berdasarkan Username
def delete_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('DELETE FROM userstable WHERE username="{}"'.format(username))
    conn.commit()
    conn.close()

# 2. Update Username & Email (Password tidak diubah demi keamanan)
def update_user_data(new_username, new_email, original_username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE userstable SET username=?, email=? WHERE username=?", (new_username, new_email, original_username))
    conn.commit()
    conn.close()