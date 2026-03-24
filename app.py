import requests
import streamlit as st
import random

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-rec-cige.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8" 

st.set_page_config(page_title="Netflix Clone | Recommender", page_icon="🎬", layout="wide")

# =============================
# STYLES (Netflix Dark Theme & Hover Effects)
# =============================
st.markdown(
    """
<style>
/* Main Background */
.stApp {
    background-color: #141414;
    color: white;
}

/* Movie Poster Container */
.movie-card {
    position: relative;
    transition: transform 0.4s ease;
    cursor: pointer;
    border-radius: 10px;
    overflow: hidden;
}

.movie-card:hover {
    transform: scale(1.1);
    z-index: 99;
    box-shadow: 0px 10px 20px rgba(0,0,0,0.5);
}

/* Play Button Overlay */
.play-btn {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 50px;
    color: white;
    opacity: 0;
    transition: opacity 0.3s ease;
    background: rgba(0,0,0,0.4);
    border-radius: 50%;
    padding: 10px;
}

.movie-card:hover .play-btn {
    opacity: 1;
}

/* Text Styling */
.movie-title { 
    font-size: 0.9rem; 
    font-weight: bold; 
    color: #e5e5e5;
    margin-top: 10px;
    text-align: center;
}

/* Sidebar Customization */
section[data-testid="stSidebar"] {
    background-color: #181818 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# API HELPERS
# =============================
@st.cache_data(ttl=30)
def api_get_json(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        return r.json() if r.status_code < 400 else None, None
    except Exception as e:
        return None, str(e)

def fetch_trailer(tmdb_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={TMDB_API_KEY}"
        res = requests.get(url, timeout=5).json()
        for v in res.get("results", []):
            if v["site"] == "YouTube" and v["type"] == "Trailer":
                return f"https://www.youtube.com/watch?v={v['key']}"
    except: return None

# =============================
# STATE + ROUTING
# =============================
if "view" not in st.session_state: st.session_state.view = "home"

def goto_home():
    st.session_state.view = "home"
    st.rerun()

def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.rerun()

# =============================
# UI COMPONENTS
# =============================
def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies found.")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards): break
            m = cards[idx]
            idx += 1
            tmdb_id = m.get("tmdb_id")
            title = m.get("title", "Untitled")
            poster = m.get("poster_url")

            with colset[c]:
                # Netflix Hover Visual
                st.markdown(f"""
                <div class="movie-card">
                    <img src="{poster}" style="width:100%;">
                    <div class="play-btn">▶️</div>
                </div>
                """, unsafe_allow_html=True)

                # Buttons for actual functionality
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Details", key=f"det_{key_prefix}_{idx}"):
                        goto_details(tmdb_id)
                with c2:
                    t_url = fetch_trailer(tmdb_id)
                    if t_url:
                        st.link_button("Trailer", t_url)
                    else:
                        st.button("N/A", disabled=True, key=f"na_{key_prefix}_{idx}")
                
                st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg", width=150)
    if st.button("🏠 Home", use_container_width=True): goto_home()
    
    if st.button("🍿 Surprise Me!", use_container_width=True):
        data, _ = api_get_json("/home", params={"category": "popular", "limit": 20})
        if data: goto_details(random.choice(data)['tmdb_id'])

    st.markdown("---")
    home_category = st.selectbox("Browse by", ["trending", "popular", "top_rated", "upcoming"])
    grid_cols = st.slider("Columns", 4, 8, 6)

# =============================
# MAIN LOGIC
# =============================
if st.session_state.view == "home":
    st.title("Browse Movies")
    typed = st.text_input("Search for a movie...", placeholder="Type title here...")
    
    if typed.strip():
        data, _ = api_get_json("/tmdb/search", params={"query": typed.strip()})
        if data:
            # Simple results display
            raw = data.get("results", [])
            cards = [{"tmdb_id": x["id"], "title": x["title"], "poster_url": f"{TMDB_IMG}{x['poster_path']}"} for x in raw if x.get("poster_path")]
            poster_grid(cards[:18], cols=grid_cols, key_prefix="search")
    else:
        home_cards, _ = api_get_json("/home", params={"category": home_category, "limit": 24})
        if home_cards: poster_grid(home_cards, cols=grid_cols, key_prefix="home")

elif st.session_state.view == "details":
    if st.button("← Back to Browse"): goto_home()
    tmdb_id = st.session_state.selected_tmdb_id
    data, _ = api_get_json(f"/movie/id/{tmdb_id}")
    
    if data:
        l, r = st.columns([1, 2])
        with l: st.image(data.get("poster_url"), use_container_width=True)
        with r:
            st.header(data.get("title"))
            st.write(f"**Released:** {data.get('release_date')} | **Rating:** ⭐ {data.get('vote_average')}")
            st.write(data.get("overview"))
        
        st.divider()
        st.subheader("More Like This")
        bundle, _ = api_get_json("/movie/search", params={"query": data.get("title"), "tfidf_top_n": 12})
        if bundle:
            # Flatten TF-IDF items to cards
            recs = []
            for x in bundle.get("tfidf_recommendations", []):
                tm = x.get("tmdb")
                if tm: recs.append({"tmdb_id": tm["tmdb_id"], "title": tm["title"], "poster_url": tm["poster_url"]})
            poster_grid(recs, cols=grid_cols, key_prefix="rec")