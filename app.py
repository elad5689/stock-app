import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Pro Executive", layout="wide", initial_sidebar_state="collapsed")

# CSS מעודכן לתיקון צבעי טקסט ב-Sidebar ועיצוב כללי
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0a192f 0%, #000000 100%); color: white; }
    
    /* עיצוב ה-Sidebar - טקסט כהה על רקע בהיר */
    section[data-testid="stSidebar"] { background-color: #f1f5f9 !important; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label { 
        color: #1e293b !important; 
        font-weight: 600 !important;
    }

    /* עיצוב כרטיסי המדדים */
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 10px; }
    .metric-value { font-size: 1.2rem; font-weight: bold; color: white !important; }
    
    /* שורת חיפוש - טקסט כהה בפנים */
    .stTextInput input { color: #121212 !important; background-color: white !important; }
    
    /* כפתור פינטל */
    div.stLinkButton > a { background-color: #003366 !important; color: white !important; border: 1px solid #3b82f6 !important; border-radius: 8px !important; font-weight: bold !important; width: 100%; text-align: center; }
    
    .company-info-box { background-color: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; color: #e2e8f0; direction: ltr; text-align: left; border-left: 4px solid #3b82f6; line-height: 1.8; }
    </style>
    """, unsafe_allow_html=True)

def fmt(val, is_pct=False):
    if val is None or isinstance(val, str) or val == 0: return "N/A"
    return f"{val * 100:.1f}%" if is_pct else f"{val:,.1f}"

ticker = st.text_input("", value="IREN", placeholder="Enter Ticker...").upper().strip()

# תפריט צד מעודכן
st.sidebar.title("Indecators Settings")
opts = {
    "SMA 200": st.sidebar.toggle("SMA 200 (Red)", value=True),
    "SMA 50": st.sidebar.toggle("SMA 50 (Green)", value=True),
    "SMA 20": st.sidebar.toggle("SMA 20 (Orange)", value=True),
    "SMA 9": st.sidebar.toggle("SMA 9 (Blue)", value=True),
    "EMA 20": st.sidebar.toggle("EMA 20 (Cyan)", value=True),
    "AVWAP": st.sidebar.toggle("AVWAP (Yellow)", value=True)
}

@st.cache_data(ttl=300)
def load_data(symbol):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="2y")
        return df, t.info
    except:
        return pd.DataFrame(), {}

data, info = load_data(ticker)

if not data.empty and len(data) > 10:
    # חישובי אינדיקטורים
    data['SMA200'] = data['Close'].rolling(200).mean()
    data['SMA50'] = data['Close'].rolling(50).mean()
    data['SMA20'] = data['Close'].rolling(20).mean()
    data['SMA9'] = data['Close'].rolling(9).mean()
    data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()

    # יצירת הגרף
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
    
    # נרות יפניים
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Price'), row=1, col=1)
    
    # הוספת קווים לפי בחירה
    colors = {'SMA200': '#ff1744', 'SMA50': '#00e676', 'SMA20': '#ff9100', 'SMA9': '#2979ff', 'EMA20': '#00e5ff'}
    for ma in colors:
        label = ma.replace("SMA", "SMA ").replace("EMA", "EMA ")
        if opts.get(label):
            fig.add_trace(go.Scatter(x=data.index, y=data[ma], line=dict(color=colors[ma], width=1.5), name=label), row=1, col=1)

    # AVWAP
    if opts["AVWAP"]:
        anchor = data.tail(120)['High'].idxmax()
        v_data = data[data.index >= anchor].copy()
        v_data['AVWAP'] = (((v_data['High']+v_data['Low']+v_data['Close'])/3) * v_data['Volume']).cumsum() / v_data['Volume'].cumsum()
        fig.add_trace(go.Scatter(x=v_data.index, y=v_data['AVWAP'], line=dict(color='#ffff00', width=2, dash='dot'), name='AVWAP'), row=1, col=1)

    # ווליום
    vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=vol_colors, name='Volume'), row=2, col=1)

    # הגדרת טווחי זמן (Buttons)
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
            bgcolor="#0f172a", activecolor="#3b82f6", font=dict(color="white")
        )
    )
    
    # טווח ראשוני מוצג (3 חודשים)
    end_date = data.index[-1]
    start_date = end_date - timedelta(days=90)
    fig.update_xaxes(range=[start_date, end_date])

    fig.update_layout(height=650, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False)
    
    st.plotly_chart(fig, use_container_width=True)

    # נתונים פונדמנטליים
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div>Price</div><div class="metric-value">${data["Close"].iloc[-1]:.2f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div>Market Cap</div><div class="metric-value">{fmt(info.get("marketCap",0)/1e9)}B</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div>Short %</div><div class="metric-value" style="color:#ff4b4b;">{fmt(info.get("shortPercentOfFloat"), True)}</div></div>', unsafe_allow_html=True)

    st.link_button(f"🔍 Open Fintel Analysis", f"https://fintel.io/so/us/{ticker.lower()}")
    st.markdown(f'<div class="company-info-box">{info.get("longBusinessSummary", "No data available.")}</div>', unsafe_allow_html=True)
else:
    st.error("No data found. Try refreshing or check the ticker.")