import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px

st.set_page_config(
    page_title="🌎 Climate Time Machine",
    layout="wide"
)

st.title("🌎 Climate Time Machine")
st.caption("현재 전 세계 날씨를 서울의 과거 날씨와 비교합니다")

CSV_URL = "https://github.com/zoozuu/260619/blob/main/ta_20260619190504.csv"

# -------------------------------
# 서울 데이터 로드
# -------------------------------
@st.cache_data
def load_seoul_data():

    df = pd.read_csv(CSV_URL, encoding="utf-8")

    date_col = df.columns[0]
    mean_col = df.columns[2]

    df[date_col] = pd.to_datetime(df[date_col])

    df["year"] = df[date_col].dt.year

    yearly = (
        df.groupby("year")[mean_col]
        .mean()
        .reset_index()
        .rename(columns={mean_col: "avg_temp"})
    )

    return yearly


# -------------------------------
# 도시 목록
# -------------------------------
cities = [
    ("Seoul",37.5665,126.9780),
    ("Tokyo",35.6762,139.6503),
    ("Beijing",39.9042,116.4074),
    ("Shanghai",31.2304,121.4737),
    ("Bangkok",13.7563,100.5018),
    ("Singapore",1.3521,103.8198),
    ("Paris",48.8566,2.3522),
    ("London",51.5072,-0.1276),
    ("Berlin",52.5200,13.4050),
    ("Rome",41.9028,12.4964),
    ("Madrid",40.4168,-3.7038),
    ("New York",40.7128,-74.0060),
    ("Chicago",41.8781,-87.6298),
    ("Los Angeles",34.0522,-118.2437),
    ("Toronto",43.6532,-79.3832),
    ("Mexico City",19.4326,-99.1332),
    ("São Paulo",-23.5505,-46.6333),
    ("Buenos Aires",-34.6037,-58.3816),
    ("Sydney",-33.8688,151.2093),
    ("Melbourne",-37.8136,144.9631),
    ("Cape Town",-33.9249,18.4241),
]

# -------------------------------
# Open Meteo
# -------------------------------
@st.cache_data(ttl=3600)
def get_weather():

    results = []

    for city, lat, lon in cities:

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m"
        )

        try:
            r = requests.get(url, timeout=10).json()

            temp = r["current"]["temperature_2m"]

            results.append(
                {
                    "city": city,
                    "lat": lat,
                    "lon": lon,
                    "temp": temp
                }
            )

        except:
            pass

    return pd.DataFrame(results)

# -------------------------------
# 유사 연도 찾기
# -------------------------------
def find_similar_year(temp, seoul_yearly):

    idx = (seoul_yearly["avg_temp"] - temp).abs().idxmin()

    row = seoul_yearly.loc[idx]

    return int(row["year"]), round(row["avg_temp"], 1)

# -------------------------------
# 데이터
# -------------------------------
seoul_yearly = load_seoul_data()
weather_df = get_weather()

weather_df["similar_year"] = weather_df["temp"].apply(
    lambda x: find_similar_year(x, seoul_yearly)[0]
)

weather_df["similar_temp"] = weather_df["temp"].apply(
    lambda x: find_similar_year(x, seoul_yearly)[1]
)

# -------------------------------
# 지구본
# -------------------------------
fig = px.scatter_geo(
    weather_df,
    lat="lat",
    lon="lon",
    size=np.abs(weather_df["temp"]) + 5,
    color="temp",
    hover_name="city",
    hover_data={
        "temp": True,
        "similar_year": True,
        "lat": False,
        "lon": False,
    },
    projection="orthographic",
)

fig.update_layout(
    height=700,
    margin=dict(l=0, r=0, t=0, b=0),
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# 도시 선택
# -------------------------------
selected_city = st.selectbox(
    "도시 선택",
    weather_df["city"]
)

city_row = weather_df[
    weather_df["city"] == selected_city
].iloc[0]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "현재 기온",
        f"{city_row['temp']}°C"
    )

with col2:
    st.metric(
        "가장 유사한 서울",
        f"{int(city_row['similar_year'])}년"
    )

with col3:
    st.metric(
        "서울 평균기온",
        f"{city_row['similar_temp']}°C"
    )

st.info(
    f"""
📍 {selected_city}

현재 기온은 {city_row['temp']}°C 입니다.

서울의 과거 데이터와 비교했을 때
가장 비슷한 해는 **{int(city_row['similar_year'])}년** 입니다.
"""
)

# -------------------------------
# 랭킹
# -------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 가장 더운 도시")

    st.dataframe(
        weather_df
        .sort_values("temp", ascending=False)
        [["city","temp"]]
        .head(10),
        use_container_width=True
    )

with col2:
    st.subheader("🥶 가장 추운 도시")

    st.dataframe(
        weather_df
        .sort_values("temp")
        [["city","temp"]]
        .head(10),
        use_container_width=True
    )
