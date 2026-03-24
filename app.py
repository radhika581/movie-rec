import requests
import streamlit as st
import random
import streamlit.components.v1 as components

# =============================
# 1. CONFIG & PAGE SETUP
# =============================
API_BASE = "https://movie-rec-cige.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
TMDB_LOGO = "https://image.tmdb.org/t/p/original" 
TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8" 

st.set_page_config(page_title="Cinema AI", page_icon="🎬", layout="wide")

# Custom CSS for UI
st.markdown("""
<style>
.stApp { background-color: #141414; color: white; }
.movie-link { text-decoration: none; color: inherit; display: block; position: relative; }
.movie-card { position: relative; transition: transform 0.4s ease; border-radius: 10px; overflow: hidden; cursor: pointer; }
.movie-card:hover { transform: scale(1.08); z-index: 9; box-shadow: 0px 10px 30px rgba(0,0,0,0.7); }
.play-btn { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 60px; opacity: 0; transition: opacity 0.3s ease; pointer-events: none; }
.movie-card:hover .play-btn { opacity: 1; }
.movie-title { font-size: 0.9rem; font-weight: bold; color: #e5e5e5; margin-top: 10px; text-align: center; height: 3rem; overflow: hidden; }
section[data-testid="stSidebar"] { background-color: #181818 !important; }
div.stButton > button { background-color: #333; color: white; border: none; width: 100%; border-radius: 5px; }
div.stButton > button:hover { background-color: #0078ff; }
</style>
""", unsafe_allow_html=True)

# =============================
# 2. DATA FETCHING (Robust)
# =============================
@st.cache_data(ttl=300)
def api_get_json(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

def fetch_trailer(tmdb_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={TMDB_API_KEY}"
        res = requests.get(url, timeout=5).json()
        for v in res.get("results", []):
            if v["site"] == "YouTube" and v["type"] == "Trailer":
                return f"https://www.youtube.com/watch?v={v['key']}"
    except: return None

def fetch_ott(tmdb_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers?api_key={TMDB_API_KEY}"
        res = requests.get(url, timeout=5).json()
        # Checks India, then US
        return res.get("results", {}).get("IN") or res.get("results", {}).get("US")
    except: return None

# =============================
# 3. ROUTING & UI
# =============================
if "view" not in st.session_state: st.session_state.view = "home"

def goto_home(): st.session_state.view = "home"; st.rerun()
def goto_details(tid): st.session_state.view = "details"; st.session_state.selected_tmdb_id = tid; st.rerun()

def render_grid(cards, cols=6, key="grid"):
    if not cards: return st.write("No movies found.")
    idx = 0
    rows = (len(cards) + cols - 1) // cols
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards): break
            m = cards[idx]; idx += 1
            tid, title, poster = m['tmdb_id'], m['title'], m['poster_url']
            t_url = fetch_trailer(tid) or f"https://www.youtube.com/results?search_query={title}+trailer"
            with colset[c]:
                st.markdown(f'<a href="{t_url}" target="_blank" class="movie-link"><div class="movie-card"><img src="{poster}" style="width:100%;"><div class="play-btn">▶️</div></div></a>', unsafe_allow_html=True)
                if st.button("Details", key=f"{key}_{tid}_{idx}"): goto_details(tid)
                st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎬 Navigator")
    if st.button("🏠 Home", use_container_width=True): goto_home()
    cat = st.selectbox("Explore", ["trending", "popular", "top_rated", "upcoming"])
    g_cols = st.slider("Columns", 4, 8, 6)

# --- MAIN CONTENT ---
if st.session_state.view == "home":
    st.title("Cinema AI")
    q = st.text_input("Search...", placeholder="Start typing a movie name...")
    if q.strip():
        data = api_get_json("/tmdb/search", {"query": q})
        if data:
            results = [{"tmdb_id": x['id'], "title": x['title'], "poster_url": f"{TMDB_IMG}{x['poster_path']}"} for x in data.get("results", []) if x.get("poster_path")]
            render_grid(results[:18], cols=g_cols, key="search")
    else:
        h_data = api_get_json("/home", {"category": cat, "limit": 24})
        if h_data: render_grid(h_data, cols=g_cols, key="home")

elif st.session_state.view == "details":
    if st.button("← Back"): goto_home()
    tid = st.session_state.selected_tmdb_id
    data = api_get_json(f"/movie/id/{tid}")
    if data:
        l, r = st.columns([1, 2.5])
        with l: st.image(data.get("poster_url"), use_container_width=True)
        with r:
            st.header(data.get("title"))
            st.write(f"⭐ {data.get('vote_average')} | 📅 {data.get('release_date')}")
            st.write(data.get("overview"))
            
            # OTT Providers
            st.markdown("#### 📡 Streaming On")
            prov = fetch_ott(tid)
            if prov and prov.get("flatrate"):
                p_cols = st.columns(min(len(prov['flatrate']), 6))
                for i, p in enumerate(prov['flatrate'][:6]):
                    with p_cols[i]:
                        st.image(f"{TMDB_LOGO}{p['logo_path']}", width=45)
                        st.caption(p['provider_name'])
            else: st.caption("Not streaming currently.")

        st.divider()
        st.subheader("More Like This")
        bundle = api_get_json("/movie/search", {"query": data.get("title"), "tfidf_top_n": 12})
        if bundle:
            recs = [{"tmdb_id": x['tmdb']["tmdb_id"], "title": x['tmdb']["title"], "poster_url": x['tmdb']["poster_url"]} for x in bundle.get("tfidf_recommendations", []) if x.get("tmdb")]
            render_grid(recs, cols=g_cols, key="rec")

# =============================
# 4. SWIPE SCRIPT (Placed at bottom)
# =============================
components.html("""
<script>
    let startX = 0;
    document.addEventListener('touchstart', e => { startX = e.touches[0].clientX; });
    document.addEventListener('touchend', e => {
        let endX = e.changedTouches[0].clientX;
        if (startX - endX > 100) { window.history.forward(); }
        if (endX - startX > 100) { window.history.back(); }
    });
</script>
""", height=0)