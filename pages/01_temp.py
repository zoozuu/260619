import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go

st.set_page_config(
    page_title="세계 날씨 vs 서울",
    layout="wide"
)

st.title("🌎 세계 날씨와 서울 날씨 비교")

uploaded_file = st.file_uploader(
    "서울 기온 CSV 업로드",
    type=["csv"]
)

if uploaded_file is None:
    st.info("서울 기온 CSV를 업로드해주세요.")
    st.stop()


@st.cache_data
def load_seoul_data(file):

    # 여러 형식 시도
    try:
        df = pd.read_csv(file, sep="\t", encoding="cp949")
    except:
        file.seek(0)

        try:
            df = pd.read_csv(file, encoding="cp949")
        except:
            file.seek(0)
            df = pd.read_csv(file)

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace('"', '')
    )

    # 날짜 컬럼 찾기
    date_col = None

    for col in df.columns:
        if "날" in col or "일시" in col:
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

    df = df.dropna(subset=[date_col])

    df["월일"] = df[date_col].dt.strftime("%m-%d")

    return df, date_col, temp_col


seoul, date_col, temp_col = load_seoul_data(uploaded_file)

st.success("서울 기온 데이터 로드 완료")

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

def find_similar_seoul(temp):

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

    d, t = find_similar_seoul(temp)

    similar_dates.append(d)
    similar_temps.append(round(t, 1))
    diffs.append(round(abs(t-temp), 1))

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
            size=10,
            color=weather["temp"],
            colorscale="Turbo",
            colorbar=dict(
                title="현재기온(°C)"
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
        "<b>%{text}</b><br><br>" +
        "현재 기온: %{customdata[0]}°C<br>" +
        "서울과 비슷한 날짜: %{customdata[1]}<br>" +
        "그날 서울 기온: %{customdata[2]}°C<br>" +
        "차이: %{customdata[3]}°C" +
        "<extra></extra>"
    )
)

fig.update_geos(
    projection_type="orthographic",
    showland=True,
    landcolor="rgb(50,80,50)",
    showocean=True,
    oceancolor="rgb(10,30,80)"
)

fig.update_layout(
    height=800,
    margin=dict(
        l=0,
        r=0,
        t=30,
        b=0
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.subheader("현재 세계 날씨")

st.dataframe(
    weather.sort_values("차이")
)
