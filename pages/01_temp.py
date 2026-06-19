import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go

st.set_page_config(
    page_title="세계 날씨 vs 서울",
    layout="wide"
)

st.title("🌎 전 세계 날씨와 서울 날씨 비교")

# ------------------------
# 서울 기온 데이터 로드
# ------------------------
@st.cache_data
def load_seoul_data():

    FILE_NAME = "ta_20260619190504.csv"   # 실제 파일명으로 수정

    df = pd.read_csv(
        FILE_NAME,
        sep="\t",
        encoding="cp949"
    )

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace('"', '')
    )

    # 컬럼명 자동 탐색
    date_col = None
    temp_col = None

    for col in df.columns:

        if "날짜" in col or "일시" in col:
            date_col = col

        if "평균기온" in col:
            temp_col = col

    if date_col is None:
        st.error(f"날짜 컬럼을 찾을 수 없음: {df.columns.tolist()}")
        st.stop()

    if temp_col is None:
        st.error(f"평균기온 컬럼을 찾을 수 없음: {df.columns.tolist()}")
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

    df = df.dropna(subset=[date_col])

    df[temp_col] = pd.to_numeric(
        df[temp_col],
        errors="coerce"
    )

    df["월일"] = df[date_col].dt.strftime("%m-%d")

    return df, date_col, temp_col


seoul, date_col, temp_col = load_seoul_data()

# ------------------------
# 전 세계 주요 도시
# ------------------------
cities = [
    ("Seoul",37.56,126.97),
    ("Tokyo",35.68,139.76),
    ("Beijing",39.90,116.40),
    ("Shanghai",31.23,121.47),
    ("Hong Kong",22.31,114.17),
    ("Bangkok",13.75,100.50),
    ("Singapore",1.35,103.82),
    ("Sydney",-33.86,151.21),
    ("London",51.50,-0.12),
    ("Paris",48.85,2.35),
    ("Berlin",52.52,13.40),
    ("Rome",41.90,12.49),
    ("Madrid",40.41,-3.70),
    ("Moscow",55.75,37.61),
    ("Dubai",25.20,55.27),
    ("Mumbai",19.07,72.87),
    ("Cairo",30.04,31.23),
    ("Cape Town",-33.92,18.42),
    ("New York",40.71,-74.00),
    ("Chicago",41.87,-87.62),
    ("Los Angeles",34.05,-118.24),
    ("Toronto",43.65,-79.38),
    ("Mexico City",19.43,-99.13),
    ("Rio",-22.90,-43.17),
    ("Buenos Aires",-34.60,-58.38),
]

# ------------------------
# Open-Meteo 실시간 날씨
# ------------------------
@st.cache_data(ttl=1800)
def get_weather():

    data = []

    for city, lat, lon in cities:

        try:

            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}"
                f"&longitude={lon}"
                f"&current=temperature_2m"
            )

            response = requests.get(
                url,
                timeout=10
            )

            temp = response.json()["current"]["temperature_2m"]

            data.append(
                {
                    "city": city,
                    "lat": lat,
                    "lon": lon,
                    "temp": temp
                }
            )

        except:
            pass

    return pd.DataFrame(data)

weather = get_weather()

# ------------------------
# 서울에서 가장 비슷한 날 찾기
# ------------------------
def find_similar_day(temp):

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

    date, seoul_temp = find_similar_day(temp)

    similar_dates.append(date)
    similar_temps.append(round(seoul_temp, 1))
    diffs.append(round(abs(temp - seoul_temp), 1))

weather["서울유사날짜"] = similar_dates
weather["서울기온"] = similar_temps
weather["차이"] = diffs

# ------------------------
# Plotly Globe
# ------------------------
fig = go.Figure()

fig.add_trace(
    go.Scattergeo(
        lon=weather["lon"],
        lat=weather["lat"],
        text=weather["city"],
        mode="markers",
        marker=dict(
            size=10,
            color=weather["temp"],
            colorscale="Turbo",
            colorbar=dict(
                title="현재기온"
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
        "현재기온: %{customdata[0]}°C<br>"
        "서울과 가장 비슷한 날: %{customdata[1]}<br>"
        "그날 서울 기온: %{customdata[2]}°C<br>"
        "차이: %{customdata[3]}°C"
        "<extra></extra>"
    )
)

fig.update_geos(
    projection_type="orthographic",
    showland=True,
    landcolor="rgb(60,100,60)",
    showocean=True,
    oceancolor="rgb(20,40,100)"
)

fig.update_layout(
    height=850,
    margin=dict(
        l=0,
        r=0,
        t=20,
        b=0
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.subheader("현재 도시별 날씨")

st.dataframe(
    weather.sort_values("차이")
)
