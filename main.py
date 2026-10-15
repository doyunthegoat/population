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
    # zip 압축 파일 형태의 CSV를 pandas가 자동으로 해제하여 읽어옵니다.
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

# 선택한 동네의 데이터 행 추출
selected_row = df_sigungu[df_sigungu["동"] == selected_dong].iloc[0]


# -----------------------------------------------------------------------------
# 4. 연령대 라벨 및 남/여 인구 데이터 추출
# -----------------------------------------------------------------------------
# '0세'부터 '99세'까지 그리고 '100세 이상' 라벨 목록을 정순(0세 -> 100세 이상)으로 만듭니다.
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

# 열 이름 형식('남_0세', '여_0세' ...)에 맞춰 열 이름 생성
male_cols = [f"남_{age}" for age in age_labels]
female_cols = [f"여_{age}" for age in age_labels]

# 남성 인구수는 피라미드 왼쪽에 배치하기 위해 음수로 변환 (-1 곱함)
male_counts = [-int(selected_row[col]) for col in male_cols]
# 여성 인구수는 피라미드 오른쪽에 배치하기 위해 양수 유지
female_counts = [int(selected_row[col]) for col in female_cols]


# -----------------------------------------------------------------------------
# 5. Plotly 가로 막대그래프(인구 피라미드) 생성
# -----------------------------------------------------------------------------
fig = go.Figure()

# 따뜻한 톤 색상 설정
COLOR_MALE = "#E07A5F"  # 따뜻한 테라코타/주황
COLOR_FEMALE = "#F28482"  # 따뜻한 코랄/로즈 핑크

# [남성 막대 그래프] - 왼쪽 (음수값)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=male_counts,
        name="남자",
        orientation="h",
        marker=dict(color=COLOR_MALE),
        # 마우스 호버 시 절댓값을 취해 양수로 표시
        hovertemplate="<b>%{y}</b> (남성): %{customdata:,}명<extra></extra>",
        customdata=[-val for val in male_counts],
    )
)

# [여성 막대 그래프] - 오른쪽 (양수값)
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


# -----------------------------------------------------------------------------
# 6. 세로축 순서 고정 및 레이아웃 설정
# -----------------------------------------------------------------------------
# x축 범위 대칭 설정을 위한 최대 인구수 계산
max_val = max(max([-x for x in male_counts]), max(female_counts))
if max_val == 0:
    max_val = 100

fig.update_layout(
    title=dict(
        text=f"<b>{selected_sido} {selected_sigungu} {selected_dong}</b> 인구 피라미드 ({latest_year}년)",
        font=dict(size=20, color="#3D405B"),
        x=0.5,
        xanchor="center",
    ),
    barmode="overlay",
    bargap=0.1,
    paper_bgcolor="#FAF8F5",  # 따뜻한 배경색
    plot_bgcolor="#FAF8F5",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=13),
    ),
    height=900,  # 0~100세 이상까지 명확히 표기되는 가독성 좋은 높이
    margin=dict(l=60, r=40, t=100, b=50),
)

# X축 (인구수): 음수 눈금 라벨을 양수로 시각화
fig.update_xaxes(
    title_text="인구수 (명)",
    gridcolor="#E0E0E0",
    range=[-max_val * 1.1, max_val * 1.1],
    tickvals=[
        -int(max_val),
        -int(max_val / 2),
        0,
        int(max_val / 2),
        int(max_val),
    ],
    ticktext=[
        f"{int(max_val):,}",
        f"{int(max_val/2):,}",
        "0",
        f"{int(max_val/2):,}",
        f"{int(max_val):,}",
    ],
)

# Y축 (나이) 순서 지정:
# autorange="reversed"나 값 기준 정렬을 일절 사용하지 않고,
# categoryarray에 0세부터 100세 이상까지 순서대로 전달하여 맨 아래가 0세, 맨 위가 100세 이상이 되도록 고정합니다.
fig.update_yaxes(
    title_text="연령 (나이)",
    type="category",
    categoryorder="array",
    categoryarray=age_labels,  # ['0세', '1세', ..., '100세 이상'] 정순 배치
    gridcolor="#E0E0E0",
    dtick=5,  # 눈금 라벨 5세 간격 표시
)

# Streamlit 화면에 출력
st.plotly_chart(fig, use_container_width=True)
