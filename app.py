import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from openai import OpenAI
from logos import DEFAULT_LOGO, STOCK_LOGOS
import os

st.set_page_config(page_title='Stock Dashboard', layout='wide')

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

        :root {
            --bg: #eef3f8;
            --panel: #ffffff;
            --ink: #0f1b2d;
            --muted: #5a6d89;
            --line: #cdd8e8;
            --bull: #0d9f6e;
            --bear: #d64545;
            --accent: #2673e8;
            --header: #091425;
        }

        .stApp {
            background:
                radial-gradient(900px 340px at -2% -15%, rgba(38, 115, 232, 0.12), transparent 65%),
                radial-gradient(900px 340px at 105% -18%, rgba(13, 159, 110, 0.11), transparent 65%),
                linear-gradient(180deg, #f7faff 0%, var(--bg) 100%);
            color: var(--ink);
            font-family: 'Space Grotesk', sans-serif;
        }

        .stApp p,
        .stApp span,
        .stApp label,
        .stApp li,
        .stApp div {
            color: var(--ink);
        }

        .block-container {
            padding-top: 1.2rem;
        }

        .market-header {
            margin-top: -1.2rem;
            margin-bottom: 1rem;
            border-radius: 0 0 16px 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background:
                linear-gradient(100deg, #081222, #0e1f38 55%, #0b2a44 100%);
            color: #e8f0ff;
            padding: 0.9rem 1rem;
            box-shadow: 0 10px 24px rgba(9, 20, 37, 0.25);
        }

        .market-header strong {
            color: #ffffff;
            letter-spacing: 0.04em;
        }

        .market-strip {
            display: grid;
            grid-template-columns: repeat(5, minmax(120px, 1fr));
            gap: 0.65rem;
            margin: 0.5rem 0 1rem;
        }

        .market-chip {
            border: 1px solid var(--line);
            background: var(--panel);
            border-radius: 12px;
            padding: 0.6rem 0.7rem;
            box-shadow: 0 6px 16px rgba(15, 27, 45, 0.06);
        }

        .chip-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-bottom: 0.22rem;
        }

        .chip-value {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1rem;
            font-weight: 600;
            color: var(--ink);
        }

        .stock-identity {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .stock-logo {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            border: 1px solid #d4deee;
            background: #ffffff;
            object-fit: contain;
            padding: 2px;
        }

        .chip-bull {
            color: var(--bull);
        }

        .chip-bear {
            color: var(--bear);
        }

        .chip-note {
            margin-top: 0.28rem;
            font-size: 0.76rem;
            font-weight: 600;
            color: var(--muted);
            font-family: 'IBM Plex Mono', monospace;
        }

        .note-bull {
            color: var(--bull);
        }

        .note-bear {
            color: var(--bear);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1628 0%, #11233d 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: #d7e6ff !important;
            font-weight: 600;
        }

        section[data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.98) !important;
            border: 1px solid rgba(255, 255, 255, 0.22) !important;
            border-radius: 10px !important;
            min-height: 42px;
        }

        section[data-testid="stSidebar"] [data-baseweb="select"] * {
            color: #152238 !important;
        }

        section[data-testid="stSidebar"] button[kind="header"] {
            background: #ffffff !important;
            border: 1px solid #d7e3f4 !important;
            border-radius: 12px !important;
        }

        section[data-testid="stSidebar"] button[kind="header"] svg,
        section[data-testid="stSidebar"] button[kind="header"] path {
            fill: #10284a !important;
            stroke: #10284a !important;
            opacity: 1 !important;
        }

        section[data-testid="stSidebar"] button[kind="header"]:hover {
            background: #f2f7ff !important;
        }

        section[data-testid="stSidebar"] button[kind="header"]:active,
        section[data-testid="stSidebar"] button[kind="header"]:focus,
        section[data-testid="stSidebar"] button[kind="header"]:focus-visible {
            background: #ffffff !important;
            border: 1px solid #c8d9f0 !important;
            box-shadow: 0 0 0 2px rgba(52, 119, 232, 0.25) !important;
            outline: none !important;
        }

        [data-testid="stMetric"] {
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 0.75rem;
            background: #fdfefe;
            box-shadow: 0 8px 18px rgba(9, 20, 37, 0.08);
        }

        [data-testid="stMetricLabel"] * {
            color: #4e6282 !important;
            font-weight: 600 !important;
        }

        [data-testid="stMetricValue"] * {
            color: #152238 !important;
            font-weight: 700 !important;
            opacity: 1 !important;
            text-shadow: 0 0 0 transparent;
        }

        [data-testid="stMetricDelta"] * {
            color: var(--bull) !important;
            font-weight: 600 !important;
            opacity: 1 !important;
        }

        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            color: var(--ink);
            letter-spacing: -0.2px;
        }

        [data-testid="stMarkdownContainer"] h1 {
            margin-top: 0.1rem;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 12px;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 8px 20px rgba(15, 27, 45, 0.07);
        }

        [data-testid="stDataFrame"] * {
            color: #152238 !important;
        }

        [data-testid="stDataFrame"] thead th {
            background: #e8eef9 !important;
            color: #132949 !important;
            font-weight: 700 !important;
        }

        [data-testid="stAlert"] {
            border-radius: 10px;
        }

        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 1px solid #aebed7;
            background: #ffffff;
            color: #152238;
        }

        .stTextInput > div > div > input:focus {
            border-color: #3477e8;
            box-shadow: 0 0 0 1px #3477e8;
        }

        .stTextInput > label {
            font-weight: 600;
            color: #21345c !important;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(140px, 1fr));
            gap: 0.7rem;
            margin: 0.4rem 0 0.9rem;
        }

        .summary-card {
            border: 1px solid var(--line);
            border-radius: 12px;
            background: linear-gradient(180deg, #ffffff, #f3f7ff);
            padding: 0.65rem 0.75rem;
            box-shadow: 0 6px 16px rgba(15, 27, 45, 0.07);
        }

        .summary-label {
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.7rem;
            color: var(--muted);
            margin-bottom: 0.2rem;
        }

        .summary-value {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1rem;
            font-weight: 700;
            color: var(--ink);
        }

        .summary-panel {
            border: 1px solid var(--line);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.96);
            padding: 0.45rem;
            box-shadow: 0 8px 20px rgba(15, 27, 45, 0.07);
        }

        .insight-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(180px, 1fr));
            gap: 0.7rem;
            margin: 0.2rem 0 1rem;
        }

        .insight-card {
            border-radius: 14px;
            padding: 0.75rem 0.85rem;
            border: 1px solid rgba(255, 255, 255, 0.25);
            box-shadow: 0 10px 22px rgba(15, 27, 45, 0.10);
        }

        .insight-bull {
            background: linear-gradient(135deg, #e8fff5 0%, #c8f6e1 100%);
            border-color: #8be0bc;
        }

        .insight-bear {
            background: linear-gradient(135deg, #fff0f0 0%, #ffd9d9 100%);
            border-color: #f1a8a8;
        }

        .insight-neutral {
            background: linear-gradient(135deg, #eef4ff 0%, #dbe9ff 100%);
            border-color: #a7c4f3;
        }

        .insight-title {
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #2a3c5d;
            margin-bottom: 0.28rem;
        }

        .insight-value {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.08rem;
            font-weight: 700;
            color: #0f1b2d;
            margin-bottom: 0.2rem;
        }

        .insight-note {
            font-size: 0.83rem;
            font-weight: 600;
            color: #2f466f;
            line-height: 1.25;
        }

        .overview-strip {
            display: grid;
            grid-template-columns: repeat(4, minmax(160px, 1fr));
            gap: 0.7rem;
            margin: 0.25rem 0 1rem;
        }

        .overview-pill {
            background: linear-gradient(120deg, #ffffff 0%, #f3f8ff 100%);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 0.55rem 0.72rem;
            box-shadow: 0 6px 14px rgba(15, 27, 45, 0.08);
        }

        .overview-label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-bottom: 0.14rem;
        }

        .overview-value {
            font-size: 0.98rem;
            font-weight: 700;
            color: var(--ink);
            font-family: 'IBM Plex Mono', monospace;
        }

        [data-testid="stVerticalBlock"] [data-testid="stElementContainer"] [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px;
            border-color: #cfdaec !important;
            background: linear-gradient(180deg, #ffffff 0%, #f7faff 100%);
            box-shadow: 0 8px 20px rgba(15, 27, 45, 0.07);
            padding: 0.15rem 0.15rem 0.25rem 0.15rem;
        }

        .section-kicker {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #5a7093;
            margin-bottom: -0.2rem;
            font-weight: 700;
        }

        .dashboard-footnote {
            margin-top: 0.8rem;
            color: #5a7093;
            font-size: 0.85rem;
            font-weight: 600;
        }

        [data-testid="stVerticalBlock"] h1 {
            font-size: 2.5rem;
            font-weight: 700;
        }

        [data-testid="stVerticalBlock"] h3 {
            font-size: 2rem;
            font-weight: 700;
        }

        @media (max-width: 900px) {
            .market-strip {
                grid-template-columns: repeat(2, minmax(120px, 1fr));
            }

            .overview-strip {
                grid-template-columns: repeat(2, minmax(120px, 1fr));
            }

            .insight-grid {
                grid-template-columns: repeat(1, minmax(180px, 1fr));
            }

            .summary-grid {
                grid-template-columns: repeat(2, minmax(120px, 1fr));
            }

            [data-testid="stMetric"] {
                min-height: 88px;
            }

            [data-testid="stVerticalBlock"] h1 {
                font-size: 2rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_col, title_col = st.columns([1, 12])
with logo_col:
    st.image('https://img.icons8.com/fluency/96/combo-chart.png', width=64)
with title_col:
    st.title('Stock Market Intelligence Dashboard')
st.subheader('NSE Stock Analytics — AI Powered')
st.markdown(
        """
        <div class='market-header'>
            <strong>NSE TERMINAL</strong> | Live historical analytics, momentum snapshots, and AI commentary
        </div>
        """,
        unsafe_allow_html=True,
)

# ── Database Connection ──
@st.cache_resource
def get_engine():
    password = quote_plus('Kar@+-2818')
    return create_engine(f'mysql+mysqlconnector://root:{password}@localhost/stock_analytics')


@st.cache_data
def load_fallback_csv_data():
    csv_df = pd.read_csv('stock_data_clean.csv')
    csv_df = csv_df.rename(
        columns={
            'Date': 'trade_date',
            'Stock': 'stock_name',
            'Open': 'open_price',
            'High': 'high_price',
            'Low': 'low_price',
            'Close': 'close_price',
            'Volume': 'volume',
        }
    )

    required_cols = {
        'trade_date',
        'stock_name',
        'open_price',
        'high_price',
        'low_price',
        'close_price',
        'volume',
    }
    missing_cols = required_cols - set(csv_df.columns)
    if missing_cols:
        raise ValueError(f'Missing required columns in CSV: {sorted(missing_cols)}')

    csv_df['trade_date'] = pd.to_datetime(csv_df['trade_date'])
    for col in ['open_price', 'high_price', 'low_price', 'close_price', 'volume']:
        csv_df[col] = pd.to_numeric(csv_df[col], errors='coerce')

    return csv_df

engine = None
all_data_df = None
data_source = 'database'

try:
    engine = get_engine()
    all_stocks_df = pd.read_sql('SELECT DISTINCT stock_name FROM stock_prices', engine)
except Exception:
    data_source = 'csv'
    all_data_df = load_fallback_csv_data()
    all_stocks_df = pd.DataFrame({'stock_name': sorted(all_data_df['stock_name'].dropna().unique())})
    st.info('Database is unreachable in this environment. Using bundled CSV data instead.')

stock_list = all_stocks_df['stock_name'].tolist()

if not stock_list:
    st.error("No data found in stock_prices table. Please run your load_to_mysql.py script first.")
    st.stop()

stock_list = sorted(stock_list)
st.sidebar.markdown('### Stocks')
stock = st.sidebar.radio('Stocks', stock_list, label_visibility='collapsed')
benchmark_choices = ['None'] + [s for s in stock_list if s != stock]
benchmark_stock = st.sidebar.selectbox('Compare With', benchmark_choices, index=0)
ma_window = st.sidebar.slider('Moving Average Window (days)', min_value=5, max_value=30, value=7)

selected_logo = STOCK_LOGOS.get(stock, DEFAULT_LOGO)

# ── Load Stock Data ──
if data_source == 'database':
    try:
        df = pd.read_sql(
            f"SELECT * FROM stock_prices WHERE stock_name='{stock}' ORDER BY trade_date",
            engine,
        )
    except Exception:
        data_source = 'csv'
        all_data_df = load_fallback_csv_data()
        st.info('Falling back to CSV because live database query failed.')

if data_source == 'csv':
    df = all_data_df[all_data_df['stock_name'] == stock].sort_values('trade_date').copy()

if df.empty:
    st.error(f"No data found for '{stock}'.")
    st.stop()

df['trade_date'] = pd.to_datetime(df['trade_date'])

min_date = df['trade_date'].min().date()
max_date = df['trade_date'].max().date()
default_start = (df['trade_date'].max() - pd.Timedelta(days=180)).date()
if default_start < min_date:
    default_start = min_date

date_range = st.sidebar.date_input(
    'Date Range',
    value=(default_start, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = min_date
    end_date = max_date

df = df[(df['trade_date'].dt.date >= start_date) & (df['trade_date'].dt.date <= end_date)].copy()
if df.empty:
    st.error('No records found in the selected date range. Please widen the window in the sidebar.')
    st.stop()

df['moving_avg'] = df['close_price'].rolling(ma_window).mean()
df['daily_return_pct'] = df['close_price'].pct_change() * 100

latest_close = float(df['close_price'].iloc[-1])
prev_close = float(df['close_price'].iloc[-2]) if len(df) > 1 else latest_close
day_change_pct = ((latest_close - prev_close) / prev_close * 100) if prev_close else 0.0
day_change_abs = latest_close - prev_close
avg_volume = float(df['volume'].mean())
seven_day_return = ((df['close_price'].iloc[-1] - df['close_price'].iloc[-7]) / df['close_price'].iloc[-7] * 100) if len(df) >= 7 else 0.0
thirty_day_return = ((df['close_price'].iloc[-1] - df['close_price'].iloc[-30]) / df['close_price'].iloc[-30] * 100) if len(df) >= 30 else 0.0
latest_volume = float(df['volume'].iloc[-1])
avg_volume_delta_pct = ((latest_volume - avg_volume) / avg_volume * 100) if avg_volume else 0.0

volatility = float(df['close_price'].std() / df['close_price'].mean() * 100)
window = min(30, len(df))
volatility_30d = float(df['close_price'].tail(window).std() / df['close_price'].tail(window).mean() * 100) if window > 1 else volatility
volatility_delta = volatility - volatility_30d

from_high_pct = (latest_close / float(df['close_price'].max()) - 1.0) * 100
from_low_pct = (latest_close / float(df['close_price'].min()) - 1.0) * 100
analysis_start = df['trade_date'].min().date()
analysis_end = df['trade_date'].max().date()
record_count = len(df)

day_class = 'chip-bull' if day_change_pct >= 0 else 'chip-bear'
r7_class = 'chip-bull' if seven_day_return >= 0 else 'chip-bear'
r30_class = 'chip-bull' if thirty_day_return >= 0 else 'chip-bear'
vol_class = 'note-bull' if avg_volume_delta_pct >= 0 else 'note-bear'

day_word = 'Increased' if day_change_pct >= 0 else 'Decreased'
r7_word = 'Increased' if seven_day_return >= 0 else 'Decreased'
vol_word = 'Above Avg' if avg_volume_delta_pct >= 0 else 'Below Avg'
day_arrow = '▲' if day_change_pct >= 0 else '▼'
r7_arrow = '▲' if seven_day_return >= 0 else '▼'
vol_arrow = '▲' if avg_volume_delta_pct >= 0 else '▼'

if seven_day_return > 0 and thirty_day_return > 0:
    momentum_text = 'Bullish Momentum'
    momentum_class = 'insight-bull'
elif seven_day_return < 0 and thirty_day_return < 0:
    momentum_text = 'Bearish Drift'
    momentum_class = 'insight-bear'
else:
    momentum_text = 'Mixed Momentum'
    momentum_class = 'insight-neutral'

if volatility >= 12:
    risk_text = 'High Risk'
    risk_note = 'Wide price swings observed'
    risk_class = 'insight-bear'
elif volatility >= 8:
    risk_text = 'Moderate Risk'
    risk_note = 'Controlled movement with pullbacks'
    risk_class = 'insight-neutral'
else:
    risk_text = 'Low Risk'
    risk_note = 'Relatively steady price behavior'
    risk_class = 'insight-bull'

if avg_volume_delta_pct > 8:
    activity_text = 'Strong Participation'
    activity_class = 'insight-bull'
elif avg_volume_delta_pct < -8:
    activity_text = 'Weak Participation'
    activity_class = 'insight-bear'
else:
    activity_text = 'Balanced Participation'
    activity_class = 'insight-neutral'

st.markdown(
        f"""
        <div class='market-strip'>
            <div class='market-chip'>
                <div class='chip-label'>Selected Stock</div>
                <div class='stock-identity'>
                    <img class='stock-logo' src='{selected_logo}' onerror="this.src='{DEFAULT_LOGO}'" />
                    <div class='chip-value'>{stock}</div>
                </div>
            </div>
            <div class='market-chip'><div class='chip-label'>Last Close</div><div class='chip-value'>Rs {latest_close:,.2f}</div></div>
            <div class='market-chip'>
                <div class='chip-label'>Day Change</div>
                <div class='chip-value {day_class}'>{day_arrow} {day_change_pct:+.2f}%</div>
                <div class='chip-note {day_class}'>{day_word} by Rs {abs(day_change_abs):.2f}</div>
            </div>
            <div class='market-chip'>
                <div class='chip-label'>7D Return</div>
                <div class='chip-value {r7_class}'>{r7_arrow} {seven_day_return:+.2f}%</div>
                <div class='chip-note {r7_class}'>{r7_word} in last 7 sessions</div>
            </div>
            <div class='market-chip'>
                <div class='chip-label'>Avg Volume</div>
                <div class='chip-value'>{avg_volume:,.0f}</div>
                <div class='chip-note {vol_class}'>{vol_arrow} {vol_word}: {avg_volume_delta_pct:+.2f}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
)

st.markdown(
        f"""
        <div class='overview-strip'>
            <div class='overview-pill'>
                <div class='overview-label'>Analysis Window</div>
                <div class='overview-value'>{start_date} to {end_date}</div>
            </div>
            <div class='overview-pill'>
                <div class='overview-label'>Rows Analyzed</div>
                <div class='overview-value'>{record_count:,}</div>
            </div>
            <div class='overview-pill'>
                <div class='overview-label'>30D Return</div>
                <div class='overview-value'>{thirty_day_return:+.2f}%</div>
            </div>
            <div class='overview-pill'>
                <div class='overview-label'>Price Range</div>
                <div class='overview-value'>Rs {df['close_price'].min():,.0f} - Rs {df['close_price'].max():,.0f}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
)

st.markdown('### Dashboard Insights')
st.markdown(
        f"""
        <div class='insight-grid'>
            <div class='insight-card {momentum_class}'>
                <div class='insight-title'>Momentum Signal</div>
                <div class='insight-value'>{momentum_text}</div>
                <div class='insight-note'>7D: {seven_day_return:+.2f}% | 30D: {thirty_day_return:+.2f}%</div>
            </div>
            <div class='insight-card {risk_class}'>
                <div class='insight-title'>Risk Signal</div>
                <div class='insight-value'>{risk_text}</div>
                <div class='insight-note'>{risk_note} (Volatility: {volatility:.2f}%)</div>
            </div>
            <div class='insight-card {activity_class}'>
                <div class='insight-title'>Volume Signal</div>
                <div class='insight-value'>{activity_text}</div>
                <div class='insight-note'>Latest vs Avg Volume: {avg_volume_delta_pct:+.2f}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
)

# ── KPI Cards ──
col1, col2, col3, col4 = st.columns(4)
col1.metric('Current Price', f'Rs {latest_close:.0f}', delta=f'{day_change_abs:+.2f} ({day_change_pct:+.2f}%)')
col2.metric('52-Week High', f'Rs {df.close_price.max():.0f}', delta=f'{from_high_pct:+.2f}% from current', delta_color='off')
col3.metric('52-Week Low', f'Rs {df.close_price.min():.0f}', delta=f'{from_low_pct:+.2f}% from current', delta_color='off')
col4.metric('Volatility', f'{volatility:.1f}%', delta=f'{volatility_delta:+.2f}% vs 30D')

# ── Price Chart with Moving Average ──
st.markdown("<div class='section-kicker'>Trend</div>", unsafe_allow_html=True)
price_container = st.container(border=True)
with price_container:
    st.subheader(f'{stock} Price Trend with {ma_window}-Day Moving Average')
    fig, ax = plt.subplots(figsize=(12, 4.6))
    fig.patch.set_facecolor('#f4f8ff')
    ax.set_facecolor('#fbfdff')

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(True, axis='y', linestyle='--', linewidth=0.8, alpha=0.24, color='#7d8ca4')
    ax.grid(False, axis='x')

    ax.plot(
        df['trade_date'],
        df['close_price'],
        color='#2b74ea',
        linewidth=2.6,
        label='Close Price',
        alpha=0.92,
    )
    ax.fill_between(df['trade_date'], df['close_price'], color='#2b74ea', alpha=0.10)

    ax.plot(
        df['trade_date'],
        df['moving_avg'],
        color='#f04f3f',
        linewidth=2.2,
        linestyle='-',
        label=f'{ma_window}-Day MA',
    )

    ax.scatter(df['trade_date'].iloc[-1], df['close_price'].iloc[-1], s=52, color='#2b74ea', zorder=4)
    ax.annotate(
        f"Rs {df['close_price'].iloc[-1]:.0f}",
        xy=(df['trade_date'].iloc[-1], df['close_price'].iloc[-1]),
        xytext=(12, 6),
        textcoords='offset points',
        fontsize=9,
        color='#1a315b',
        fontweight='bold',
    )

    date_locator = mdates.AutoDateLocator(minticks=5, maxticks=8)
    ax.xaxis.set_major_locator(date_locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(date_locator))

    ax.tick_params(axis='both', colors='#314b70', labelsize=10)
    ax.set_xlabel('Date', color='#243b5d', fontsize=10)
    ax.set_ylabel('Price (Rs)', color='#243b5d', fontsize=10)
    ax.legend(frameon=False, loc='upper right', fontsize=10)
    plt.tight_layout()
    st.pyplot(fig)

    if benchmark_stock != 'None':
        if data_source == 'database':
            benchmark_df = pd.read_sql(
                f"SELECT * FROM stock_prices WHERE stock_name='{benchmark_stock}' ORDER BY trade_date",
                engine,
            )
        else:
            benchmark_df = all_data_df[all_data_df['stock_name'] == benchmark_stock].sort_values('trade_date').copy()

        benchmark_df['trade_date'] = pd.to_datetime(benchmark_df['trade_date'])
        benchmark_df = benchmark_df[
            (benchmark_df['trade_date'].dt.date >= start_date)
            & (benchmark_df['trade_date'].dt.date <= end_date)
        ].copy()

        if not benchmark_df.empty:
            base_a = float(df['close_price'].iloc[0])
            base_b = float(benchmark_df['close_price'].iloc[0])
            if base_a and base_b:
                norm_a = (df['close_price'] / base_a) * 100
                norm_b = (benchmark_df['close_price'] / base_b) * 100

                st.caption(f'Indexed Performance Comparison: {stock} vs {benchmark_stock} (Base = 100)')
                fig_cmp, ax_cmp = plt.subplots(figsize=(12, 3.8))
                fig_cmp.patch.set_facecolor('#f4f8ff')
                ax_cmp.set_facecolor('#fbfdff')

                for spine in ax_cmp.spines.values():
                    spine.set_visible(False)

                ax_cmp.plot(df['trade_date'], norm_a, color='#2b74ea', linewidth=2.2, label=stock)
                ax_cmp.plot(benchmark_df['trade_date'], norm_b, color='#0ea371', linewidth=2.2, label=benchmark_stock)
                ax_cmp.axhline(100, color='#7d8ca4', linestyle='--', linewidth=1.2, alpha=0.6)
                ax_cmp.grid(True, axis='y', linestyle='--', linewidth=0.7, alpha=0.2)
                ax_cmp.xaxis.set_major_locator(date_locator)
                ax_cmp.xaxis.set_major_formatter(mdates.ConciseDateFormatter(date_locator))
                ax_cmp.set_ylabel('Indexed Price', color='#243b5d', fontsize=10)
                ax_cmp.legend(frameon=False, loc='upper left', fontsize=10)
                plt.tight_layout()
                st.pyplot(fig_cmp)

# ── Volume Chart ──
st.markdown("<div class='section-kicker'>Liquidity</div>", unsafe_allow_html=True)
volume_container = st.container(border=True)
with volume_container:
    st.subheader('Trading Volume')
    fig2, ax2 = plt.subplots(figsize=(12, 3.6))
    fig2.patch.set_facecolor('#f4f8ff')
    ax2.set_facecolor('#fbfdff')

    for spine in ax2.spines.values():
        spine.set_visible(False)

    ax2.grid(True, axis='y', linestyle='--', linewidth=0.8, alpha=0.2, color='#7d8ca4')
    ax2.grid(False, axis='x')

    volume_colors = df['close_price'].diff().fillna(0).ge(0).map({True: '#0ea371', False: '#db4b4b'})
    ax2.bar(df['trade_date'], df['volume'], color=volume_colors, alpha=0.72, width=1.4)
    ax2.axhline(df['volume'].mean(), color='#ed5151', linestyle='--', linewidth=1.8, label='Avg Volume')

    ax2.yaxis.set_major_formatter(
        FuncFormatter(lambda x, _: f"{x/1_000_000:.1f}M" if x >= 1_000_000 else f"{x/1_000:.0f}K")
    )
    ax2.xaxis.set_major_locator(date_locator)
    ax2.xaxis.set_major_formatter(mdates.ConciseDateFormatter(date_locator))

    ax2.tick_params(axis='both', colors='#314b70', labelsize=10)
    ax2.legend(frameon=False, loc='upper right', fontsize=10)
    ax2.set_xlabel('Date', color='#243b5d', fontsize=10)
    ax2.set_ylabel('Volume', color='#243b5d', fontsize=10)
    plt.tight_layout()
    st.pyplot(fig2)

st.markdown("<div class='section-kicker'>Return Diagnostics</div>", unsafe_allow_html=True)
diag_container = st.container(border=True)
with diag_container:
    st.subheader('Daily Return Distribution and Regime Signals')
    valid_returns = df['daily_return_pct'].dropna()

    up_days = int((valid_returns > 0).sum())
    down_days = int((valid_returns < 0).sum())
    flat_days = int((valid_returns == 0).sum())
    win_rate = (up_days / len(valid_returns) * 100) if len(valid_returns) else 0.0

    dcol1, dcol2, dcol3, dcol4 = st.columns(4)
    dcol1.metric('Up Days', f'{up_days}')
    dcol2.metric('Down Days', f'{down_days}')
    dcol3.metric('Flat Days', f'{flat_days}')
    dcol4.metric('Win Rate', f'{win_rate:.1f}%')

    if len(valid_returns) < 2:
        st.info('Not enough data points in selected range for return distribution.')
    else:
        fig3, ax3 = plt.subplots(figsize=(12, 3.6))
        fig3.patch.set_facecolor('#f4f8ff')
        ax3.set_facecolor('#fbfdff')
        for spine in ax3.spines.values():
            spine.set_visible(False)

        ax3.hist(valid_returns, bins=24, color='#2b74ea', alpha=0.72, edgecolor='#e9f0fb')
        ax3.axvline(valid_returns.mean(), color='#f04f3f', linewidth=2, linestyle='--', label='Mean Daily Return')
        ax3.axvline(0, color='#7d8ca4', linewidth=1.2, linestyle=':')
        ax3.grid(True, axis='y', linestyle='--', linewidth=0.8, alpha=0.2)
        ax3.set_xlabel('Daily Return (%)', color='#243b5d', fontsize=10)
        ax3.set_ylabel('Frequency', color='#243b5d', fontsize=10)
        ax3.legend(frameon=False, fontsize=9)
        plt.tight_layout()
        st.pyplot(fig3)

    st.markdown('#### Best and Worst Sessions')
    session_table = df[['trade_date', 'close_price', 'daily_return_pct']].copy()
    session_table['trade_date'] = session_table['trade_date'].dt.date
    best_days = session_table.nlargest(5, 'daily_return_pct')
    worst_days = session_table.nsmallest(5, 'daily_return_pct')
    t1, t2 = st.columns(2)
    with t1:
        st.caption('Top 5 Positive Days')
        st.dataframe(best_days.rename(columns={'trade_date': 'Date', 'close_price': 'Close', 'daily_return_pct': 'Return %'}), width='stretch')
    with t2:
        st.caption('Top 5 Negative Days')
        st.dataframe(worst_days.rename(columns={'trade_date': 'Date', 'close_price': 'Close', 'daily_return_pct': 'Return %'}), width='stretch')

st.markdown("<div class='section-kicker'>Monthly Momentum</div>", unsafe_allow_html=True)
monthly_container = st.container(border=True)
with monthly_container:
    st.subheader('Month-over-Month Close Return')
    monthly_close = df.set_index('trade_date')['close_price'].resample('M').last()
    monthly_return = (monthly_close.pct_change() * 100).dropna()
    monthly_return_df = monthly_return.reset_index()
    monthly_return_df.columns = ['Month', 'Monthly Return %']
    monthly_return_df['Month Label'] = monthly_return_df['Month'].dt.strftime('%b %Y')

    if monthly_return_df.empty:
        st.info('Not enough data points in selected range for monthly return analysis.')
    else:
        fig4, ax4 = plt.subplots(figsize=(12, 3.8))
        fig4.patch.set_facecolor('#f4f8ff')
        ax4.set_facecolor('#fbfdff')
        for spine in ax4.spines.values():
            spine.set_visible(False)

        month_colors = monthly_return_df['Monthly Return %'].ge(0).map({True: '#0ea371', False: '#db4b4b'})
        ax4.bar(monthly_return_df['Month Label'], monthly_return_df['Monthly Return %'], color=month_colors, alpha=0.85)
        ax4.axhline(0, color='#7d8ca4', linewidth=1.2)
        ax4.grid(True, axis='y', linestyle='--', linewidth=0.8, alpha=0.2)
        ax4.set_ylabel('Return (%)', color='#243b5d', fontsize=10)
        ax4.tick_params(axis='x', rotation=35, labelsize=9)
        plt.tight_layout()
        st.pyplot(fig4)

# ── Statistical Summary ──
st.markdown("<div class='section-kicker'>Descriptive Analytics</div>", unsafe_allow_html=True)
summary_container = st.container(border=True)
with summary_container:
    st.subheader('Statistical Summary')
    stats = df[['open_price', 'high_price', 'low_price', 'close_price', 'volume']].describe().round(2)

    summary_mean_close = float(df['close_price'].mean())
    summary_median_close = float(df['close_price'].median())
    summary_std_close = float(df['close_price'].std())
    summary_avg_vol = float(df['volume'].mean())

    st.markdown(
        f"""
        <div class='summary-grid'>
        <div class='summary-card'>
            <div class='summary-label'>Mean Close</div>
            <div class='summary-value'>Rs {summary_mean_close:,.2f}</div>
        </div>
        <div class='summary-card'>
            <div class='summary-label'>Median Close</div>
            <div class='summary-value'>Rs {summary_median_close:,.2f}</div>
        </div>
        <div class='summary-card'>
            <div class='summary-label'>Std Deviation</div>
            <div class='summary-value'>Rs {summary_std_close:,.2f}</div>
        </div>
        <div class='summary-card'>
            <div class='summary-label'>Average Volume</div>
            <div class='summary-value'>{summary_avg_vol:,.0f}</div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stats_table = stats.T
    stats_table.index = ['Open', 'High', 'Low', 'Close', 'Volume']

    formatted_stats = (
        stats_table.style
        .format(
            {
                'count': '{:,.0f}',
                'mean': '{:,.2f}',
                'std': '{:,.2f}',
                'min': '{:,.2f}',
                '25%': '{:,.2f}',
                '50%': '{:,.2f}',
                '75%': '{:,.2f}',
                'max': '{:,.2f}',
            }
        )
        .set_table_styles(
            [
                {
                    'selector': 'thead th',
                    'props': [
                        ('background-color', '#1b2a41'),
                        ('color', '#f4f7ff'),
                        ('font-weight', '700'),
                        ('border', '1px solid #314968'),
                    ],
                },
                {
                    'selector': 'tbody th',
                    'props': [
                        ('background-color', '#eff4ff'),
                        ('color', '#142743'),
                        ('font-weight', '700'),
                        ('border', '1px solid #d4deef'),
                    ],
                },
                {
                    'selector': 'tbody td',
                    'props': [
                        ('background-color', '#fbfdff'),
                        ('color', '#10233f'),
                        ('border', '1px solid #dce4f2'),
                    ],
                },
                {
                    'selector': 'tbody tr:nth-child(even) td',
                    'props': [('background-color', '#f4f8ff')],
                },
            ]
        )
    )

    st.markdown("<div class='summary-panel'>", unsafe_allow_html=True)
    st.dataframe(formatted_stats, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

# ── AI Chat Section ──
st.divider()
st.markdown("<div class='section-kicker'>Narrative</div>", unsafe_allow_html=True)
ai_container = st.container(border=True)
with ai_container:
    st.subheader('🤖 Ask the AI Analyst')

    client = OpenAI(
        api_key=os.getenv('GROQ_API_KEY'),
        base_url='https://api.groq.com/openai/v1'
    )

    SYSTEM_PROMPT = '''You are a senior equity analyst at a top investment bank.
You have access to stock price data for Indian NSE stocks.
Rules:
1. Always cite specific numbers from the data provided
2. Give 2-3 actionable insights, not vague statements
3. Compare the stock to its historical average when relevant
4. End with a risk disclaimer
5. Keep response under 150 words
Do NOT make future price predictions. Stick to historical analysis.'''

    safe_7d = seven_day_return if len(df) >= 7 else 0.0
    safe_30d = thirty_day_return if len(df) >= 30 else 0.0

    data_context = f'''
Stock: {stock}
Analysis Period: {df.trade_date.min().date()} to {df.trade_date.max().date()}
Current Price: Rs {df.close_price.iloc[-1]:.2f}
Range High: Rs {df.close_price.max():.2f}
Range Low: Rs {df.close_price.min():.2f}
Average Price: Rs {df.close_price.mean():.2f}
Price Volatility (CV): {df.close_price.std()/df.close_price.mean()*100:.2f}%
Average Daily Volume: {df.volume.mean():,.0f}
Recent 7-Day Return: {safe_7d:.2f}%
Recent 30-Day Return: {safe_30d:.2f}%
Win Rate: {(df['daily_return_pct'].dropna().gt(0).mean() * 100) if len(df['daily_return_pct'].dropna()) else 0.0:.2f}%
'''

    user_question = st.text_input('Ask about this stock...', placeholder='e.g. How has this stock performed recently?')

    if user_question:
        with st.spinner('Analyzing...'):
            candidate_models = [
                'llama-3.1-8b-instant',
                'llama-3.3-70b-versatile',
                'mixtral-8x7b-32768',
            ]
            last_error = None

            for model_name in candidate_models:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        max_tokens=300,
                        temperature=0.3,
                        messages=[
                            {'role': 'system', 'content': SYSTEM_PROMPT},
                            {'role': 'user', 'content': f'Data:\n{data_context}\n\nQuestion: {user_question}'}
                        ]
                    )
                    st.caption(f'Model used: {model_name}')
                    st.info(response.choices[0].message.content)
                    break
                except Exception as e:
                    last_error = e
            else:
                st.error(
                    f'AI unavailable: {last_error}. The configured model may be retired or your API key may be invalid.'
                )

st.markdown(
    "<div class='dashboard-footnote'>Insight colors are signal-based: green indicates strength, red indicates caution, and blue indicates neutral conditions.</div>",
    unsafe_allow_html=True,
)
