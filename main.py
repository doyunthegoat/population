import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="전국 읍·면·동 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
)

st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.caption("최신 연도 데이터를 바탕으로 지역별 남녀 연령대 인구 구성을 확인합니다.")


# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 및 최신 연도 필터링
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # GitHub 주소를 pandas가 직접 읽을 수 있는 raw URL 형태로 지정합니다.
    url = "https://raw.githubusercontent.com/doyunthegoat/population/main/population_ts_yearly_gender.zip"
    df = pd.read_csv(url)

    # 데이터 내 가장 최신 연도만 추출합니다.
    latest_year = df["연도"].max()
    df_latest = df[df["연도"] == latest_year].copy()

    return df_latest, latest_year


with st.spinner("최신 인구 데이터를 불러오는 중입니다..."):
    df, latest_year = load_data()

st.success(f"기준 연도: **{latest_year}년** 최신 데이터 로드 완료")


# -----------------------------------------------------------------------------
# 3. 화면 상단 드롭다운 3개 (시도 → 시군구 → 동)
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df["시도"].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

with col2:
    df_sido = df[df["시도"] == selected_sido]
    sigungu_list = sorted(df_sido["시군구"].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

with col3:
    df_sigungu = df_sido[df_sido["시군구"] == selected_sigungu]
    dong_list = sorted(df_sigungu["동"].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# 선택한 동네의 데이터 행 추출
selected_row = df_sigungu[df_sigungu["동"] == selected_dong].iloc[0]


# -----------------------------------------------------------------------------
# 4. 연령대 라벨 및 인구 통계 지표 계산
# -----------------------------------------------------------------------------
# '0세'부터 '99세'까지 그리고 '100세 이상' 라벨 목록
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]
ages_numeric = np.array(list(range(100)) + [100])  # 가중평균 계산용 수치 배열 (0 ~ 100)

male_cols = [f"남_{age}" for age in age_labels]
female_cols = [f"여_{age}" for age in age_labels]

# 남성/여성/연령별 합계 계산
male_counts = np.array([int(selected_row[col]) for col in male_cols])
female_counts = np.array([int(selected_row[col]) for col in female_cols])
total_by_age = male_counts + female_counts

# 1) 총인구
total_population = int(total_by_age.sum())

if total_population > 0:
    # 2) 평균연령 (연령 수치 x 해당 연령 인구수의 가중평균)
    avg_age = (ages_numeric * total_by_age).sum() / total_population

    # 3) 고령화율 (65세 이상 비율)
    elderly_pop = total_by_age[65:].sum()
    elderly_ratio = (elderly_pop / total_population) * 100

    # 4) 유소년 비율 (0세 ~ 14세 비율)
    child_pop = total_by_age[:15].sum()
    child_ratio = (child_pop / total_population) * 100
else:
    avg_age = 0.0
    elderly_ratio = 0.0
    child_ratio = 0.0


# -----------------------------------------------------------------------------
# 5. 그래프 위 주요 지표 카드 3개 표기
# -----------------------------------------------------------------------------
st.markdown("---")
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    st.metric(label="👥 총인구", value=f"{total_population:,} 명")

with m_col2:
    st.metric(label="🎂 평균연령", value=f"{avg_age:.1f} 세")

with m_col3:
    # 고령화율 20% 초과 시 주의 경고 표시 붙임 (초고령사회 기준)
    elderly_label = "👵 고령화율 (65세 이상)"
    if elderly_ratio >= 20.0:
        st.metric(
            label=f"{elderly_label} ⚠️ [초고령]",
            value=f"{elderly_ratio:.1f} %",
            delta="20% 초과 (주의)",
            delta_color="inverse",
        )
    else:
        st.metric(label=elderly_label, value=f"{elderly_ratio:.1f} %")

st.markdown("---")


# -----------------------------------------------------------------------------
# 6. Plotly 가로 막대그래프(인구 피라미드) 생성
# -----------------------------------------------------------------------------
fig = go.Figure()

# 차트용 남성 인구수는 음수 변환 (-1 곱함)
male_counts_plot = [-val for val in male_counts]

COLOR_MALE = "#E07A5F"   # 따뜻한 테라코타/주황
COLOR_FEMALE = "#F28482" # 따뜻한 코랄/로즈 핑크

# [남성 막대 그래프] - 왼쪽 (음수)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=male_counts_plot,
        name="남자",
        orientation="h",
        marker=dict(color=COLOR_MALE),
        hovertemplate="<b>%{y}</b> (남성): %{customdata:,}명<extra></extra>",
        customdata=male_counts,
    )
)

# [여성 막대 그래프] - 오른쪽 (양수)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=female_counts,
        name="여자",
        orientation="h",
        marker=dict(color=COLOR_FEMALE),
        hovertemplate="<b>%{y}</b> (여성): %{x:,}명<extra></extra>",
    )
)

# 좌우 대칭 범주용 최대값 계산
max_val = max(male_counts.max(), female_counts.max()) if total_population > 0 else 100
if max_val == 0:
    max_val = 100

fig.update_layout(
    title=dict(
