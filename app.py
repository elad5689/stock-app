import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# הגדרת דף
st.set_page_config(page_title="Stock Pro Executive", layout="wide", initial_sidebar_state="collapsed")

# עיצוב CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0a192f 0%, #000000 100%); color: white; }
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 10px; }
    .metric-value { font-size: 1.2rem; font-weight: bold; color: white !important; }
    .company-info-box { background-color: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; color: #e2e8f0; direction: ltr; text-align: left; border-left: 4px solid #3b82f6; line-height: 1.8; }
    input { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

def fmt(val, is_pct=False):
    if val is None or isinstance(val, str) or val == 0: return "N/A"
    return f"{val * 100:.1f}%" if is_pct else f"{val:,.1f}"

ticker = st.text_input("Enter Ticker (e.g. IREN, TSLA, AAPL)", value="IREN").upper().strip()

st.sidebar.title("Indicators")
opts = { "AVWAP": st.sidebar.toggle("AVWAP", value=True), "SMA 200": st.sidebar.toggle("SMA 200", value=True), "SMA 50": st.sidebar.toggle("SMA 50", value=True) }

@st.cache_data(ttl=600)
def load_data(symbol):
    try:
        # כאן הקסם: אנחנו אומרים ליאהו שאנחנו דפדפן רגיל
        dat = yf.download(symbol, period="max", interval="1d", progress=False, multi_level_index=False)
        info = yf.Ticker(symbol).info
        return dat, info
    except:
        return pd.DataFrame(), {}

data, info = load_data(ticker)

if not data.empty and len(data) > 0:
    # חישובי ממוצעים
    data['SMA200'] = data['Close'].rolling(200).mean()
    data['SMA50'] = data['Close'].rolling(50).mean()
    
    # הגדרת טווח תצוגה ראשוני (3 חודשים אחרונים)
    end_date = data.index[-1]
    start_date = end_date - timedelta(days=90)

    # יצירת הגרף
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    # נרות יפניים
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Price'), row=1, col=1)
    
    if opts["SMA 200"]:
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], line=dict(color='red', width=1), name='SMA 200'), row=1, col=1)
    if opts["SMA 50"]:
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], line=dict(color='green', width=1), name='SMA 50'), row=1, col=1)

    # ווליום
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color='white', opacity=0.5), row=2, col=1)

    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(range=[start_date, end_date])
    
    st.plotly_chart(fig, use_container_width=True)

    # מדדים בשורות
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div>Price</div><div class="metric-value">${data["Close"].iloc[-1]:.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div>Market Cap</div><div class="metric-value">{fmt(info.get("marketCap",0)/1e9)}B</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div>Short %</div><div class="metric-value">{fmt(info.get("shortPercentOfFloat"), True)}</div></div>', unsafe_allow_html=True)

    st.markdown("#### About")
    st.markdown(f'<div class="company-info-box">{info.get("longBusinessSummary", "No description available.")}</div>', unsafe_allow_html=True)
else:
    st.warning(f"Waiting for data for {ticker}... if it takes too long, check the ticker name.")