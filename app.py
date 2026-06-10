import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Futures OI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── storage helpers ───────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
INDEX_FILE = DATA_DIR / "products_index.json"


def load_index() -> dict:
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            return json.load(f)
    return {}


def save_index(idx: dict):
    with open(INDEX_FILE, "w") as f:
        json.dump(idx, f)


def product_path(symbol: str) -> Path:
    return DATA_DIR / f"{symbol.upper()}.json"


def save_product(symbol: str, oi_df, close_df, vol_df, dates):
    symbol = symbol.upper()
    contracts = [c for c in oi_df.columns if c != "date"]

    def df_to_arr(df):
        df2 = df.set_index("date") if "date" in df.columns else df
        rows = []
        for d in dates:
            row = []
            for c in contracts:
                if c in df2.columns and d in df2.index:
                    v = df2.loc[d, c]
                    if pd.isna(v):
                        row.append(None)
                    elif isinstance(v, (np.integer,)):
                        row.append(int(v))
                    elif isinstance(v, (np.floating,)):
                        row.append(round(float(v), 4))
                    else:
                        row.append(v)
                else:
                    row.append(None)
            rows.append(row)
        return rows

    payload = {
        "symbol": symbol,
        "dates": dates,
        "contracts": contracts,
        "oi": df_to_arr(oi_df),
        "close": df_to_arr(close_df),
        "volume": df_to_arr(vol_df),
    }
    with open(product_path(symbol), "w") as f:
        json.dump(payload, f, separators=(",", ":"))


def load_product(symbol: str) -> dict | None:
    p = product_path(symbol)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return None


def parse_upload(uploaded_file) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    xl = pd.ExcelFile(uploaded_file)
    required = {"oi", "close", "volume"}
    if not required.issubset(set(s.lower() for s in xl.sheet_names)):
        raise ValueError(f"Excel must have sheets: oi, close, volume. Found: {xl.sheet_names}")

    sheet_map = {s.lower(): s for s in xl.sheet_names}

    def read(name):
        df = pd.read_excel(uploaded_file, sheet_name=sheet_map[name])
        df = df.rename(columns={df.columns[0]: "date"})
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        return df

    oi_df = read("oi")
    close_df = read("close")
    vol_df = read("volume")

    dates = sorted(oi_df["date"].dropna().unique().tolist())
    return oi_df, close_df, vol_df, dates


# ── color helpers ─────────────────────────────────────────────────────────────
def pct_to_bg(pct):
    if pct is None or (isinstance(pct, float) and np.isnan(pct)):
        return ""
    ab = min(abs(pct) / 2.5, 1.0)
    alpha = 0.12 + ab * 0.78
    if pct > 0:
        r, g, b = 22, 163, 74
    else:
        r, g, b = 220, 38, 38
    return f"rgba({r},{g},{b},{alpha:.2f})"


def pct_to_text(pct):
    if pct is None or (isinstance(pct, float) and np.isnan(pct)):
        return "#94a3b8"
    return "#ffffff" if abs(pct) > 0.8 else "#1e293b"


def fmt_num(v):
    if v is None:
        return "—"
    return f"{round(v):,}"


def fmt_pct(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return ""
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:.2f}%"


def fmt_chg(c):
    if c is None or (isinstance(c, float) and np.isnan(c)):
        return ""
    sign = "+" if c >= 0 else ""
    return f"{sign}{round(c):,}"


# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown(
        """
<style>
/* sidebar */
section[data-testid="stSidebar"] { background: #0f172a; }
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
/* main bg */
.stApp { background: #0f1117; }
/* metric cards */
[data-testid="metric-container"] {
    background: #141820; border: 1px solid #1e2530;
    border-radius: 8px; padding: 12px 16px;
}
/* heatmap table */
.hm-table { border-collapse: collapse; width: 100%; font-size: 12px; font-family: monospace; }
.hm-table th {
    background: #141820; color: #64748b; font-size: 11px; font-weight: 600;
    padding: 7px 10px; text-align: right; border-bottom: 1px solid #1e2530;
    white-space: nowrap; position: sticky; top: 0;
}
.hm-table th:first-child { text-align: left; }
.hm-table td {
    padding: 5px 10px; text-align: right;
    border-bottom: 1px solid #0f1117; white-space: nowrap;
}
.hm-table td:first-child {
    text-align: left; color: #64748b; font-weight: 500;
    background: #141820; position: sticky; left: 0;
    border-right: 1px solid #1e2530;
}
.hm-table tr:hover td { filter: brightness(1.25); }
.cell-inner { display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.ov { font-size: 12px; font-weight: 600; }
.pv { font-size: 10px; opacity: 0.85; }
.legend-bar {
    height: 8px; width: 220px; border-radius: 4px;
    background: linear-gradient(to right,#7f1d1d,#dc2626,#fca5a5,#f8fafc,#86efac,#16a34a,#14532d);
    display: inline-block; vertical-align: middle;
}
.scrollable { overflow-x: auto; overflow-y: auto; max-height: 72vh;
    border-radius: 8px; border: 1px solid #1e2530; }
</style>
""",
        unsafe_allow_html=True,
    )


