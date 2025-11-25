import pickle
import streamlit as st
import pandas as pd
import requests
from functools import lru_cache
import numpy as np
import time  # Library untuk menghitung waktu eksekusi (Algoritma)

st.set_page_config(layout="wide", page_title="Movie Recommender System")

# Custom CSS
st.markdown("""
    <style>
    a {
        color: #FF6347 !important;
        text-decoration: none !important;
        font-weight: bold;
    }
    a:hover {
        color: #FFA07A !important;
        text-decoration: underline !important;
    }
    /* Style untuk box skor */
    .metric-box {
        padding: 10px;
        background-color: #f0f2f6;
        border-radius: 5px;
        margin-bottom: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 1. Load Data (Menggunakan Cache agar cepat)
@st.cache_resource
def load_data():
    with open('movielist.pkl', 'rb') as file:
        movies = pd.read_pickle(file)
    # Memuat cosine similarity yang dipecah
    with open('cosine_sim1.pkl', 'rb') as file:
        sim1 = pd.read_pickle(file)
    with open('cosine_sim2.pkl', 'rb') as file:
        sim2 = pd.read_pickle(file)
    with open('cosine_sim3.pkl', 'rb') as file:
        sim3 = pd.read_pickle(file)
    
    # Menggabungkan kembali (Merge Algorithm)
    similarity = np.concatenate((sim1, sim2, sim3), axis=0)
    return movies, similarity

movies, similarity = load_data()

# 2. Fetch API Data (Dengan Caching LRU)
@lru_cache(maxsize=1000)
def fetch_movie_details(movie_id):
    try:
        # Mengambil API Key dari secrets.toml
        api_key = st.secrets["tmdb_api_key"]
        response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}')
        response.raise_for_status()
        data = response.json()
        
        # Validasi data tahun
        release_date = data.get('release_date', '')
        year = release_date[:4] if release_date else '0'
        
        genres = data.get('genres', [])
        genre_str = ', '.join([g['name'] for g in genres]) if genres else 'Unknown'

        return {
            'poster_url': f'https://image.tmdb.org/t/p/w500{data.get("poster_path", "")}',
            'imdb_id': data.get('imdb_id', ''),
            'release_year': year,
            'genres': genre_str
        }
    except Exception as e:
        # Jangan print error di UI agar tetap bersih, cukup return None
        return None

# 3. Core Algorithm: Recommendation with Filtering
def recommend(movie, start_year, end_year):
    try:
        # A. Searching Algorithm (Mencari Index)
        index = movies[movies['title'] == movie].index[0]
        
        # B. Calculation (Mengambil vektor jarak)
        # enumerate menambah index, list mengubah jadi list of tuple
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        
        recommended_movies = []
        
        # C. Iteration & Filtering Logic
        # Kita scan 50 film teratas (Search Space Expansion) 
        # karena mungkin top 8 tidak masuk kriteria tahun.
        for i in distances[1:51]: 
            # Early Exit: Jika sudah dapat 8 rekomendasi, berhenti.
            if len(recommended_movies) >= 8:
                break
                
            movie_id = movies.iloc[i[0]]['movie_id']
            score = i[1] # Similarity Score
            
            # Fetch details untuk cek tahun
            details = fetch_movie_details(movie_id)
            
            if details:
                try:
                    movie_year = int(details['release_year'])
                except:
                    movie_year = 0
                
                # FILTER: Cek apakah tahun masuk rentang (Conditional Logic)
                if start_year <= movie_year <= end_year:
                    recommended_movies.append({
                        'title': movies.iloc[i[0]]['title'],
                        'poster': details['poster_url'],
                        'imdb_id': details['imdb_id'],
                        'year': details['release_year'],
                        'genres': details['genres'],
                        'score': score # Masukkan skor untuk ditampilkan
                    })
                    
        return recommended_movies
    except IndexError:
        return []

# --- UI SECTION ---

# Sidebar Options
with st.sidebar:
    st.header("⚙️ Algorithm Settings")
    st.write("Filter results to test the search algorithm:")
    
    # Slider Filter Tahun
    start_year, end_year = st.slider(
        "Release Year Range",
        min_value=1980,
        max_value=2025,
        value=(2000, 2025)
    )
    
    st.info(f"Searching movies between: **{start_year} - {end_year}**")

# Main Content
st.title('🎬 Movie Recommender System')
st.caption("Enhanced with Content-Based Filtering & Search Optimization")

# Bagian Penjelasan Algoritma (Untuk Nilai Plus Dosen)
with st.expander("ℹ️ How the Algorithm Works (Math & Logic)"):
    st.markdown("""
    **1. Vectorization (TF-IDF):** Mengubah teks (genre, cast, crew) menjadi vektor numerik.
    **2. Cosine Similarity:** Menghitung sudut antar vektor untuk menentukan kemiripan.
    """)
    st.latex(r'''
        \text{similarity} = \cos(\theta) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}
    ''')
    st.markdown("""
    **3. Filtering Logic:** Menggunakan *Sequential Search* pada hasil sorting untuk memfilter berdasarkan Tahun Rilis.
    """)

# Input User
movie_list = movies['title'].values
selected = st.selectbox('Select or type a movie to get recommendations:', movie_list)

# Tombol Rekomendasi
if st.button('Show Recommendations'):
    
    # Mulai hitung waktu (Time Complexity Analysis)
    start_time = time.time()
    
    # Proses Utama
    selected_movie_id = movies[movies['title'] == selected]['movie_id'].values[0]
    selected_movie_details = fetch_movie_details(selected_movie_id)
    recommendations = recommend(selected, start_year, end_year)
    
    # Selesai hitung waktu
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Tampilkan Detail Film Pilihan
    if selected_movie_details:
        st.write("---")
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(selected_movie_details['poster_url'], use_column_width=True)
        with col2:
            st.subheader(f"{selected} ({selected_movie_details['release_year']})")
            st.write(f"**Genres:** {selected_movie_details['genres']}")
            st.write(f"**Overview:** [Read on IMDB](https://www.imdb.com/title/{selected_movie_details['imdb_id']})")
            
            # Tampilkan waktu eksekusi algoritma
            st.success(f"⚡ Algorithm Execution Time: **{execution_time:.4f} seconds**")
            st.caption(f"Searching through {len(movies)} movies database.")

    # Tampilkan Hasil Rekomendasi
    if recommendations:
        st.subheader('🎯 Top Recommendations')
        cols = st.columns(4)
        for i, movie in enumerate(recommendations):
            with cols[i % 4]:
                st.markdown(f"**{movie['title']}**")
                st.image(movie['poster'], use_column_width=True)
                
                # Menampilkan Similarity Score
                st.progress(float(movie['score']))
                st.caption(f"Match: {movie['score']*100:.1f}% | Year: {movie['year']}")
                
                st.markdown(f"[View on IMDB](https://www.imdb.com/title/{movie['imdb_id']})")
    else:
        st.warning(f"No movies found similar to '{selected}' in the year range {start_year}-{end_year}. Try widening the filter.")

# Footer
st.markdown("---")
st.markdown("Data provided by [The Movie Database (TMDb)](https://www.themoviedb.org) | Built with Streamlit")