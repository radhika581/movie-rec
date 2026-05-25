# 🎬 Cinema AI — Movie Recommendation System

A **Netflix-inspired movie recommendation web app** built with Python and Streamlit. Users can log in, search movies, browse trending/popular/top-rated content, and get personalised TF-IDF based recommendations — all powered by the TMDB API.

🚀 **Live Demo:** [movie-rec-cige.onrender.com](https://movie-rec-cige.onrender.com)

---

## 📸 Screenshots

> _Add screenshots of your app here — Home page, Login page, Movie Details page_
> _(Tip: Press `Win + Shift + S` to take a screenshot and drag it into the repo)_

---

## ✨ Features

- 🔐 **User Authentication** — Signup / Login with session management
- 🎥 **Movie Browsing** — Trending, Popular, and Top Rated categories
- 🔍 **Search** — Real-time movie search powered by TMDB API
- 🤖 **AI Recommendations** — TF-IDF cosine similarity to suggest similar movies
- 📋 **Watch History** — Tracks last 5 movies viewed per user
- 🎨 **Netflix-style UI** — Dark theme with hover zoom effects on movie cards
- 🔗 **Trailer Links** — One-click YouTube trailer search per movie

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit, Custom CSS |
| Backend | Python, Flask REST API |
| ML / Recommendations | TF-IDF, Cosine Similarity (Scikit-learn) |
| Data | TMDB API, Pandas, NumPy |
| Storage | JSON (user data), Pickle (model files) |
| Deployment | Render (backend API + frontend) |

---

## 📁 Project Structure

```
movie-rec/
├── app.py                  # Streamlit frontend (UI + auth + navigation)
├── main.py                 # Flask backend API (recommendations + TMDB)
├── requirements.txt        # Python dependencies
├── runtime.txt             # Python version for deployment
├── df.pkl                  # Preprocessed movie dataframe
├── tfidf.pkl               # Trained TF-IDF vectorizer
├── tfidf_matrix.pkl        # TF-IDF feature matrix
├── indices.pkl             # Movie title → index mapping
└── users.json              # User accounts and watch history
```

---

## ⚙️ How It Works

1. Movie metadata (title, genres, overview, cast) is preprocessed and vectorized using **TF-IDF**.
2. When a user views a movie, **cosine similarity** is computed against all other movies in the dataset.
3. The top-N most similar movies are returned as recommendations.
4. Poster images, ratings, and metadata are fetched live from the **TMDB API**.

---

## 🚀 Run Locally

### Prerequisites
- Python 3.10+
- TMDB API Key (free at [themoviedb.org](https://www.themoviedb.org/))

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/radhika581/movie-rec.git
cd movie-rec

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your TMDB API key
# Create a .env file (do NOT commit this):
# TMDB_API_KEY=your_api_key_here

# 5. Run the backend API
python main.py

# 6. In a new terminal, run the Streamlit app
streamlit run app.py
```

---

## 📦 Dependencies

```
streamlit
requests
pandas
numpy
scikit-learn
flask
pickle5
python-dotenv
```

Install all with:
```bash
pip install -r requirements.txt
```

---

## 🌐 Deployment

- **Backend API** deployed on [Render](https://render.com) at `https://movie-rec-cige.onrender.com`
- **Frontend** runs via Streamlit, also hosted on Render
- `runtime.txt` specifies the Python version for the deployment environment

---

## 👩‍💻 Author

**Radhika**
B.Sc. Computer Science (AI) — Gurugram University

[![GitHub](https://img.shields.io/badge/GitHub-radhika581-black?logo=github)](https://github.com/radhika581)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://linkedin.com/in/radhika)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
