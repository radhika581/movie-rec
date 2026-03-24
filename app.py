import requests
import streamlit as st
import random

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-rec-cige.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8" # Your TMDB Key

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# STYLES (Modern Dark Theme)
# =============================
st.markdown(
    """
<style>
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1400px; }
.small-muted { color:#6b7280; font-size: 0.92rem; }
.movie-title { font-size: 0.9rem; font-weight: bold; line-height: 1.15rem; height: 2.3rem; overflow: hidden; margin-top: 5px;}
.card { border: 1px solid rgba(0,0,0,0.08); border-radius: 16px; padding: 14px; background: rgba(255,255,255,0.05); }
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
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}"
        return r.json(), None
    except Exception as e:
        return None, str(e)

def fetch_trailer(tmdb_id):
    """Fetches YouTube Trailer Link"""
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={TMDB_API_KEY}"
        res = requests.get(url, timeout=5).json()
        for v in res.get("results", []):
            if v["site"] == "YouTube" and v["type"] == "Trailer":
                return f"https://www.youtube.com/watch?v={v['key']}"
    except:
        return None
    return None

# =============================
# STATE + ROUTING
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

def goto_home():
    st.session_state.view = "home"
    st.query_params["view"] = "home"
    if "id" in st.query_params: del st.query_params["id"]
    st.rerun()

def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.query_params["view"] = "details"
    st.query_params["id"] = str(tmdb_id)
    st.rerun()

# =============================
# UI COMPONENTS
# =============================
def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies to show.")
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
                if poster:
                    st.image(poster, use_container_width=True)
                else:
                    st.write("🖼️ No poster")
                
                # Action Buttons
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Open", key=f"open_{key_prefix}_{idx}_{tmdb_id}"):
                        goto_details(tmdb_id)
                with c2:
                    t_url = fetch_trailer(tmdb_id)
                    if t_url:
                        st.link_button("📺 Watch", t_url)
                    else:
                        st.button("N/A", disabled=True, key=f"no_t_{idx}_{tmdb_id}")
                
                st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)

def to_cards_from_tfidf_items(tfidf_items):
    cards = []
    for x in tfidf_items or []:
        tmdb = x.get("tmdb") or {}
        if tmdb.get("tmdb_id"):
            cards.append({
                "tmdb_id": tmdb["tmdb_id"],
                "title": tmdb.get("title") or x.get("title") or "Untitled",
                "poster_url": tmdb.get("poster_url"),
            })
    return cards

def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    keyword_l = keyword.strip().lower()
    raw_items = []
    if isinstance(data, dict) and "results" in data:
        for m in data.get("results", []):
            if m.get("id") and m.get("title"):
                raw_items.append({
                    "tmdb_id": int(m["id"]),
                    "title": m["title"],
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None,
                    "release_date": m.get("release_date", ""),
                })
    matched = [x for x in raw_items if keyword_l in x["title"].lower()]
    final = matched if matched else raw_items
    suggestions = [(f"{x['title']} ({x['release_date'][:4]})", x['tmdb_id']) for x in final[:10]]
    cards = [{"tmdb_id": x["tmdb_id"], "title": x["title"], "poster_url": x["poster_url"]} for x in final[:limit]]
    return suggestions, cards

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.markdown("## 🎬 Menu")
    if st.button("🏠 Home", use_container_width=True): goto_home()
    
    # UNIQUE FEATURE: Surprise Me
    if st.button("🍿 Surprise Me!", use_container_width=True):
        # Fetching from 'top_rated' to ensure a good surprise
        data, _ = api_get_json("/home", params={"category": "top_rated", "limit": 20})
        if data:
            lucky_movie = random.choice(data)
            goto_details(lucky_movie['tmdb_id'])

    st.markdown("---")
    home_category = st.selectbox("Category", ["trending", "popular", "top_rated", "upcoming"], index=0)
    grid_cols = st.slider("Grid columns", 4, 8, 6)

# =============================
# MAIN APP LOGIC
# =============================
st.title("🎬 Movie Recommender")

if st.session_state.view == "home":
    typed = st.text_input("Search movie title...", placeholder="Type: Avenger, Batman...")
    if typed.strip():
        data, err = api_get_json("/tmdb/search", params={"query": typed.strip()})
        if not err and data:
            suggestions, cards = parse_tmdb_search_to_cards(data, typed.strip())
            if suggestions:
                sel = st.selectbox("Quick Select", ["-- Choose --"] + [s[0] for s in suggestions])
                if sel != "-- Choose --":
                    goto_details(dict(suggestions)[sel])
            st.markdown("### Search Results")
            poster_grid(cards, cols=grid_cols, key_prefix="search")
    else:
        st.markdown(f"### 🏠 {home_category.title()}")
        home_cards, err = api_get_json("/home", params={"category": home_category, "limit": 24})
        if home_cards: poster_grid(home_cards, cols=grid_cols, key_prefix="home")

elif st.session_state.view == "details":
    tmdb_id = st.session_state.selected_tmdb_id
    if st.button("← Back"): goto_home()
    
    data, err = api_get_json(f"/movie/id/{tmdb_id}")
    if data:
        l, r = st.columns([1, 2.5])
        with l: st.image(data.get("poster_url", ""), use_container_width=True)
        with r:
            st.header(data.get("title"))
            st.caption(f"Released: {data.get('release_date')} | ⭐ {data.get('vote_average')}")
            st.write(data.get("overview"))
        
        st.divider()
        st.subheader("✅ Recommendations")
        bundle, _ = api_get_json("/movie/search", params={"query": data.get("title"), "tfidf_top_n": 12})
        if bundle:
            st.markdown("#### 🔎 Because you liked this")
            poster_grid(to_cards_from_tfidf_items(bundle.get("tfidf_recommendations")), cols=grid_cols, key_prefix="rec")