import pickle
import streamlit as st
import pandas as pd
import requests
import os
import time
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Hybrid Movie Recommender", layout="wide")
st.title("🎬 Hybrid Movie Recommender System")

# -----------------------------
# Custom CSS (UI Enhancement)
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}

h1 {
    text-align: center;
    font-weight: 800;
}

.movie-card {
    background: rgba(255,255,255,0.08);
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 25px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.4);
    transition: transform 0.3s ease;
}

.movie-card:hover {
    transform: scale(1.02);
}

.movie-title {
    font-size: 22px;
    font-weight: bold;
    color: #ffcc70;
}

.genre-badge {
    display: inline-block;
    background: #ff6f61;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    margin: 4px 6px 4px 0;
}

.rating {
    font-size: 18px;
    color: #ffd700;
    font-weight: bold;
}

.overview {
    font-size: 14px;
    line-height: 1.6;
    color: #e0e0e0;
}

.stButton > button {
    background: linear-gradient(90deg, #ff512f, #dd2476);
    color: white;
    border-radius: 25px;
    padding: 10px 25px;
    font-weight: bold;
    border: none;
}

.stButton > button:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Load data
# -----------------------------
movies_dict = pickle.load(open("movie_dict.pkl", "rb"))
movies = pd.DataFrame(movies_dict)

content_similarity = pickle.load(open("similarity.pkl", "rb"))

# -----------------------------
# Load or initialize ratings
# -----------------------------
if os.path.exists("ratings.pkl"):
    ratings = pickle.load(open("ratings.pkl", "rb"))
else:
    ratings = {}

# -----------------------------
# TMDB API Key
# -----------------------------
TMDB_API_KEY = "9578fe9fcfa44dcafb9cd5ba675ec208"

# -----------------------------
# Session state
# -----------------------------
if "recs" not in st.session_state:
    st.session_state.recs = []
if "recs_type" not in st.session_state:
    st.session_state.recs_type = ""

# -----------------------------
# Fetch movie details
# -----------------------------
@st.cache_data(ttl=3600)
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{int(movie_id)}"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}

    poster = "https://via.placeholder.com/500x750?text=No+Poster"
    genres = []
    overview = "No description available."
    rating = 0

    for _ in range(3):
        try:
            res = requests.get(url, params=params, timeout=20)
            if res.status_code == 200:
                data = res.json()
                if data.get("poster_path"):
                    poster = f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
                genres = [g["name"] for g in data.get("genres", [])]
                overview = data.get("overview", overview)
                rating = round(data.get("vote_average", 0) / 2, 1)
                break
        except:
            time.sleep(1)

    return poster, genres, overview, rating

# -----------------------------
# Content-based recommend
# -----------------------------
def content_based_recommend(movie_title, n=5):
    if movie_title not in movies["title"].values:
        return []

    idx = movies[movies["title"] == movie_title].index[0]
    distances = sorted(
        list(enumerate(content_similarity[idx])),
        key=lambda x: x[1],
        reverse=True
    )[1:n+1]

    recs = []
    for i in distances:
        row = movies.iloc[i[0]]
        poster, genres, overview, rating = fetch_movie_details(row.movie_id)
        recs.append({
            "title": row.title,
            "poster": poster,
            "genres": genres,
            "overview": overview,
            "rating": rating
        })
    return recs

# -----------------------------
# Collaborative recommend
# -----------------------------
def collaborative_recommend(user_id, n=5):
    if user_id not in ratings or len(ratings[user_id]) < 2:
        return []

    rating_df = pd.DataFrame(ratings).T.fillna(0)
    sim = cosine_similarity(rating_df)
    sim_df = pd.DataFrame(sim, index=rating_df.index, columns=rating_df.index)

    sim_users = sim_df[user_id].drop(user_id)
    weighted_scores = pd.Series(0, index=rating_df.columns)

    for u, score in sim_users.items():
        weighted_scores += rating_df.loc[u] * score

    weighted_scores = weighted_scores / sim_users.sum()
    weighted_scores = weighted_scores[rating_df.loc[user_id] == 0]

    top_movies = weighted_scores.sort_values(ascending=False).head(n).index

    recs = []
    for mid in top_movies:
        row = movies[movies["movie_id"] == mid].iloc[0]
        poster, genres, overview, rating = fetch_movie_details(mid)
        recs.append({
            "title": row.title,
            "poster": poster,
            "genres": genres,
            "overview": overview,
            "rating": rating
        })
    return recs

# -----------------------------
# Add rating
# -----------------------------
def add_rating(user_id, movie_title, rating):
    movie_id = int(movies[movies["title"] == movie_title]["movie_id"].values[0])
    if user_id not in ratings:
        ratings[user_id] = {}
    ratings[user_id][movie_id] = int(rating)
    pickle.dump(ratings, open("ratings.pkl", "wb"))

# -----------------------------
# UI Inputs
# -----------------------------
user_id = st.text_input("👤 User ID", "user_1")
selected_movie = st.selectbox("🎥 Select a movie", movies["title"].values)
rating = st.slider("⭐ Rate this movie", 1, 5, 3)

# -----------------------------
# Selected movie display
# -----------------------------
movie_id = int(movies[movies["title"] == selected_movie]["movie_id"].values[0])
poster, genres, overview, tmdb_rating = fetch_movie_details(movie_id)

c1, c2 = st.columns([1, 2])
with c1:
    st.image(poster, width='stretch')
    st.markdown(f"<div class='rating'>⭐ TMDB: {tmdb_rating}/5</div>", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="movie-card">
        <div class="movie-title">{selected_movie}</div>
        <div>
            {''.join([f"<span class='genre-badge'>{g}</span>" for g in genres])}
        </div>
        <p class="overview">{overview}</p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Save rating
# -----------------------------
if st.button("💾 Save Rating"):
    add_rating(user_id, selected_movie, rating)
    st.success("Rating saved successfully!")

# -----------------------------
# Rating history
# -----------------------------
if user_id in ratings and ratings[user_id]:
    st.subheader("📊 Your Ratings")
    for mid, r in ratings[user_id].items():
        title = movies[movies["movie_id"] == mid]["title"].values[0]
        st.write(f"🎬 {title} — ⭐ {r}")

# -----------------------------
# Get recommendations
# -----------------------------
if st.button("🎯 Get Recommendations"):
    if user_id in ratings and len(ratings[user_id]) >= 2:
        st.session_state.recs_type = "🔵 Collaborative Filtering"
        st.session_state.recs = collaborative_recommend(user_id)
    else:
        st.session_state.recs_type = "🟢 Content-Based Filtering"
        st.session_state.recs = content_based_recommend(selected_movie)

# -----------------------------
# Display recommendations
# -----------------------------
if st.session_state.recs:
    st.subheader(st.session_state.recs_type)
    for rec in st.session_state.recs:
        c1, c2 = st.columns([1, 3])
        with c1:
            st.image(rec["poster"], width='stretch')
        with c2:
            st.markdown(f"""
            <div class="movie-card">
                <div class="movie-title">{rec['title']}</div>
                <div class="rating">⭐ {rec['rating']}/5</div>
                <div>
                    {''.join([f"<span class='genre-badge'>{g}</span>" for g in rec["genres"]])}
                </div>
                <p class="overview">{rec["overview"][:300]}...</p>
            </div>
            """, unsafe_allow_html=True)