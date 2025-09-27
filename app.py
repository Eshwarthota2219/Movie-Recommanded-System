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
def download_file_from_drive(drive_url, filename):
    if not os.path.exists(filename):
        file_id = drive_url.split("/d/")[1].split("/")[0]
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
    # Download similarity.pkl from Google Drive
    download_file_from_drive(
        "https://drive.google.com/file/d/17tW5chin2O_3rBIi5d8uRIQlYxC7v0kf/view?usp=sharing",
        "similarity.pkl"
    )
    # Load movie_list.pkl (small, kept in repo)
    movies_dict = pickle.load(open('movie_list.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    return movies, similarity

movies, similarity = load_data()

# ----------------- Movie Selection -----------------
movie_list = movies['title'].values
selected_movie = st.selectbox("🔎 Search or select a movie", movie_list)

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
