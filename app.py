import requests
import streamlit as st
import random

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-rec-cige.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
TMDB_LOGO = "https://image.tmdb.org/t/p/original" # For OTT logos
TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8" 

st.set_page_config(page_title="Cinema AI | Smart Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# STYLES
# =============================
st.markdown(
    """
<style>
.stApp { background-color: #141414; color: white; }
.movie-link { text-decoration: none; color: inherit; display: block; position: relative; }
.movie-card { position: relative; transition: transform 0.4s ease; border-radius: 10px; overflow: hidden; cursor: pointer; }
.movie-card:hover { transform: scale(1.1); z-index: 99; box-shadow: 0px 10px 30px rgba(0,0,0,0.7); }
.play-btn { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 60px; color: white; opacity: 0; transition: opacity 0.3s ease; background: rgba(0,0,0,0.3); border-radius: 50%; padding: 10px; }
.movie-card:hover .play-btn { opacity: 1; }
.movie-title { font-size: 0.9rem; font-weight: bold; color: #e5e5e5; margin-top: 12px; text-align: center; }
.ott-badge { background: #333; padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; margin-right: 5px; border: 1px solid #444; }
div.stButton > button { background-color: #333; color: white; border: none; width: 100%; border-radius: 5px; margin-top: 5px; }
div.stButton > button:hover { background-color: #0078ff; color: white; }
section[data-testid="stSidebar"] { background-color: #181818 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# API HELPERS
# =============================
@st.cache_data(ttl=60)
def api_get_json(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        return r.json() if r.status_code < 400 else None
    except: return None

def fetch_trailer(tmdb_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={TMDB_API_KEY}"
        res = requests.get(url, timeout=5).json()
        for v in res.get("results", []):
            if v["site"] == "YouTube" and v["type"] == "Trailer":
                return f"https://www.youtube.com/watch?v={v['key']}"
    except: return None

def fetch_ott_providers(tmdb_id):
    """Fetches Streaming/OTT platforms for the movie"""
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers?api_key={TMDB_API_KEY}"
        res = requests.get(url, timeout=5).json()
        # Defaulting to 'US' region, but can be changed to 'IN' or others
        results = res.get("results", {}).get("US", {}) 
        return {
            "flatrate": results.get("flatrate", []), # Streaming (Netflix, etc)
            "buy": results.get("buy", []),           # Rent/Buy
            "link": results.get("link")              # TMDB official watch link
        }
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
            t_url = fetch_trailer(tmdb_id)
            final_link = t_url if t_url else f"https://www.youtube.com/results?search_query={title}+trailer"
            with colset[c]:
                st.markdown(f'<a href="{final_link}" target="_blank" class="movie-link"><div class="movie-card"><img src="{poster}" style="width:100%;"><div class="play-btn">▶️</div></div></a>', unsafe_allow_html=True)
                if st.button("Details", key=f"det_{key_prefix}_{idx}_{tmdb_id}"): goto_details(tmdb_id)
                st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)

# =============================
# MAIN LOGIC
# =============================
with st.sidebar:
    st.title("🎬 Navigator")
    if st.button("🏠 Home", use_container_width=True): goto_home()
    if st.button("🍿 Surprise Me!", use_container_width=True):
        data = api_get_json("/home", params={"category": "popular", "limit": 20})
        if data: goto_details(random.choice(data)['tmdb_id'])
    st.markdown("---")
    home_category = st.selectbox("Explore By", ["trending", "popular", "top_rated", "upcoming"])
    grid_cols = st.slider("Layout", 4, 8, 6)

if st.session_state.view == "home":
    st.title("Cinema AI Recommender")
    typed = st.text_input("Find a movie...", placeholder="Search for titles...")
    if typed.strip():
        data = api_get_json("/tmdb/search", params={"query": typed.strip()})
        if data:
            raw = data.get("results", [])
            cards = [{"tmdb_id": x["id"], "title": x["title"], "poster_url": f"{TMDB_IMG}{x['poster_path']}"} for x in raw if x.get("poster_path")]
            poster_grid(cards[:18], cols=grid_cols, key_prefix="search")
    else:
        home_cards = api_get_json("/home", params={"category": home_category, "limit": 24})
        if home_cards: poster_grid(home_cards, cols=grid_cols, key_prefix="home")

elif st.session_state.view == "details":
    if st.button("← Back"): goto_home()
    tmdb_id = st.session_state.selected_tmdb_id
    data = api_get_json(f"/movie/id/{tmdb_id}")
    
    if data:
        l, r = st.columns([1, 2.2])
        with l: st.image(data.get("poster_url"), use_container_width=True)
        with r:
            st.header(data.get("title"))
            st.markdown(f"**Released:** {data.get('release_date')} | **Rating:** ⭐ {data.get('vote_average')}")
            st.write(data.get("overview"))
            
            # --- NEW: OTT PROVIDERS SECTION ---
            st.markdown("### 📡 Available On")
            providers = fetch_ott_providers(tmdb_id)
            if providers and providers["flatrate"]:
                cols = st.columns(len(providers["flatrate"]) + 1)
                for i, p in enumerate(providers["flatrate"]):
                    with cols[i]:
                        st.image(f"{TMDB_LOGO}{p['logo_path']}", width=50)
                        st.caption(p['provider_name'])
            elif providers and providers["buy"]:
                st.info("Available to Rent/Buy")
                cols = st.columns(len(providers["buy"]) + 1)
                for i, p in enumerate(providers["buy"][:4]): # Limit to 4
                    with cols[i]:
                        st.image(f"{TMDB_LOGO}{p['logo_path']}", width=40)
            else:
                st.write("Checking availability...")
                st.caption("Availability data varies by region (Currently showing US).")

        st.divider()
        st.subheader("Discover Similar Titles")
        bundle = api_get_json("/movie/search", params={"query": data.get("title"), "tfidf_top_n": 12})
        if bundle:
            recs = [{"tmdb_id": x['tmdb']["tmdb_id"], "title": x['tmdb']["title"], "poster_url": x['tmdb']["poster_url"]} for x in bundle.get("tfidf_recommendations", []) if x.get("tmdb")]
            poster_grid(recs, cols=grid_cols, key_prefix="rec")