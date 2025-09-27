import pickle
import pandas as pd
import streamlit as st
import requests
from requests.exceptions import RequestException
import time
import os

# ----------------- Streamlit Page Config -----------------
st.set_page_config(page_title="Movie Recommender 🎬", layout="wide")

# ----------------- Helper Functions -----------------
@st.cache_data
def fetch_poster(movie_id):
    try:
        api_key = st.secrets["TMDB_API_KEY"]
    except Exception:
        api_key = "5d6bc3cf1a64beb1639a7556871b64b3"

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"

    for attempt in range(3):
        try:
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get("poster_path")
            if poster_path:
                return "https://image.tmdb.org/t/p/w500/" + poster_path
            break
        except RequestException as e:
            print(f"⚠️ Attempt {attempt + 1} failed for movie_id {movie_id}: {e}")
            time.sleep(1)
            continue

    return "https://via.placeholder.com/500x750.png?text=No+Image"

def recommend(movie):
    match = movies[movies['title'].str.lower() == movie.lower()]
    if match.empty:
        return [], []

    index = match.index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)

    return recommended_movie_names, recommended_movie_posters

# ----------------- Download large file helper -----------------
def download_file_from_drive(file_id, filename):
    """Download file from Google Drive using direct link. Overwrites if exists."""
    if os.path.exists(filename):
        os.remove(filename)  # Remove invalid or old file
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    with st.spinner(f"Downloading {filename}..."):
        r = requests.get(download_url, stream=True)
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

# ----------------- Load Data -----------------
@st.cache_resource
def load_data():
    # Download similarity.pkl (large file) from Google Drive
    similarity_file_id = "17tW5chin2O_3rBIi5d8uRIQlYxC7v0kf"
    download_file_from_drive(similarity_file_id, "similarity.pkl")

    # Load movie_list.pkl (small, kept in repo)
    movies_dict = pickle.load(open('movie_list.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)

    similarity = pickle.load(open('similarity.pkl', 'rb'))
    return movies, similarity

movies, similarity = load_data()

# ----------------- Movie Selection -----------------
movie_list = movies['title'].values
selected_movie = st.selectbox("🔎 Search or select a movie", movie_list)

# ----------------- Custom CSS Styling -----------------
st.markdown("""
    <style>
        body {background-color: #0e0e0e; color: #f5f5f5;}
        .main-title {text-align: center; font-size: 50px; font-weight: bold; color: #e50914; margin-bottom: 10px;}
        .subtitle {text-align: center; font-size: 18px; color: #b3b3b3; margin-bottom: 40px;}
        .movie-card {background: #1c1c1c; border-radius: 15px; padding: 10px; transition: transform 0.3s ease, box-shadow 0.3s ease; box-shadow: 0px 4px 15px rgba(0,0,0,0.6);}
        .movie-card:hover {transform: scale(1.05); box-shadow: 0px 6px 20px rgba(229,9,20,0.7);}
        .movie-title {text-align: center; font-size: 16px; font-weight: bold; color: white; margin-top: 10px;}
    </style>
""", unsafe_allow_html=True)

# ----------------- Header -----------------
st.markdown("<h1 class='main-title'>🍿 Movie Recommender System</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Discover movies you'll love — powered by AI 🎥</p>", unsafe_allow_html=True)

# ----------------- Sidebar -----------------
st.sidebar.markdown("## ℹ️ About")
st.sidebar.write("This app recommends movies similar to the one you select. Built with **Machine Learning** and **Streamlit**.")
st.sidebar.write("🎯 Designed for a professional, Netflix-like experience.")
st.sidebar.markdown("## 📩 Contact")
st.sidebar.write("Created by: *Thota Eshwar*")
st.sidebar.write("Email: eshwarthota2211@gmail.com")
st.sidebar.write("[LinkedIn](www.linkedin.com/in/eshwar-thota-162a0832)")

# ----------------- Show Recommendations -----------------
if st.button('🚀 Show Recommendations'):
    with st.spinner("Fetching recommendations... 🍿"):
        recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

    if not recommended_movie_names:
        st.error(f"❌ Sorry, '{selected_movie}' not found.")
    else:
        cols = st.columns(min(5, len(recommended_movie_names)), gap="large")
        for col, name, poster in zip(cols, recommended_movie_names, recommended_movie_posters):
            with col:
                imdb_url = f"https://www.imdb.com/find?q={name.replace(' ', '+')}&ref_=nv_sr_sm"
                st.markdown(f"""
                    <a href="{imdb_url}" target="_blank" style="text-decoration:none;">
                        <div class="movie-card">
                            <img src="{poster}" style="width:100%; border-radius:10px;">
                            <p class="movie-title">{name}</p>
                        </div>
                    </a>
                """, unsafe_allow_html=True)
