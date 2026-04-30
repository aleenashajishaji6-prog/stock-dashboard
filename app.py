import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 Real-Time Stock Market Dashboard")
st.markdown("---")

# Sidebar
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Enter Stock Ticker", value="AAPL").upper()
period = st.sidebar.selectbox("Select Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=1)
interval = st.sidebar.selectbox("Select Interval", ["1d", "1wk", "1mo"], index=0)
auto_refresh = st.sidebar.checkbox("Auto Refresh (60s)", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("### Popular Tickers")
st.sidebar.markdown("AAPL, TSLA, GOOGL, MSFT, AMZN, META, NVDA")

# Fetch data
@st.cache_data(ttl=60)
def get_stock_data(ticker, period, interval):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    info = stock.info
    return df, info

try:
    with st.spinner(f"Fetching data for {ticker}..."):
        df, info = get_stock_data(ticker, period, interval)

    if df.empty:
        st.error(f"No data found for ticker '{ticker}'. Please check the symbol.")
        st.stop()

    # Calculate indicators
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['Change'] = df['Close'].diff()
    df['Change%'] = df['Close'].pct_change() * 100

    # Current values
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100
    volume = df['Volume'].iloc[-1]
    high_52w = df['High'].max()
    low_52w = df['Low'].min()

    # Company name
    company_name = info.get('longName', ticker)
    st.subheader(f"{company_name} ({ticker})")

    # Metric cards
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Current Price", f"${current_price:.2f}",
                f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
    col2.metric("Volume", f"{int(volume):,}")
    col3.metric("52W High", f"${high_52w:.2f}")
    col4.metric("52W Low", f"${low_52w:.2f}")
    col5.metric("Data Points", len(df))

    st.markdown("---")

    # Main chart — candlestick + moving averages + volume
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3]
    )

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ), row=1, col=1)

    # MA20 line
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MA20'],
        line=dict(color='#FFA500', width=1.5),
        name='MA 20'
    ), row=1, col=1)

    # MA50 line
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MA50'],
        line=dict(color='#1E90FF', width=1.5),
        name='MA 50'
    ), row=1, col=1)

    # Volume bars
    colors = ['#26a69a' if c >= o else '#ef5350'
              for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        name='Volume',
        marker_color=colors,
        opacity=0.7
    ), row=2, col=1)

    fig.update_layout(
        title=f"{ticker} Price Chart",
        xaxis_rangeslider_visible=False,
        height=600,
        template='plotly_dark',
        legend=dict(orientation='h', y=1.02),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Recent data table
    st.subheader("Recent Data")
    recent = df[['Open', 'High', 'Low', 'Close', 'Volume', 'Change%']].tail(10).copy()
    recent = recent.round(2)
    recent.index = recent.index.strftime('%Y-%m-%d')
    recent['Volume'] = recent['Volume'].astype(int)
    st.dataframe(recent, use_container_width=True)

    # Auto refresh
    if auto_refresh:
        st.info("Auto-refresh is ON. Page refreshes every 60 seconds.")
        time.sleep(60)
        st.rerun()

    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.info("Please check your ticker symbol and try again.")