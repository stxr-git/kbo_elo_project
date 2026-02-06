import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------------------------------
# 1. 설정 및 데이터 로드
# -----------------------------------------------------------
st.set_page_config(page_title="KBO 역대 팀 승률 예측기", page_icon="⚾", layout="centered")

@st.cache_data
def load_data():
    # CSV 파일 로드 (파일명 확인 필수)
    # 같은 폴더에 'KBO_Elo_Custom_Rankings_Final.csv'가 있어야 합니다.
    df = pd.read_csv('KBO_Elo_Custom_Rankings.csv')
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("CSV 파일을 찾을 수 없습니다. (KBO_Elo_Custom_Rankings.csv)")
    st.stop()

# [핵심] Z-Score -> Elo 변환을 위한 표준편차 계산
elo_std = df['Final_Elo'].std()

# -----------------------------------------------------------
# 2. 팀명 고증 로직 (연도별 실제 팀명 변환)
# -----------------------------------------------------------
def get_display_name(row):
    year = row['Season']
    team = row['Team']
    
    # 1. 현대 유니콘스 계보 (삼미-청보-태평양-현대)
    if team in ['현대', '삼청태현', '태평양', '청보', '삼미']:
        if year <= 1985: return '삼미'
        if year <= 1987: return '청보'
        if year <= 1995: return '태평양'
        return '현대'
        
    # 2. 히어로즈 계보 (우리-히어로즈-넥센-키움)
    if team in ['키움', '넥센', '히어로즈', '우리']:
        if year == 2008: return '우리/히어로즈'
        if year <= 2018: return '넥센'
        return '키움'
        
    # 3. SSG 랜더스 계보 (SK-SSG)
    if team in ['SSG', 'SK']:
        return 'SK' if year <= 2020 else 'SSG'
        
    # 4. KIA 타이거즈 계보 (해태-KIA)
    if team in ['KIA', '해태']:
        return '해태' if year <= 2000 else 'KIA'
        
    # 5. 두산 베어스 계보 (OB-두산)
    if team in ['두산', 'OB']:
        return 'OB' if year <= 1998 else '두산'
        
    # 6. LG 트윈스 계보 (MBC-LG)
    if team in ['LG', 'MBC']:
        return 'MBC' if year <= 1989 else 'LG'
        
    # 7. 한화 이글스 계보 (빙그레-한화)
    if team in ['한화', '빙그레']:
        return '빙그레' if year <= 1993 else '한화'
        
    return team # 삼성, 롯데, 쌍방울, NC, KT 등은 그대로

# 데이터프레임에 'Real_Name' 컬럼 미리 적용
df['Real_Name'] = df.apply(get_display_name, axis=1)

# -----------------------------------------------------------
# 3. 메인 UI 구성
# -----------------------------------------------------------
st.title("⚾ KBO Dream Match Simulator")
st.markdown("##### 시공간을 초월한 KBO 역대 팀 간의 가상 대결")
st.divider()

# [요청사항 1] 설정 메뉴를 본문 상단으로 이동
st.subheader("⚙️ 경기 설정")
set_col1, set_col2 = st.columns(2)

with set_col1:
    calc_mode = st.radio(
        "🏆 승부 예측 기준",
        ("Elo 기반 (체급 대결)", "Z-Score 기반 (시대 보정)"),
        index=1,
        help="Elo: 시대 보정 없이, 타임머신을 타고 두 팀이서 붙는다면?\n\nZ-Score: 시대 보정을 통해 누가 더 본인의 시대를 완벽히 지배했는지"
    )

with set_col2:
    st.write("🏟️ 구장 설정")
    neutral_ground = st.checkbox("중립 구장 (홈 어드밴티지 제거)", value=True)
    hfa_value = 0 if neutral_ground else 17.57
    if not neutral_ground:
        st.caption(f"※ 홈 팀에게 Elo +{hfa_value}점 부여")

st.divider()

# -----------------------------------------------------------
# 4. 팀 선택 (연도 -> 팀 2단계 방식)
# -----------------------------------------------------------
col_home, col_away = st.columns(2)
seasons = sorted(df['Season'].unique(), reverse=True) # 최신 연도부터

