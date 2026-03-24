import requests
import streamlit as st
import random
import json
import os

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-rec-cige.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Cinema AI", page_icon="🎬", layout="wide")

# =============================
# UI (Netflix Hover)
# =============================
st.markdown("""
<style>
.stApp { background-color: #141414; color: white; }

.movie-card {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    border-radius: 10px;
    overflow: hidden;
}
.movie-card:hover {
    transform: scale(1.12);
    z-index: 10;
    box-shadow: 0px 10px 25px rgba(0,0,0,0.7);
}
</style>
""", unsafe_allow_html=True)

# =============================
# FILE SETUP
# =============================
USER_FILE = "users.json"

if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=4)

USERS = load_users()

# =============================
# SESSION
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "view" not in st.session_state:
    st.session_state.view = "home"

# =============================
# LOGIN
# =============================
def login_page():
    st.title("🔐 Login / Signup")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u in USERS and USERS[u]["password"] == p:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        u = st.text_input("Create Username")
        p = st.text_input("Create Password", type="password")
        if st.button("Signup"):
            if u in USERS:
                st.warning("User exists")
            else:
                USERS[u] = {"password": p, "history": []}
                save_users(USERS)
                st.success("Account created")

# =============================
# API
# =============================
@st.cache_data(ttl=60)
def api_get_json(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        return r.json() if r.status_code < 400 else None
    except:
        return None

# =============================
# NAVIGATION
# =============================
def goto_home():
    st.session_state.view = "home"
    st.rerun()

def goto_details(tmdb_id, title):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id

    if title not in USERS[st.session_state.user]["history"]:
        USERS[st.session_state.user]["history"].append(title)
        save_users(USERS)

    st.rerun()

# =============================
# GRID (FAST)
# =============================
def poster_grid(cards):
    if not cards:
        st.warning("No movies found")
        return

    cols = st.columns(6)

    for i, m in enumerate(cards):
        # 🔥 NO API CALL HERE (FAST)
        link = f"https://www.youtube.com/results?search_query={m['title']} trailer"

        with cols[i % 6]:
            st.markdown(f"""
            <a href="{link}" target="_blank">
                <div class="movie-card">
                    <img src="{m['poster_url']}" style="width:100%;">
                </div>
            </a>
            """, unsafe_allow_html=True)

            if st.button("Details", key=f"{m['tmdb_id']}_{i}"):
                goto_details(m["tmdb_id"], m["title"])

            st.caption(m["title"])

# =============================
# AUTH CHECK
# =============================
if not st.session_state.logged_in:
    login_page()
    st.stop()

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.write(f"👤 {st.session_state.user}")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.write(f"👥 Users: {len(USERS)}")

    st.markdown("### History")
    for h in USERS[st.session_state.user]["history"][-5:][::-1]:
        st.caption(h)

    if st.button("Home"):
        goto_home()

    category = st.selectbox("Category", ["trending", "popular", "top_rated"])

# =============================
# MAIN
# =============================
if st.session_state.view == "home":
    st.title("🎬 Cinema AI")

    query = st.text_input("Search movie...")

    # SEARCH
    if query:
        data = api_get_json("/tmdb/search", {"query": query})

        if data:
            cards = [
                {
                    "tmdb_id": m["id"],
                    "title": m["title"],
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}"
                }
                for m in data.get("results", [])
                if m.get("poster_path")
            ]
            poster_grid(cards)

    # HOME (ALWAYS SHOW)
    else:
        data = api_get_json("/home", {"category": category, "limit": 24})

        cards = []

        if data:
            cards = [
                {
                    "tmdb_id": m.get("tmdb_id") or m.get("id"),
                    "title": m.get("title"),
                    "poster_url": m.get("poster_url") or (
                        f"{TMDB_IMG}{m.get('poster_path')}" if m.get("poster_path") else None
                    )
                }
                for m in data
                if (m.get("poster_url") or m.get("poster_path"))
            ]

        # fallback
        if not cards:
            fallback = api_get_json("/home", {"category": "popular", "limit": 24})
            if fallback:
                cards = [
                    {
                        "tmdb_id": m.get("tmdb_id") or m.get("id"),
                        "title": m.get("title"),
                        "poster_url": m.get("poster_url") or (
                            f"{TMDB_IMG}{m.get('poster_path')}" if m.get("poster_path") else None
                        )
                    }
                    for m in fallback
                    if (m.get("poster_url") or m.get("poster_path"))
                ]

        poster_grid(cards)

# =============================
# DETAILS
# =============================
elif st.session_state.view == "details":

    if st.button("← Back"):
        goto_home()

    movie = api_get_json(f"/movie/id/{st.session_state.selected_tmdb_id}")

    if movie:
        st.header(movie.get("title"))
        st.image(movie.get("poster_url"))
        st.write(movie.get("overview"))

        st.subheader("🎯 Similar Movies")

        recs = api_get_json("/movie/search", {"query": movie.get("title")})

        cards = []

        if recs and recs.get("tfidf_recommendations"):
            cards = [
                {
                    "tmdb_id": x["tmdb"]["tmdb_id"],
                    "title": x["tmdb"]["title"],
                    "poster_url": x["tmdb"]["poster_url"]
                }
                for x in recs["tfidf_recommendations"]
                if x.get("tmdb")
            ]

        if not cards:
            fallback = api_get_json("/home", {"category": "popular", "limit": 12})
            if fallback:
                cards = [
                    {
                        "tmdb_id": m.get("tmdb_id") or m.get("id"),
                        "title": m.get("title"),
                        "poster_url": m.get("poster_url") or (
                            f"{TMDB_IMG}{m.get('poster_path')}" if m.get("poster_path") else None
                        )
                    }
                    for m in fallback
                    if (m.get("poster_url") or m.get("poster_path"))
                ]

        poster_grid(cards)