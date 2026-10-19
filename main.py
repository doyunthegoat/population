import json
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 스타일링
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="2026 전국 시군구 고령화 단계구분도",
    page_icon="🗺️",
    layout="wide",
)

st.title("🗺️ 2026년 전국 시군구 고령화 단계구분도")
st.caption(
    "전국 읍·면·동 인구 데이터를 바탕으로 시군구(5자리 코드 기준)별 65세 이상 고령화율(%)을 지도에 시각화합니다."
)


# -----------------------------------------------------------------------------
# 2. 데이터 및 GeoJSON 불러오기 (캐싱 적용)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 1) 인구 데이터 불러오기 (GitHub Raw URL)
    pop_url = "https://raw.githubusercontent.com/doyunthegoat/population/main/population_ts_yearly_gender.zip"
    df = pd.read_csv(pop_url)

    # 2026년 데이터만 선택
    df_2026 = df[df["연도"] == 2026].copy()

    # 동 코드(예: 1111051500)의 앞 5자리를 시군구 코드로 추출 (문자열 타입 처리)
    df_2026["코드5자리"] = (
        df_2026["코드"].astype(str).str.zfill(10).str[:5]
    )

    # '계_'로 시작하는 전체 나이 열 찾기
    total_cols = [c for c in df_2026.columns if c.startswith("계_")]

    # '계_65세'부터 '계_100세 이상'까지의 열 정순 추출
    age_labels = [f"계_{i}세" for i in range(65, 100)] + ["계_100세 이상"]
    elderly_cols = [c for c in age_labels if c in df_2026.columns]

    # 시군구(코드 5자리) 단위로 그룹화하여 인구 합계 계산
    grouped = df_2026.groupby("코드5자리", as_index=False).agg(
        total_pop=(
            total_cols[0],
            lambda x: df_2026.loc[x.index, total_cols].sum(axis=1).sum(),
        )
    )

    # 65세 이상 및 전체 인구 합산 계산
    df_2026["전체인구"] = df_2026[total_cols].sum(axis=1)
    df_2026["고령인구"] = df_2026[elderly_cols].sum(axis=1)

    df_sigungu = (
        df_2026.groupby("코드5자리", as_index=False)[
            ["전체인구", "고령인구"]
        ].sum()
    )

    # 시군구별 고령화율(%) 계산
    df_sigungu["고령화율"] = (
        df_sigungu["고령인구"] / df_sigungu["전체인구"]
    ) * 100
    df_sigungu["고령화율"] = df_sigungu["고령화율"].round(2)

    # 2) GeoJSON 시군구 경계 데이터 내려받기
    geojson_url = "https://raw.githubusercontent.com/doyunthegoat/population/main/sigungu_kr.geojson.txt"
    resp = requests.get(geojson_url)
    geojson_data = json.loads(resp.text)

    # GeoJSON 내부 속성에서 지역 이름 매핑 (시도, 시군구 이름)
    code_to_names = {}
    for feat in geojson_data["features"]:
        props = feat["properties"]
        code = str(props["코드"])
        sido_name = props.get("시도", "")
        sigungu_name = props.get("시군구", "")
        code_to_names[code] = f"{sido_name} {sigungu_name}".strip()

    df_sigungu["시군구명"] = df_sigungu["코드5자리"].map(code_to_names)

    return df_sigungu, geojson_data


with st.spinner("2026년 인구 데이터 및 시군구 지도를 로딩하는 중입니다..."):
    df_sigungu, geojson_data = load_data()

# -----------------------------------------------------------------------------
# 3. 주요 통계 카드 표기
# -----------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("총 분석 시군구", f"{len(df_sigungu)} 개")
with c2:
    st.metric(
        "전국 평균 고령화율",
        f"{(df_sigungu['고령인구'].sum() / df_sigungu['전체인구'].sum() * 100):.1f} %",
    )
with c3:
    max_row = df_sigungu.loc[df_sigungu["고령화율"].idxmax()]
    st.metric(
        "최고 고령화 지역",
        f"{max_row['시군구명']}",
        f"{max_row['고령화율']}%",
    )
with c4:
    min_row = df_sigungu.loc[df_sigungu["고령화율"].idxmin()]
    st.metric(
        "최저 고령화 지역",
        f"{min_row['시군구명']}",
        f"{min_row['고령화율']}%",
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. Plotly 단계구분도 (Choropleth) 지도 생성
# -----------------------------------------------------------------------------
# 지도 중심 및 확대율 기본값 설정
fig = px.choropleth_mapbox(
    df_sigungu,
    geojson=geojson_data,
    locations="코드5자리",  # 데이터 프레임의 연결 열
    featureidkey="properties.코드",  # GeoJSON 매핑 열 ('코드')
    color="고령화율",
    color_continuous_scale="Reds",  # 고령화율이 높을수록 진한 빨간색
    range_color=(
        df_sigungu["고령화율"].min(),
        df_sigungu["고령화율"].max(),
    ),
    mapbox_style="white-bg",  # 지도 타일(배경) 없이 경계만 표시
    center={"lat": 36.0, "lon": 127.8},  # 대한민국 중심점 좌표
    zoom=6.2,
    hover_name="시군구명",
    hover_data={"코드5자리": True, "고령화율": ":.2f%", "전체인구": ":,명"},
    labels={"고령화율": "고령화율 (%)", "코드5자리": "지역코드"},
)

# 호버 서식 및 레이아웃 커스텀
fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>코드: %{location}<br>고령화율: <b>%{z:.2f}%</b><extra></extra>"
)

fig.update_layout(
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    height=750,
    coloraxis_colorbar=dict(
        title="고령화율 (%)",
        ticksuffix="%",
        thickness=20,
        len=0.75,
    ),
)

st.plotly_chart(fig, use_container_width=True)
