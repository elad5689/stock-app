import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Pro Executive", layout="wide", initial_sidebar_state="collapsed")

# CSS יוקרתי
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0a192f 0%, #000000 100%); color: white; }
    header[data-testid="stHeader"] { background: transparent !important; }
    h1, h2, h3, h4, span, label, p { color: white !important; }
    .stTextInput input { color: #121212 !important; background-color: white !important; border-radius: 8px !important; }
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 10px; }
    .metric-value { font-size: 1.2rem; font-weight: bold; color: white !important; }
    .company-info-box { background-color: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; color: #e2e8f0; direction: ltr; text-align: left; border-left: 4px solid #3b82f6; line-height: 1.8; }
    div.stLinkButton > a { background-color: #003366 !important; color: white !important; border: 1px solid #3b82f6 !important; border-radius: 8px !important; font-weight: bold !important; width: 100%; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

def fmt(val, is_pct=False):
    if val is None or isinstance(val, str) or val == 0: return "N/A"
    return f"{val * 100:.1f}%" if is_pct else f"{val:,.1f}"

ticker = st.text_input("", value="IREN", placeholder="Enter Ticker...").upper().strip()

st.sidebar.title("Indicators")
opts = {
    "SMA 200": st.sidebar.toggle("SMA 200", value=True),
    "SMA 50": st.sidebar.toggle("SMA 50", value=True),
    "SMA 20": st.sidebar.toggle("SMA 20", value=True),
    "EMA 20": st.sidebar.toggle("EMA 20", value=True),
    "AVWAP": st.sidebar.toggle("AVWAP", value=True)
}

@st.cache_data(ttl=300)
def load_data(symbol):
    try:
        # שימוש ב-Ticker עם הגדרת User-Agent למניעת חסימות
        t = yf.Ticker(symbol)
        # הורדת היסטוריה של שנה אחת
        df = t.history(period="1y")
        if df.empty:
            # ניסיון גיבוי אם history נכשל
            df = yf.download(symbol, period="1y", progress=False)
        return df, t.info
    except:
        return pd.DataFrame(), {}

data, info = load_data(ticker)

if not data.empty and len(data) > 0:
    # חישובי ממוצעים (וידוא שהם על עמודת Close)
    data['SMA200'] = data['Close'].rolling(200).mean()
    data['SMA50'] = data['Close'].rolling(50).mean()
    data['SMA20'] = data['Close'].rolling(20).mean()
    data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()

    end_date = data.index[-1]
    start_date = end_date - timedelta(days=90)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Price'), row=1, col=1)
    
    colors = {'SMA200': '#ff1744', 'SMA50': '#00e676', 'SMA20': '#ff9100', 'EMA20': '#00e5ff'}
    for ma in ['SMA200', 'SMA50', 'SMA20', 'EMA20']:
        if opts.get(ma.replace("SMA", "SMA ").replace("EMA", "EMA ")):
            fig.add_trace(go.Scatter(x=data.index, y=data[ma], line=dict(color=colors[ma], width=1.5), name=ma), row=1, col=1)

    if opts["AVWAP"]:
        anchor = data.tail(120)['High'].idxmax()
        v_data = data[data.index >= anchor].copy()
        v_data['AVWAP'] = (((v_data['High']+v_data['Low']+v_data['Close'])/3) * v_data['Volume']).cumsum() / v_data['Volume'].cumsum()
        fig.add_trace(go.Scatter(x=v_data.index, y=v_data['AVWAP'], line=dict(color='#ffff00', width=2, dash='dot'), name='AVWAP'), row=1, col=1)

    vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=vol_colors, name='Volume'), row=2, col=1)

    fig.update_layout(height=650, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False)
    fig.update_xaxes(range=[start_date, end_date])
    
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div>Price</div><div class="metric-value">${data["Close"].iloc[-1]:.2f}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div>P/E</div><div class="metric-value">{fmt(info.get("trailingPE"))}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div>Market Cap</div><div class="metric-value">{fmt(info.get("marketCap",0)/1e9)}B</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div>Short %</div><div class="metric-value" style="color:#ff4b4b;">{fmt(info.get("shortPercentOfFloat"), True)}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div>Target</div><div class="metric-value">${fmt(info.get("targetMeanPrice"))}</div></div>', unsafe_allow_html=True)
        st.link_button(f"🔍 Fintel", f"https://fintel.io/so/us/{ticker.lower()}")

    st.markdown(f'<div class="company-info-box">{info.get("longBusinessSummary", "No data available.")}</div>', unsafe_allow_html=True)
else:
    st.error(f"Waiting for markets... Try refreshing or enter a different ticker (like AAPL).")