# --- [홈 팀 선택] ---
with col_home:
    st.subheader("🏠 Home Team")
    # 1단계: 연도 선택
    year_a = st.selectbox("연도 선택", seasons, index=0, key='year_a')
    
    # 2단계: 해당 연도 팀 필터링 & 고증된 이름 표시
    teams_a_df = df[df['Season'] == year_a].copy()
    
    # 선택박스에 보여질 이름: "팀명 (Elo: 점수)"
    teams_a_df['Label'] = teams_a_df['Real_Name'] + " (" + teams_a_df['Final_Elo'].round(0).astype(str) + ")"
    
    team_a_label = st.selectbox("팀 선택", teams_a_df['Label'], key='team_a')
    
    # 선택된 데이터 추출
    team_a_data = teams_a_df[teams_a_df['Label'] == team_a_label].iloc[0]

    # 스탯 표시
    st.info(f"**{year_a} {team_a_data['Real_Name']}**\n\nElo: {team_a_data['Final_Elo']}\nZ: {team_a_data['Z_Score']}")


# --- [원정 팀 선택] ---
with col_away:
    st.subheader("✈️ Away Team")
    # 1단계: 연도 선택
    year_b = st.selectbox("연도 선택", seasons, index=1, key='year_b') # 기본값: 작년
    
    # 2단계: 해당 연도 팀 필터링
    teams_b_df = df[df['Season'] == year_b].copy()
    teams_b_df['Label'] = teams_b_df['Real_Name'] + " (" + teams_b_df['Final_Elo'].round(0).astype(str) + ")"
    
    team_b_label = st.selectbox("팀 선택", teams_b_df['Label'], key='team_b')
    
    # 선택된 데이터 추출
    team_b_data = teams_b_df[teams_b_df['Label'] == team_b_label].iloc[0]

    # 스탯 표시
    st.info(f"**{year_b} {team_b_data['Real_Name']}**\n\nElo: {team_b_data['Final_Elo']}\nZ: {team_b_data['Z_Score']}")


# -----------------------------------------------------------
# 5. 승률 계산 및 결과 표시
# -----------------------------------------------------------
st.write("") # 여백
if st.button("🔥 경기 예측 시작!", use_container_width=True):
    st.divider()
    
    # 계산 로직
    if "Elo" in calc_mode:
        score_diff = team_a_data['Final_Elo'] - team_b_data['Final_Elo']
        final_diff = score_diff + hfa_value
        mode_text = "Elo 점수(절대 평가)"
    else:
        # Z-Score 차이를 Elo 차이로 환산
        z_diff = team_a_data['Z_Score'] - team_b_data['Z_Score']
        converted_elo_diff = z_diff * elo_std
        final_diff = converted_elo_diff + hfa_value
        mode_text = "Z-Score 격차(시대 보정)"

    # 승률 공식
    prob_home = 1 / (1 + 10 ** (-final_diff / 400))
    prob_away = 1 - prob_home

    # 승자 결정
    if prob_home > prob_away:
        winner_name = f"{year_a} {team_a_data['Real_Name']}"
        win_prob = prob_home
        color = "#0066ff" # 파랑
        winner_side = "Home"
    else:
        winner_name = f"{year_b} {team_b_data['Real_Name']}"
        win_prob = prob_away
        color = "#ff3333" # 빨강
        winner_side = "Away"

    # 결과 UI
    st.markdown(f"<h3 style='text-align: center;'>🏆 승자 예측</h3>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; color: {color};'>{winner_name}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>승리 확률: {win_prob*100:.1f}%</h2>", unsafe_allow_html=True)
    
    st.caption(f"※ 계산 기준: {mode_text} | 보정 점수차: {final_diff:.2f}")

    # [수정된 부분] 게이지 바 및 텍스트 정렬
    st.progress(prob_home)
    
    # 오류가 났던 부분 수정: st.write에서 인자 제거하고 HTML/Markdown으로 처리
    res_c1, res_c2 = st.columns(2)
    
    # 홈팀 (왼쪽 정렬)
    res_c1.markdown(f"**🏠 {team_a_data['Real_Name']}** ({prob_home*100:.1f}%)")
    
    # 원정팀 (오른쪽 정렬을 위해 HTML 사용)
    res_c2.markdown(f"<div style='text-align: right;'>**✈️ {team_b_data['Real_Name']}** ({prob_away*100:.1f}%)</div>", unsafe_allow_html=True)

    # Z-Score 모드일 때 추가 설명
    if "Z-Score" in calc_mode:
        st.info(f"""
        💡 **결과 해석:**
        이 결과는 **'누가 자신의 시대를 더 완벽하게 지배했는가?'**에 대한 답입니다.
        **{winner_name}** 팀이 **{year_b if winner_side=='Home' else year_a}년의 상대팀**보다
        당시 리그 내에서의 위상이 더 독보적이었습니다.
        """)
