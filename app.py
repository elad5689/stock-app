import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from googletrans import Translator
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Pro Executive", layout="wide", initial_sidebar_state="collapsed")

# CSS - עיצוב הבר העליון, כפתור Fintel וניקוי ממשק
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0a192f 0%, #000000 100%); color: white; }
    header[data-testid="stHeader"] { background: linear-gradient(90deg, #0a192f 0%, #000000 100%) !important; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
    button[data-testid="stExpandSidebarButton"] { background-color: white !important; color: #0a192f !important; }
    h1, h2, h3, h4, span, label, p, .stCheckbox, .stToggleButton { color: white !important; }
    .stTextInput input { color: #121212 !important; background-color: white !important; border-radius: 8px !important; }
    section[data-testid="stSidebar"] { background-color: #f1f5f9 !important; }
    section[data-testid="stSidebar"] * { color: #121212 !important; }
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.1); }
    .metric-value { font-size: 1.2rem; font-weight: bold; color: white !important; }
    div.stLinkButton > a { background-color: #003366 !important; color: white !important; border: 1px solid #3b82f6 !important; border-radius: 8px !important; font-weight: bold !important; }
    div.stLinkButton > a:hover { background-color: #000000 !important; border-color: #ffffff !important; }
    .company-info-box { background-color: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; color: #e2e8f0; direction: rtl; text-align: right; border-right: 4px solid #3b82f6; line-height: 1.8; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def translate_text(text):
    if not text: return "אין תיאור זמין."
    try: return Translator().translate(text, dest='he').text
    except: return text

def fmt(val, is_pct=False):
    if val is None or isinstance(val, str) or val == 0: return "N/A"
    return f"{val * 100:.1f}%" if is_pct else f"{val:,.1f}"

ticker = st.text_input("", value="IREN", placeholder="הזן סימול מניה...").upper().strip()

st.sidebar.title("אינדיקטורים")
opts = { "AVWAP": st.sidebar.toggle("AVWAP", value=True), "SMA 200": st.sidebar.toggle("SMA 200", value=True), "SMA 50": st.sidebar.toggle("SMA 50", value=True), "SMA 20": st.sidebar.toggle("SMA 20", value=True), "EMA 20": st.sidebar.toggle("EMA 20", value=True), "EMA 5": st.sidebar.toggle("EMA 5", value=True) }

@st.cache_data(ttl=600)
def load_data(symbol):
    try:
        s = yf.Ticker(symbol)
        return s.history(period="max"), s.info
    except: return pd.DataFrame(), {}

data, info = load_data(ticker)

if not data.empty:
    data['SMA200'] = data['Close'].rolling(200).mean()
    data['SMA50'] = data['Close'].rolling(50).mean()
    data['SMA20'] = data['Close'].rolling(20).mean()
    data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
    data['EMA5'] = data['Close'].ewm(span=5, adjust=False).mean()

    end_date = data.index[-1]
    start_date = end_date - timedelta(days=90)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Price', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'), row=1, col=1)
    
    clrs = {'SMA200': '#ff1744', 'SMA50': '#00e676', 'SMA20': '#ff9100', 'EMA20': '#00e5ff', 'EMA5': '#007bff'}
    for ma in ['SMA200', 'SMA50', 'SMA20', 'EMA20', 'EMA5']:
        label = ma.replace("SMA", "SMA ").replace("EMA", "EMA ")
        if opts.get(label): fig.add_trace(go.Scatter(x=data.index, y=data[ma], line=dict(color=clrs[ma], width=1.5), name=label), row=1, col=1)

    if opts["AVWAP"]:
        anchor = data.tail(120)['High'].idxmax()
        v_data = data[data.index >= anchor].copy()
        v_data['AVWAP'] = (((v_data['High']+v_data['Low']+v_data['Close'])/3) * v_data['Volume']).cumsum() / v_data['Volume'].cumsum()
        fig.add_trace(go.Scatter(x=v_data.index, y=v_data['AVWAP'], line=dict(color='#ffff00', width=2, dash='dot'), name='AVWAP'), row=1, col=1)

    vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=vol_colors, name='Volume'), row=2, col=1)

    fig.update_xaxes(gridcolor='#1e293b', tickfont=dict(color="white"), range=[start_date, end_date], rangeselector=dict(buttons=list([dict(count=5, label="5D", step="day", stepmode="backward"), dict(count=1, label="1M", step="month", stepmode="backward"), dict(count=3, label="3M", step="month", stepmode="backward"), dict(count=6, label="6M", step="month", stepmode="backward"), dict(count=1, label="YTD", step="year", stepmode="todate"), dict(count=1, label="1Y", step="year", stepmode="backward"), dict(step="all", label="MAX")]), bgcolor="#0f172a", activecolor="#3b82f6", font=dict(color="white")))
    fig.update_layout(height=650, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#000000', xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified", legend=dict(font=dict(color="white", size=11)), font=dict(color="white"))
    fig.update_yaxes(gridcolor='#1e293b', tickfont=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div style="color:#94a3b8">מחיר</div><div class="metric-value">{data["Close"].iloc[-1]:.2f}$</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div style="color:#94a3b8">מכפיל P/E</div><div class="metric-value">{fmt(info.get("trailingPE"))}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div style="color:#94a3b8">שווי שוק</div><div class="metric-value">{fmt(info.get("marketCap",0)/1e9)}B</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div style="color:#94a3b8">מכפיל P/S</div><div class="metric-value">{fmt(info.get("priceToSalesTrailing12Months"))}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div style="color:#94a3b8">מחיר יעד (1Y)</div><div class="metric-value">{fmt(info.get("targetMeanPrice"))}$</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div style="color:#94a3b8">Short %</div><div class="metric-value" style="color:#ff4b4b;">{fmt(info.get("shortPercentOfFloat"), True)}</div></div>', unsafe_allow_html=True)

    st.write("")
    st.link_button(f"🔍 Open Fintel", f"https://fintel.io/so/us/{ticker.lower()}", use_container_width=True)
    st.write("---")
    st.markdown("#### 🏢 אודות החברה")
    with st.spinner('מתרגם...'):
        heb_desc = translate_text(info.get('longBusinessSummary', ''))
        st.markdown(f'<div class="company-info-box">{heb_desc}</div>', unsafe_allow_html=True)
else:
    st.error("לא נמצאו נתונים.")