import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Global Market Cap Top 10 Dashboard",
    layout="wide"
)

st.title("🌎 Global Market Cap Top 10 Stocks")
st.caption("최근 1년 주가 수익률 비교")

stocks = {
    "NVIDIA": "NVDA",
    "Alphabet": "GOOGL",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Broadcom": "AVGO",
    "TSMC": "TSM",
    "Saudi Aramco": "2222.SR",
    "Tesla": "TSLA",
    "Meta": "META"
}

end_date = datetime.today()
start_date = end_date - timedelta(days=365)

@st.cache_data
def load_data():
    price_df = pd.DataFrame()

    for name, ticker in stocks.items():
        data = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=True
        )

        if not data.empty:
            price_df[name] = data["Close"]

    return price_df

prices = load_data()

# 시작점을 100으로 정규화
normalized = prices.div(prices.iloc[0]).mul(100)

fig = go.Figure()

for col in normalized.columns:
    fig.add_trace(
        go.Scatter(
            x=normalized.index,
            y=normalized[col],
            mode="lines",
            name=col,
            hovertemplate=
            "<b>%{fullData.name}</b><br>" +
            "%{x|%Y-%m-%d}<br>" +
            "수익률: %{y:.2f}%<extra></extra>"
        )
    )

fig.update_layout(
    height=700,
    template="plotly_white",
    title="최근 1년 주가 성과 비교 (시작값=100)",
    xaxis_title="Date",
    yaxis_title="Normalized Price",
    hovermode="x unified",
    legend_title="Company"
)

st.plotly_chart(fig, use_container_width=True)

# 성과 테이블
returns = (
    (prices.iloc[-1] / prices.iloc[0] - 1) * 100
).sort_values(ascending=False)

st.subheader("📈 최근 1년 수익률")

result_df = pd.DataFrame({
    "Company": returns.index,
    "Return (%)": returns.values.round(2)
})

st.dataframe(
    result_df,
    use_container_width=True,
    hide_index=True
)
