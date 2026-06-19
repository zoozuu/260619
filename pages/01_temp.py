import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="서울 날씨 비교 지구본",
    layout="wide"
)

# ----------------------------
# 서울 기온 데이터 로드
# ----------------------------
@st.cache_data
def load_seoul_data():

    df = pd.read_csv("ta_20260619190504(1).csv")

    df["일시"] = (
        df["일시"]
        .astype(str)
        .str.replace("\t", "", regex=False)
    )

    df["날짜"] = pd.to_datetime(df["날짜"])

    df["월일"] = df["날짜"].dt.strftime("%m-%d")

    return df

seoul = load_seoul_data()

today_md = datetime.now().strftime("%m-%d")

today_seoul = seoul[
    seoul["월일"] == today_md
]

seoul_avg_temp = today_seoul["평균기온(℃)"].mean()

# ----------------------------
# 주요 도시 목록
# ----------------------------
cities = [
    ("Seoul",37.5665,126.9780),
    ("Tokyo",35.6762,139.6503),
    ("Beijing",39.9042,116.4074),
    ("Bangkok",13.7563,100.5018),
    ("Singapore",1.3521,103.8198),
    ("Sydney",-33.8688,151.2093),
    ("London",51.5072,-0.1276),
    ("Paris",48.8566,2.3522),
    ("Berlin",52.52,13.405),
    ("Rome",41.9028,12.4964),
    ("Moscow",55.7558,37.6173),
    ("New York",40.7128,-74.0060),
    ("Chicago",41.8781,-87.6298),
    ("Los Angeles",34.0522,-118.2437),
    ("Mexico City",19.4326,-99.1332),
    ("Toronto",43.651,-79.347),
    ("Rio",-22.9068,-43.1729),
    ("Buenos Aires",-34.6037,-58.3816),
    ("Cape Town",-33.9249,18.4241),
    ("Cairo",30.0444,31.2357),
    ("Dubai",25.2048,55.2708),
    ("Mumbai",19.0760,72.8777),
]

# ----------------------------
# 실시간 날씨
# ----------------------------
@st.cache_data(ttl=1800)
def get_weather():

    rows = []

    for city, lat, lon in cities:

        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}"
            f"&longitude={lon}"
            "&current=temperature_2m"
        )

        try:
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

# ----------------------------
# 서울과 가장 비슷한 날 찾기
# ----------------------------
def find_similar_seoul_weather(temp):

    idx = (
        seoul["평균기온(℃)"] - temp
    ).abs().idxmin()

    row = seoul.loc[idx]

    return (
        row["날짜"].strftime("%Y-%m-%d"),
        row["평균기온(℃)"]
    )

dates = []
temps = []
diffs = []

for t in weather["temp"]:

    d, stemp = find_similar_seoul_weather(t)

    dates.append(d)
    temps.append(round(stemp,1))
    diffs.append(round(abs(stemp - t),1))

weather["서울유사날짜"] = dates
weather["서울기온"] = temps
weather["차이"] = diffs

# ----------------------------
# Globe
# ----------------------------
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
                title="°C"
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
        "<b>%{text}</b><br>"
        "현재 기온: %{customdata[0]}°C<br>"
        "서울과 비슷한 날: %{customdata[1]}<br>"
        "서울 기온: %{customdata[2]}°C<br>"
        "차이: %{customdata[3]}°C"
        "<extra></extra>"
    )
)

fig.update_geos(
    projection_type="orthographic",
    showland=True,
    landcolor="rgb(20,40,80)",
    showocean=True,
    oceancolor="rgb(0,30,60)"
)

fig.update_layout(
    height=800,
    margin=dict(
        l=0,
        r=0,
        t=40,
        b=0
    )
)

# ----------------------------
# 화면
# ----------------------------
st.title("🌎 서울 날씨 비교 지구본")

st.metric(
    "오늘 서울 과거평균 기온",
    f"{seoul_avg_temp:.1f}°C"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.dataframe(
    weather.sort_values(
        "차이"
    )
)
