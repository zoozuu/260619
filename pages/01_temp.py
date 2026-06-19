import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

# ==================================================
# 페이지 설정
# ==================================================

st.set_page_config(
    page_title="Weather Globe",
    page_icon="🌍",
    layout="wide"
)

FILE_NAME = "ta_20260619190504.csv"

# ==================================================
# 서울 데이터 로드
# ==================================================

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
        except:
            continue

    if df is None:
        st.error("서울 기온 CSV를 읽을 수 없습니다.")
        st.stop()

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace('"', '')
    )

    date_col = None
    temp_col = None

    for col in df.columns:

        if ("날짜" in col) or ("일시" in col):
            date_col = col

        if "평균기온" in col:
            temp_col = col

    if date_col is None:
        st.error(f"날짜 컬럼을 찾을 수 없습니다.\n{df.columns.tolist()}")
        st.stop()

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

    df = df.dropna(
        subset=[date_col, temp_col]
    )

    return df, date_col, temp_col


seoul, date_col, temp_col = load_seoul_data()

# ==================================================
# 제목
# ==================================================

st.title("🌍 Weather Globe")

st.markdown("""
### 서울의 과거 날씨와 비교하는 세계 날씨 지구본

전 세계 주요 도시의 **실시간 기온**을 확인하고,
현재 날씨가 서울의 과거 어느 날과 가장 비슷한지 비교할 수 있습니다.

#### 사용 방법
- 🌎 지구본을 드래그하여 회전
- 📍 도시 마커에 마우스를 올리면 상세 정보 확인
- 🌡️ 현재 기온 확인
- 🇰🇷 서울과 가장 비슷한 날짜 확인
- 📊 기온 차이 확인
""")

# ==================================================
# 사이드바
# ==================================================

with st.sidebar:

    st.title("🌎 Weather Globe")

    st.markdown("""
    서울의 과거 기온 데이터를 활용하여
    전 세계 도시의 현재 날씨를 비교합니다.
    """)

    st.divider()

    st.subheader("📌 Hover 정보")

    st.markdown("""
    - 현재 기온
    - 서울 유사 날짜
    - 서울 기온
    - 기온 차이
    """)

    st.divider()

    st.caption(
        "Data: KMA + Open-Meteo"
    )

# ==================================================
# 도시 목록
# ==================================================

cities = [
    ("Seoul",37.5665,126.9780),
    ("Tokyo",35.6762,139.6503),
    ("Beijing",39.9042,116.4074),
    ("Shanghai",31.2304,121.4737),
    ("Bangkok",13.7563,100.5018),
    ("Singapore",1.3521,103.8198),
    ("Sydney",-33.8688,151.2093),
    ("London",51.5072,-0.1276),
    ("Paris",48.8566,2.3522),
    ("Berlin",52.5200,13.4050),
    ("Rome",41.9028,12.4964),
    ("Madrid",40.4168,-3.7038),
    ("Moscow",55.7558,37.6173),
    ("New York",40.7128,-74.0060),
    ("Chicago",41.8781,-87.6298),
    ("Los Angeles",34.0522,-118.2437),
    ("Toronto",43.6510,-79.3470),
    ("Mexico City",19.4326,-99.1332),
    ("Rio",-22.9068,-43.1729),
    ("Buenos Aires",-34.6037,-58.3816),
    ("Cape Town",-33.9249,18.4241),
    ("Cairo",30.0444,31.2357),
    ("Dubai",25.2048,55.2708),
    ("Mumbai",19.0760,72.8777),
]

# ==================================================
# 실시간 날씨
# ==================================================

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

# ==================================================
# KPI 카드
# ==================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "서울 데이터",
        f"{len(seoul):,}일"
    )

with col2:
    st.metric(
        "도시 수",
        len(weather)
    )

with col3:
    st.metric(
        "평균 기온",
        f"{weather['temp'].mean():.1f}°C"
    )

# ==================================================
# 서울 유사 날짜 찾기
# ==================================================

def find_similar(temp):

    idx = (
        seoul[temp_col] - temp
    ).abs().idxmin()

    row = seoul.loc[idx]

    return (
        row[date_col].strftime("%Y-%m-%d"),
        float(row[temp_col])
    )

similar_dates = []
similar_temps = []
diffs = []

for temp in weather["temp"]:

    d, t = find_similar(temp)

    similar_dates.append(d)
    similar_temps.append(round(t, 1))
    diffs.append(round(abs(temp - t), 1))

weather["서울유사날짜"] = similar_dates
weather["서울기온"] = similar_temps
weather["차이"] = diffs

# ==================================================
# 지구본
# ==================================================

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
            colorbar=dict(
                title="기온 (°C)"
            )
        ),
        customdata=np.stack(
            [
                weather["temp"],
                weather["서울유사날짜"],
                weather["서울기온"],
                weather["차이"]
            ],
            axis=1
        ),
        hovertemplate=
        "<b>%{text}</b><br><br>"
        "현재 기온: %{customdata[0]}°C<br>"
        "서울 유사 날짜: %{customdata[1]}<br>"
        "서울 기온: %{customdata[2]}°C<br>"
        "기온 차이: %{customdata[3]}°C"
        "<extra></extra>"
    )
)

fig.update_geos(
    projection_type="orthographic",
    showland=True,
    showocean=True,
    landcolor="rgb(80,120,80)",
    oceancolor="rgb(20,40,80)"
)

fig.update_layout(
    height=800,
    margin=dict(
        l=0,
        r=0,
        t=0,
        b=0
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==================================================
# 데이터 테이블
# ==================================================

st.subheader("📋 현재 세계 날씨")

st.dataframe(
    weather.sort_values("차이")
)
