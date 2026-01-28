import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Pro Executive", layout="wide", initial_sidebar_state="collapsed")

# CSS ממוקד: Sidebar בהיר עם טקסט כהה, שאר הדף יוקרתי
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0a192f 0%, #000000 100%); color: white; }
    
    /* עיצוב Sidebar - טקסט כהה על רקע אפרפר */
    section[data-testid="stSidebar"] { background-color: #cbd5e1 !important; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { 
        color: #0f172a !important; 
        font-weight: bold !important; 
    }
    
    .metric-card { background: rgba(255, 255, 255, 0.07); padding: 15px; border-radius: 12px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.1); }
    .stTextInput input { color: black !important; }
    div.stLinkButton > a { background-color: #003366 !important; color: white !important; width: 100%; text-align: center; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# קלט טיקר
ticker = st.text_input("", value="IREN", placeholder="Enter Ticker...").upper().strip()

# אינדיקטורים ב-Sidebar
st.sidebar.title("Chart Settings")
show_sma200 = st.sidebar.toggle("SMA 200 (Red)", value=True)
show_sma50 = st.sidebar.toggle("SMA 50 (Green)", value=True)
show_sma20 = st.sidebar.toggle("SMA 20 (Orange)", value=True)
show_sma9 = st.sidebar.toggle("SMA 9 (Blue)", value=True)
show_ema20 = st.sidebar.toggle("EMA 20 (Cyan)", value=True)
show_avwap = st.sidebar.toggle("AVWAP (Yellow)", value=True)

@st.cache_data(ttl=300)
def fetch_data(symbol):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="2y")
        return df, t.info
    except:
        return pd.DataFrame(), {}

data, info = fetch_data(ticker)

if not data.empty and len(data) > 10:
    # חישובים
    data['SMA200'] = data['Close'].rolling(200).mean()
    data['SMA50'] = data['Close'].rolling(50).mean()
    data['SMA20'] = data['Close'].rolling(20).mean()
    data['SMA9'] = data['Close'].rolling(9).mean()
    data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()

    # גרף
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Price'), row=1, col=1)

    # הוספת קווים
    ma_list = [
        (show_sma200, 'SMA200', '#ff1744'), (show_sma50, 'SMA50', '#00e676'),
        (show_sma20, 'SMA20', '#ff9100'), (show_sma9, 'SMA9', '#2979ff'),
        (show_ema20, 'EMA20', '#00e5ff')
    ]
    for show, col, color in ma_list:
        if show:
            fig.add_trace(go.Scatter(x=data.index, y=data[col], line=dict(color=color, width=1.5), name=col), row=1, col=1)

    # AVWAP
    if show_avwap:
        anchor = data.tail(120)['High'].idxmax()
        v_data = data[data.index >= anchor].copy()
        v_data['AVWAP'] = (((v_data['High']+v_data['Low']+v_data['Close'])/3) * v_data['Volume']).cumsum() / v_data['Volume'].cumsum()
        fig.add_trace(go.Scatter(x=v_data.index, y=v_data['AVWAP'], line=dict(color='#ffff00', width=2, dash='dot'), name='AVWAP'), row=1, col=1)

    # ווליום
    vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=vol_colors, name='Volume'), row=2, col=1)

    # טווחי זמן
    fig.update_xaxes(
        gridcolor='#1e293b',
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(step="all", label="MAX")
            ]),
            bgcolor="#1e293b", activecolor="#3b82f6", font=dict(color="white")
        )
    )
    
    # הגדרת תצוגה ראשונית ל-3 חודשים
    end_date = data.index[-1]
    start_date = end_date - timedelta(days=90)
    fig.update_xaxes(range=[start_date, end_date], xaxis_rangeslider_visible=False)
    fig.update_layout(height=700, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    
    st.plotly_chart(fig, use_container_width=True)

    # כרטיסים
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><div style="color:#94a3b8">Price</div><div style="font-size:20px; font-weight:bold;">${data["Close"].iloc[-1]:.2f}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div style="color:#94a3b8">Market Cap</div><div style="font-size:20px; font-weight:bold;">{info.get("marketCap",0)/1e9:.1f}B</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div style="color:#94a3b8">Short %</div><div style="font-size:20px; font-weight:bold; color:#ff4b4b;">{info.get("shortPercentOfFloat",0)*100:.1f}%</div></div>', unsafe_allow_html=True)

    st.write("")
    st.link_button(f"🔍 Open Fintel for {ticker}", f"https://fintel.io/so/us/{ticker.lower()}")
    st.markdown(f'<div style="background:rgba(255,255,255,0.03); padding:20px; border-radius:12px; text-align:left; direction:ltr;">{info.get("longBusinessSummary", "No description available.")}</div>', unsafe_allow_html=True)
else:
    st.warning("Data connection lost. Please type a ticker (e.g. AAPL) and press Enter.")