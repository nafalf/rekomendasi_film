import streamlit as st
import pandas as pd
import requests
from functools import lru_cache
import numpy as np
import time
import auth       # Backend Database
import admin      # Halaman Admin

# Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Movie Recommender System")

# --- SESSION STATE MANAGEMENT ---
# Mengatur status login dan navigasi halaman
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'page' not in st.session_state:
    st.session_state['page'] = 'login' # Default halaman awal adalah login

# ==========================================
# 1. HALAMAN REGISTER
# ==========================================
def register_page():
    st.title("📝 Register New Account")
    
    # Form Input
    new_user = st.text_input("Username")
    new_email = st.text_input("Email Address")
    new_password = st.text_input("Password", type='password')
    
    # Tambahan info helper agar user tahu syaratnya
    st.caption("Syarat: Email harus @gmail.com dan Password minimal 8 karakter.")

    if st.button("Create Account"):
        # 1. Cek jika ada kolom kosong
        if not new_user or not new_email or not new_password:
            st.warning("Mohon isi semua kolom!")
            
        # 2. Cek Validasi Email (Harus ada @gmail.com)
        elif "@gmail.com" not in new_email:
            st.error("Email tidak valid! Wajib menggunakan domain @gmail.com")
            
        # 3. Cek Panjang Password (Minimal 8)
        elif len(new_password) < 8:
            st.error("Password terlalu pendek! Minimal harus 8 huruf/karakter.")
            
        # 4. Jika semua syarat terpenuhi, baru simpan ke Database
        else:
            try:
                auth.create_usertable() # Pastikan tabel ada
                hashed_pass = auth.make_hashes(new_password) # Enkripsi password
                auth.add_userdata(new_user, new_email, hashed_pass) # Simpan ke DB
                st.success("Akun berhasil dibuat! Silakan Login.")
            except Exception as e:
                st.error(f"Gagal membuat akun: {e}")

    # Sidebar Navigasi
    with st.sidebar:
        st.title("Navigasi")
        st.info("Sudah punya akun?")
        if st.button("Go to Login"):
            st.session_state['page'] = 'login'
            st.rerun()

# ==========================================
# 2. HALAMAN LOGIN
# ==========================================
def login_page():
    st.title("🔑 Login System")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        hashed_pswd = auth.make_hashes(password)
        result = auth.login_user(username, hashed_pswd)

        if result:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success(f"Selamat datang {username}!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Username atau Password salah.")

    # Sidebar Navigasi
    with st.sidebar:
        st.title("Navigasi")
        st.info("Belum punya akun?")
        if st.button("Go to Register"):
            st.session_state['page'] = 'register'
            st.rerun()

# ==========================================
# 3. APLIKASI MOVIE (User Biasa)
# ==========================================
def movie_app():
    # --- Sidebar Logout ---
    with st.sidebar:
        st.title(f"👤 {st.session_state['username']}")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ''
            st.rerun()
    
    # --- KODE ASLI MOVIE RECOMMENDATION ANDA ---
    # (Copy Paste kode UI Movie Anda di sini tanpa mengubah logika UI-nya)
    
    st.markdown("""
        <style>
        a { color: #FF6347 !important; text-decoration: none !important; font-weight: bold; }
        a:hover { color: #FFA07A !important; text-decoration: underline !important; }
        </style>
        """, unsafe_allow_html=True)

    # Load data
    @st.cache_resource
    def load_data():
        with open('movielist.pkl', 'rb') as file:
            movies = pd.read_pickle(file)
        with open('cosine_sim1.pkl', 'rb') as file:
            sim1 = pd.read_pickle(file)
        with open('cosine_sim2.pkl', 'rb') as file:
            sim2 = pd.read_pickle(file)
        with open('cosine_sim3.pkl', 'rb') as file:
            sim3 = pd.read_pickle(file)
        similarity = np.concatenate((sim1, sim2, sim3), axis=0)
        return movies, similarity

    movies, similarity = load_data()

    @lru_cache(maxsize=1000)
    def fetch_movie_details(movie_id):
        try:
            api_key = st.secrets["tmdb_api_key"]
            response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}')
            response.raise_for_status()
            data = response.json()
            return {
                'poster_url': f'https://image.tmdb.org/t/p/w500{data["poster_path"]}',
                'imdb_id': data['imdb_id'],
                'release_year': data['release_date'][:4],
                'genres': ', '.join([genre['name'] for genre in data['genres']])
            }
        except Exception:
            return None

    def recommend(movie):
        try:
            index = movies[movies['title'] == movie].index[0]
            distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
            recommended_movies = []
            for i in distances[1:9]:
                movie_id = movies.iloc[i[0]]['movie_id']
                details = fetch_movie_details(movie_id)
                if details:
                    recommended_movies.append({
                        'title': movies.iloc[i[0]]['title'],
                        'poster': details['poster_url'],
                        'imdb_id': details['imdb_id'],
                        'year': details['release_year'],
                        'genres': details['genres']
                    })
            return recommended_movies
        except IndexError:
            return []

    # UI Utama
    st.title('🎬 Movie Recommender System')

    movie_list = movies['title'].values
    selected = st.selectbox('Select or type a movie to get recommendations', movie_list)

    if selected:
        with st.spinner('Fetching recommendations...'):
            selected_movie_id = movies[movies['title'] == selected]['movie_id'].values[0]
            selected_movie_details = fetch_movie_details(selected_movie_id)
            recommendations = recommend(selected)
        
        if selected_movie_details:
            st.subheader(f'Selected Movie: [{selected}](https://www.imdb.com/title/{selected_movie_details["imdb_id"]})')
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(selected_movie_details['poster_url'], use_container_width=True)
            with col2:
                st.write(f"**Release Year:** {selected_movie_details['release_year']}")
                st.write(f"**Genres:** {selected_movie_details['genres']}")
        
        if recommendations:
            st.subheader('Recommended Movies')
            cols = st.columns(4)
            for i, movie in enumerate(recommendations):
                with cols[i % 4]:
                    st.markdown(f"##### [{movie['title']} ({movie['year']})](https://www.imdb.com/title/{movie['imdb_id']})")
                    st.markdown(f"[![Poster]({movie['poster']})](https://www.imdb.com/title/{movie['imdb_id']})")
                    st.caption(f"Genres: {movie['genres']}")
    
    st.markdown("---")
    st.markdown("Data provided by TMDb")

# ==========================================
# MAIN CONTROLLER (LOGIKA PERPINDAHAN HALAMAN)
# ==========================================
if __name__ == '__main__':
    # Pastikan tabel DB dibuat saat pertama run
    auth.create_usertable()

    # Cek apakah sudah login
    if st.session_state['logged_in']:
        # Jika login sebagai admin -> Buka halaman Admin
        if st.session_state['username'] == 'admin':
            admin.show_admin_page()
        # Jika login sebagai user biasa -> Buka App Film
        else:
            movie_app()
    else:
        # Jika belum login, cek mau ke Login atau Register
        if st.session_state['page'] == 'register':
            register_page()
        else:
            login_page()