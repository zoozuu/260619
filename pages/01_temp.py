import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="세계 날씨 vs 서울", layout="wide")

FILE_NAME = "ta_20260619190504.csv"

@st.cache_data
def load_seoul_data():

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp949",
        "euc-kr"
    ]

    df = None

    for enc in encodings:
        try:
            df = pd.read_csv(
                FILE_NAME,
                sep=None,
                engine="python",
                encoding=enc
            )
            break

        except Exception:
            continue

    if df is None:
        st.error("CSV 파일을 읽을 수 없습니다.")
        st.stop()

    df.columns = (
        df.columns.astype(str)
        .str.replace('"', '')
        .str.strip()
    )

    # 날짜 컬럼 찾기
    date_col = None
    for col in df.columns:
        if "날짜" in col or "일시" in col:
            date_col = col
            break

    if date_col is None:
        st.error(f"날짜 컬럼을 찾을 수 없습니다.\n{df.columns.tolist()}")
        st.stop()

    # 평균기온 컬럼 찾기
    temp_col = None
    for col in df.columns:
        if "평균기온" in col:
            temp_col = col
            break

    if temp_col is None:
        st.error(f"평균기온 컬럼을 찾을 수 없습니다.\n{df.columns.tolist()}")
        st.stop()

    df[date_col] = (
        df[date_col]
        .astype(str)
        .str.replace('"', '')
        .str.strip()
    )

    df[date_col] = pd.to_datetime(
        df[date_col],
        errors="coerce"
    )

    df[temp_col] = pd.to_numeric(
        df[temp_col],
        errors="coerce"
    )

    df = df.dropna(subset=[date_col, temp_col])

    return df, date_col, temp_col


seoul, date_col, temp_col = load_seoul_data()

st.success("서울 기온 데이터 로드 완료")
st.write(f"데이터 수: {len(seoul):,}건")

cities = [
    ("Seoul",37.5665,126.9780),
    ("Tokyo",35.6762,139.6503),
    ("London",51.5072,-0.1276),
    ("Paris",48.8566,2.3522),
    ("New York",40.7128,-74.0060),
    ("Sydney",-33.8688,151.2093),
    ("Bangkok",13.7563,100.5018),
]

@st.cache_data(ttl=1800)
def get_weather():

    rows = []

    for city, lat, lon in cities:

        try:
            url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}"
                f"&longitude={lon}"
                "&current=temperature_2m"
            )

            r = requests.get(url, timeout=10)
            temp = r.json()["current"]["temperature_2m"]

            rows.append({
                "city": city,
                "lat": lat,
                "lon": lon,
                "temp": temp
            })

        except:
            pass

    return pd.DataFrame(rows)

weather = get_weather()

def find_similar(temp):

    idx = (seoul[temp_col] - temp).abs().idxmin()

    row = seoul.loc[idx]

    return (
        row[date_col].strftime("%Y-%m-%d"),
        float(row[temp_col])
    )

similar_dates = []
similar_temps = []
diffs = []

for t in weather["temp"]:

    d, s = find_similar(t)

    similar_dates.append(d)
    similar_temps.append(round(s,1))
    diffs.append(round(abs(t-s),1))

weather["서울유사날짜"] = similar_dates
weather["서울기온"] = similar_temps
weather["차이"] = diffs

fig = go.Figure()

fig.add_trace(
    go.Scattergeo(
        lon=weather["lon"],
        lat=weather["lat"],
        text=weather["city"],
        mode="markers",
        marker=dict(
            size=12,
            color=weather["temp"],
            colorscale="Turbo",
            showscale=True
        ),
        customdata=np.stack([
            weather["temp"],
            weather["서울유사날짜"],
            weather["서울기온"],
            weather["차이"]
        ], axis=1),
        hovertemplate=
        "<b>%{text}</b><br>" +
        "현재 기온: %{customdata[0]}°C<br>" +
        "서울 유사 날짜: %{customdata[1]}<br>" +
        "서울 기온: %{customdata[2]}°C<br>" +
        "차이: %{customdata[3]}°C" +
        "<extra></extra>"
    )
)

fig.update_geos(
    projection_type="orthographic",
    showland=True,
    showocean=True
)

fig.update_layout(height=800)

st.plotly_chart(fig, use_container_width=True)