# ── sidebar upload ────────────────────────────────────────────────────────────
def sidebar_upload():
    st.sidebar.header("📤 Upload Product Data")
    st.sidebar.caption("Excel with sheets: **oi**, **close**, **volume** (date in col 1)")
    uploaded = st.sidebar.file_uploader("Choose .xlsx file", type=["xlsx"])
    symbol_input = st.sidebar.text_input("Product symbol (e.g. SB, BO, SM, W, C)", max_chars=10)

    if st.sidebar.button("💾 Save Product", use_container_width=True):
        if not uploaded:
            st.sidebar.error("Please upload a file.")
        elif not symbol_input.strip():
            st.sidebar.error("Please enter a product symbol.")
        else:
            sym = symbol_input.strip().upper()
            try:
                with st.spinner(f"Processing {sym}..."):
                    oi_df, close_df, vol_df, dates = parse_upload(uploaded)
                    save_product(sym, oi_df, close_df, vol_df, dates)
                    idx = load_index()
                    idx[sym] = {
                        "name": sym,
                        "dates": len(dates),
                        "contracts": len([c for c in oi_df.columns if c != "date"]),
                        "from": dates[0] if dates else "",
                        "to": dates[-1] if dates else "",
                        "uploaded": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    save_index(idx)
                st.sidebar.success(f"✅ {sym} saved ({len(dates)} days)")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

    st.sidebar.divider()

    # delete
    idx = load_index()
    if idx:
        st.sidebar.subheader("🗑 Remove Product")
        del_sym = st.sidebar.selectbox("Select to remove", [""] + list(idx.keys()), label_visibility="collapsed")
        if st.sidebar.button("Remove", disabled=not del_sym):
            if del_sym:
                p = product_path(del_sym)
                if p.exists():
                    p.unlink()
                idx.pop(del_sym, None)
                save_index(idx)
                st.sidebar.success(f"Removed {del_sym}")
                st.rerun()


# ── heatmap builder ───────────────────────────────────────────────────────────
def build_heatmap(data, filtered_dates, active_contracts, view_mode):
    dates_idx = {d: i for i, d in enumerate(data["dates"])}
    contracts_idx = {c: i for i, c in enumerate(data["contracts"])}

    sheet = "volume" if view_mode == "vol" else "close" if view_mode == "close" else "oi"

    def get(s, date, contract):
        di = dates_idx.get(date, -1)
        ci = contracts_idx.get(contract, -1)
        if di < 0 or ci < 0:
            return None
        row = data[s][di]
        return row[ci] if row and ci < len(row) else None

    all_dates_sorted = sorted(data["dates"])
    date_prev = {d: all_dates_sorted[all_dates_sorted.index(d) - 1] if all_dates_sorted.index(d) > 0 else None
                 for d in all_dates_sorted}

    sorted_dates = sorted(filtered_dates, reverse=True)

    # header
    cols_header = "".join(f"<th>{c}</th>" for c in active_contracts)
    rows_html = ""

    for date in sorted_dates:
        prev_date = date_prev.get(date)
        row_html = f"<td>{date}</td>"
        for c in active_contracts:
            val = get(sheet, date, c)
            prev_val = get(sheet, prev_date, c) if prev_date else None
            chg = (val - prev_val) if (val is not None and prev_val is not None) else None
            pct = (chg / prev_val * 100) if (chg is not None and prev_val and prev_val != 0) else None

            bg = pct_to_bg(pct)
            col = pct_to_text(pct)
            style = f"background:{bg};color:{col}" if bg else f"color:{col}"

            if view_mode == "oi":
                main = fmt_num(val)
                sub = fmt_pct(pct)
            elif view_mode == "chg":
                main = fmt_chg(chg)
                sub = fmt_pct(pct)
            elif view_mode == "pct":
                main = fmt_pct(pct)
                sub = ""
            elif view_mode == "vol":
                main = fmt_num(val)
                sub = fmt_pct(pct)
            else:  # close
                main = f"{val:.2f}" if val is not None else "—"
                sub = fmt_pct(pct)

            row_html += f'<td style="{style}"><div class="cell-inner"><span class="ov">{main}</span>'
            if sub:
                row_html += f'<span class="pv">{sub}</span>'
            row_html += "</div></td>"

        rows_html += f"<tr>{row_html}</tr>"

    return f"""
<div class="scrollable">
<table class="hm-table">
<thead><tr><th>Date</th>{cols_header}</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>
"""


# ── stats cards ───────────────────────────────────────────────────────────────
def show_stats(data, filtered_dates, active_contracts):
    if not filtered_dates:
        return
    dates_idx = {d: i for i, d in enumerate(data["dates"])}
    contracts_idx = {c: i for i, c in enumerate(data["contracts"])}
    all_dates_sorted = sorted(data["dates"])

    def get_oi(date, contract):
        di = dates_idx.get(date, -1)
        ci = contracts_idx.get(contract, -1)
        if di < 0 or ci < 0:
            return None
        row = data["oi"][di]
        return row[ci] if row and ci < len(row) else None

    latest = max(filtered_dates)
    prev_all = all_dates_sorted[all_dates_sorted.index(latest) - 1] if all_dates_sorted.index(latest) > 0 else None

    total_oi, total_prev = 0, 0
    big_gain = (None, "")
    big_drop = (None, "")

    for c in active_contracts:
        v = get_oi(latest, c)
        p = get_oi(prev_all, c) if prev_all else None
        if v:
            total_oi += v
        if p:
            total_prev += p
        if v is not None and p is not None:
            chg = v - p
            if big_gain[0] is None or chg > big_gain[0]:
                big_gain = (chg, c)
            if big_drop[0] is None or chg < big_drop[0]:
                big_drop = (chg, c)

    total_chg = total_oi - total_prev
    total_pct = (total_chg / total_prev * 100) if total_prev else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total OI (latest)", f"{round(total_oi):,}", delta=None)
    c2.metric("OI Change (1d)", fmt_chg(total_chg), delta=f"{total_pct:+.2f}%")
    c3.metric(
        "Biggest gain (1d)",
        f"{fmt_chg(big_gain[0])}  {big_gain[1]}" if big_gain[0] is not None else "—",
    )
    c4.metric(
        "Biggest drop (1d)",
        f"{fmt_chg(big_drop[0])}  {big_drop[1]}" if big_drop[0] is not None else "—",
    )


# ── OI trend chart ────────────────────────────────────────────────────────────
def show_trend_chart(data, filtered_dates, active_contracts):
    import plotly.graph_objects as go

    dates_idx = {d: i for i, d in enumerate(data["dates"])}
    contracts_idx = {c: i for i, c in enumerate(data["contracts"])}

    def get_oi(date, contract):
        di = dates_idx.get(date, -1)
        ci = contracts_idx.get(contract, -1)
        if di < 0 or ci < 0:
            return None
        row = data["oi"][di]
        return row[ci] if row and ci < len(row) else None

    sorted_dates = sorted(filtered_dates)
    totals = []
    for d in sorted_dates:
        t = sum(v for c in active_contracts if (v := get_oi(d, c)) is not None)
        totals.append(t if t > 0 else None)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sorted_dates, y=totals,
        mode="lines", name="Total OI",
        line=dict(color="#3b82f6", width=1.5),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.07)",
    ))
    fig.update_layout(
        height=160, margin=dict(l=40, r=10, t=10, b=30),
        paper_bgcolor="#141820", plot_bgcolor="#141820",
        font=dict(color="#64748b", size=10),
        xaxis=dict(gridcolor="#1e2530", showline=False),
        yaxis=dict(gridcolor="#1e2530", showline=False,
                   tickformat=",", ticksuffix=""),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    inject_css()
    sidebar_upload()

    idx = load_index()
    if not idx:
        st.title("📊 Futures OI Dashboard")
        st.info("👈 Upload your first product Excel file in the sidebar to get started.")
        return

    # product selector
    st.markdown("### 📊 Futures Open Interest Dashboard")
    col_prod, col_gap = st.columns([2, 6])
    with col_prod:
        products = list(idx.keys())
        selected_product = st.selectbox("Product", products, label_visibility="collapsed",
                                        format_func=lambda x: f"⬤  {x}  —  {idx[x]['from']} → {idx[x]['to']}")

    data = load_product(selected_product)
    if data is None:
        st.error(f"Data file for {selected_product} not found. Please re-upload.")
        return

    all_contracts = data["contracts"]
    all_dates = data["dates"]

    # ── controls row ──────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 3, 1.5])
    with col1:
        date_from = st.date_input("From", value=datetime.strptime(all_dates[-min(260, len(all_dates))], "%Y-%m-%d"),
                                  min_value=datetime.strptime(all_dates[0], "%Y-%m-%d"),
                                  max_value=datetime.strptime(all_dates[-1], "%Y-%m-%d"))
    with col2:
        date_to = st.date_input("To", value=datetime.strptime(all_dates[-1], "%Y-%m-%d"),
                                min_value=datetime.strptime(all_dates[0], "%Y-%m-%d"),
                                max_value=datetime.strptime(all_dates[-1], "%Y-%m-%d"))
    with col3:
        # smart default: contracts active near end of data
        default_contracts = []
        if all_contracts:
            # pick last 8 contracts that have data
            dates_idx = {d: i for i, d in enumerate(all_dates)}
            last_di = len(all_dates) - 1
            for c in reversed(all_contracts):
                ci = all_contracts.index(c)
                row = data["oi"][last_di]
                if row and ci < len(row) and row[ci] is not None and row[ci] > 0:
                    default_contracts.append(c)
                if len(default_contracts) >= 8:
                    break
            default_contracts = list(reversed(default_contracts))

        selected_contracts = st.multiselect(
            "Contracts", options=all_contracts,
            default=default_contracts or all_contracts[:6],
        )
    with col4:
        view_mode = st.selectbox("View", ["oi", "chg", "pct", "vol", "close"],
                                 format_func=lambda x: {
                                     "oi": "OI Value", "chg": "Daily Change",
                                     "pct": "% Change", "vol": "Volume", "close": "Close Price"
                                 }[x])

    if not selected_contracts:
        st.warning("Select at least one contract.")
        return

    # filter dates
    from_str = date_from.strftime("%Y-%m-%d")
    to_str = date_to.strftime("%Y-%m-%d")
    filtered_dates = [d for d in all_dates if from_str <= d <= to_str]

    if not filtered_dates:
        st.warning("No data in selected date range.")
        return

    # ── stats ─────────────────────────────────────────────────────────────────
    show_stats(data, filtered_dates, selected_contracts)
    st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

    # ── trend chart ───────────────────────────────────────────────────────────
    with st.container():
        st.markdown(
            "<div style='background:#141820;border:1px solid #1e2530;border-radius:8px;padding:12px 16px;margin-bottom:12px'>"
            "<p style='font-size:12px;color:#64748b;margin-bottom:4px'>Total OI — selected contracts</p>",
            unsafe_allow_html=True,
        )
        show_trend_chart(data, filtered_dates, selected_contracts)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── heatmap ───────────────────────────────────────────────────────────────
    hm_html = build_heatmap(data, filtered_dates, selected_contracts, view_mode)
    st.markdown(hm_html, unsafe_allow_html=True)

    # legend
    st.markdown(
        "<div style='margin-top:10px;font-size:11px;color:#64748b;display:flex;align-items:center;gap:10px'>"
        "<span>Color scale:</span>"
        "<span class='legend-bar'></span>"
        "<span>Red = OI falling &nbsp;|&nbsp; Green = OI rising &nbsp;|&nbsp; Intensity = magnitude</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # footer info
    st.markdown(
        f"<div style='margin-top:20px;font-size:11px;color:#334155'>"
        f"{selected_product} · {len(filtered_dates)} trading days · "
        f"{len(selected_contracts)} contracts · Last upload: {idx[selected_product].get('uploaded','')}"
        f"</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
