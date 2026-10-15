import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인 (따뜻한 톤 레이아웃)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="전국 읍·면·동 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
)

st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.caption("최신 연도 데이터를 바탕으로 지역별 남녀 연령대 인구 구성을 확인합니다.")


# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 함수 (캐싱 적용으로 속도 최적화)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # GitHub 주소를 raw 파일 형태로 변환하여 판다스로 읽어옵니다.
    url = "https://github.com/doyunthegoat/population/raw/main/population_ts_yearly_gender.zip"

    # 판다스는 zip 압축 파일 형태의 CSV를 자동으로 해제하여 읽을 수 있습니다.
    df = pd.read_csv(url)

    # 데이터 내 가장 최신 연도만 추출합니다.
    latest_year = df["연도"].max()
    df_latest = df[df["연도"] == latest_year].copy()

    return df_latest, latest_year


# 데이터 로딩 상태 표시
with st.spinner("최신 인구 데이터를 불러오는 중입니다..."):
    df, latest_year = load_data()

st.success(f"기준 연도: **{latest_year}년** 최신 데이터 로드 완료")


# -----------------------------------------------------------------------------
# 3. 화면 상단 드롭다운 3개 (시도 → 시군구 → 동)
# -----------------------------------------------------------------------------
# 3개의 컬럼을 생성하여 드롭다운을 가로로 배치합니다.
col1, col2, col3 = st.columns(3)

with col1:
    # 1) 시도 선택
    sido_list = sorted(df["시도"].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

with col2:
    # 2) 선택된 시도에 해당하는 시군구 목록 필터링
    df_sido = df[df["시도"] == selected_sido]
    sigungu_list = sorted(df_sido["시군구"].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

with col3:
    # 3) 선택된 시군구에 해당하는 동 목록 필터링
    df_sigungu = df_sido[df_sido["시군구"] == selected_sigungu]
    dong_list = sorted(df_sigungu["동"].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# 선택한 행 추출
selected_row = df_sigungu[df_sigungu["동"] == selected_dong].iloc[0]


# -----------------------------------------------------------------------------
# 4. 연령대 라벨 및 남/여 인구 데이터 정리
# -----------------------------------------------------------------------------
# '0세'부터 '99세'까지 그리고 '100세 이상' 라벨 목록을 순서대로 작성합니다.
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

# 열 이름 형식('남_0세', '여_0세' ...)에 맞추어 데이터 추출
male_cols = [f"남_{age}" for age in age_labels]
female_cols = [f"여_{age}" for age in age_labels]

# 남성 인구수는 왼쪽 배치를 위해 음수(-1 곱함)로 처리
male_counts = [-int(selected_row[col]) for col in male_cols]
# 여성 인구수는 오른쪽 배치를 위해 양수 그대로 유지
female_counts = [int(selected_row[col]) for col in female_cols]


# -----------------------------------------------------------------------------
# 5. Plotly 가로 막대그래프(인구 피라미드) 생성
# -----------------------------------------------------------------------------
fig = go.Figure()

# 따뜻한 톤 색상 설정
COLOR_MALE = "#E07A5F"  # 따뜻한 테라코타/주황
COLOR_FEMALE = "#F28482"  # 따뜻한 코랄/로즈 핑크

# [남성 막대 그래프] - 왼쪽(음수값)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=male_counts,
        name="남자",
        orientation="h",
        marker=dict(color=COLOR_MALE),
        # 마우스 호버 시 절댓값(양수)으로 인구수 표시
        hovertemplate="<b>%{y}</b> (남성): %{customdata:,}명<extra></extra>",
        customdata=[-val for val in male_counts],  # 음수를 양수로 변환하여 전달
    )
)
