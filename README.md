# Futures OI Dashboard

Interactive Open Interest heatmap dashboard for commodity futures (Soybean, Bean Oil, Soy Meal, etc.) built with Streamlit.

## Features

- 📊 **OI Heatmap** — color-coded daily OI changes across contracts
- 📈 **5 view modes** — OI Value, Daily Change, % Change, Volume, Close Price
- 🔄 **Multi-product** — upload any number of products (SB, BO, SM, W, C, etc.)
- 💾 **Persistent storage** — data saved as JSON, survives refreshes and redeployments
- 📉 **Trend chart** — total OI line chart across selected contracts
- 🗂 **Date range & contract filtering**

## Excel Format

Your Excel file must have exactly **3 sheets**:
| Sheet | Contents |
|-------|----------|
| `oi` | Open Interest — first column = date, rest = contract columns |
| `close` | Close Price — same layout |
| `volume` | Volume — same layout |

Contract column names should follow the format `SBN26`, `BOH27`, etc.

## Local Setup

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/futures-oi-dashboard.git
cd futures-oi-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

## Deploy on Streamlit Community Cloud (Free)

1. **Fork / push** this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo, branch `main`, file `app.py`
4. Click **Deploy** — done!

### Persistent Data on Streamlit Cloud

Streamlit Community Cloud has **ephemeral filesystem** — files are lost on restart.  
To make data truly permanent, use one of these backends:

#### Option A — GitHub itself (simplest, free)
Use the `st-github-contents` approach: commit uploaded JSON back to the repo via GitHub API.  
See `storage_github.py` (optional extension).

#### Option B — Streamlit Secrets + external storage
Add a `secrets.toml` and use any of:
- **Supabase** (free Postgres) — replace `save_product` / `load_product` in `app.py`
- **MongoDB Atlas** (free tier)
- **AWS S3 / Cloudflare R2**

#### Option C — Pre-seed data (recommended for private use)
Run the app locally, upload all your products, then **commit the `data/` folder** to git:
```bash
git add data/
git commit -m "seed product data"
git push
```
The JSON files in `data/` will be deployed with the app and persist as long as the repo doesn't change.

## Project Structure

```
futures-oi-dashboard/
├── app.py                  # Main Streamlit app
├── requirements.txt
├── .streamlit/
│   └── config.toml         # Dark theme config
├── data/                   # Persisted product JSON (commit this!)
│   ├── products_index.json
│   ├── SB.json
│   ├── BO.json
│   └── ...
└── README.md
```
