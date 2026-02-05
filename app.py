import streamlit as st
import pandas as pd
import numpy as np
import os

# -----------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------
st.set_page_config(page_title="KBO 역대 팀 승률 예측기", page_icon="⚾")

# -----------------------------------------------------------
# 2. 데이터 로드 함수 정의
# -----------------------------------------------------------
@st.cache_data
def load_data():
    file_name = 'KBO_Elo_Custom_Rankings.csv'
    
    if not os.path.exists(file_name):
        return None
        
    df = pd.read_csv(file_name)
    return df

# -----------------------------------------------------------
# 3. 데이터 로드 실행
# -----------------------------------------------------------
df = load_data()

if df is None:
    st.error("csv 파일을 찾을 수 없습니다. 같은 폴더에 'KBO_Elo_Custom_Rankings.csv' 파일을 넣어주세요.")
    st.stop()

# -----------------------------------------------------------
# 4. UI 구성
# -----------------------------------------------------------
st.title("⚾ KBO 역대 팀 매치업 시뮬레이터")
st.markdown("Elo Rating 시스템을 기반으로 **역대 팀 간의 가상 대결 승률**을 예측합니다.")
st.caption("※ 이 시뮬레이션은 시대별 리그 수준 차이를 반영한 절대적 실력 비교가 아닌, **각 시대에서의 리그 지배력(Relative Dominance)을 기반으로 한 가상 대결**입니다.")

st.divider() # 구분선 추가

# [수정] 사이드바 제거 -> 메인 화면에 배치
# 팀 선택 컬럼 바로 위에 체크박스 배치
neutral_ground = st.checkbox("🏟️ 중립 구장 (홈 어드밴티지 제거)", value=True)

# 홈 어드밴티지 점수 계산
hfa_value = 0 if neutral_ground else 17.57

st.write("") # 약간의 여백

# 연도 리스트 (내림차순 정렬)
unique_years = sorted(df['Season'].unique(), reverse=True)

# 메인: 팀 선택 (2단 컬럼)
col1, col2 = st.columns(2)

# --- 홈 팀 선택 ---
with col1:
    st.subheader("🏠 홈 팀 (Home)")
    
    year_a = st.selectbox("연도 선택", unique_years, key='year_a')
    
    teams_a_df = df[df['Season'] == year_a].sort_values(by='Final_Elo', ascending=False)
    teams_a_df['Label'] = teams_a_df['Team'] + " (Elo: " + teams_a_df['Final_Elo'].round(1).astype(str) + ")"
    
    team_a_label = st.selectbox("팀 선택", teams_a_df['Label'], key='team_a')
    team_a_data = teams_a_df[teams_a_df['Label'] == team_a_label].iloc[0]
    
    st.info(f"**{team_a_data['Team']}**\n\nElo: {team_a_data['Final_Elo']}\nZ-Score: {team_a_data['Z_Score']}")

# --- 원정 팀 선택 ---
with col2:
    st.subheader("✈️ 원정 팀 (Away)")
    
    year_b = st.selectbox("연도 선택", unique_years, index=0, key='year_b')
    
    teams_b_df = df[df['Season'] == year_b].sort_values(by='Final_Elo', ascending=False)
    teams_b_df['Label'] = teams_b_df['Team'] + " (Elo: " + teams_b_df['Final_Elo'].round(1).astype(str) + ")"
    
    default_idx_b = 1 if len(teams_b_df) > 1 else 0
    team_b_label = st.selectbox("팀 선택", teams_b_df['Label'], index=default_idx_b, key='team_b')
    
    team_b_data = teams_b_df[teams_b_df['Label'] == team_b_label].iloc[0]
    
    st.info(f"**{team_b_data['Team']}**\n\nElo: {team_b_data['Final_Elo']}\nZ-Score: {team_b_data['Z_Score']}")

# -----------------------------------------------------------
# 5. 승률 계산 및 결과 표시
# -----------------------------------------------------------
if st.button("경기 예측 시작! 🚀", use_container_width=True):
    elo_home = team_a_data['Final_Elo']
    elo_away = team_b_data['Final_Elo']
    
    # 승률 공식
    diff = elo_home - elo_away + hfa_value
    win_prob_home = 1 / (1 + 10 ** (-diff / 400))
    win_prob_away = 1 - win_prob_home
    
    st.divider()
    
    # 승자 판별
    if win_prob_home > win_prob_away:
        winner = f"{team_a_data['Season']} {team_a_data['Team']}"
        prob = win_prob_home
        color = "blue"
    else:
        winner = f"{team_b_data['Season']} {team_b_data['Team']}"
        prob = win_prob_away
        color = "red"

    # 결과 텍스트
    st.markdown(f"<h2 style='text-align: center;'>예상 승자: <span style='color:{color}'>{winner}</span></h2>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <p style='text-align: center; font-size: 1.1em;'>
    두 팀이 맞붙을 경우, 당대 리그를 더 압도했던 <b>{winner}</b>이(가)<br>
    <b>{prob*100:.1f}%</b>의 확률로 승리할 것으로 예측됩니다.<br>
    <span style='color:gray; font-size:0.8em;'>(100경기 시뮬레이션 시 약 {int(prob*100)}승 {int((1-prob)*100)}패 예상)</span>
    </p>
    """, unsafe_allow_html=True)

    # 게이지 바
    st.write("")
    st.write(f"🏠 {team_a_data['Season']} {team_a_data['Team']} ({win_prob_home*100:.1f}%)")
    st.progress(win_prob_home)
    st.write(f"✈️ {team_b_data['Season']} {team_b_data['Team']} ({win_prob_away*100:.1f}%)")
    
    # Z-Score 비교
    st.divider()
    st.caption("💡 참고: Z-Score(시대 보정 위대함) 비교")
    z_diff = team_a_data['Z_Score'] - team_b_data['Z_Score']
    
    if abs(z_diff) < 0.2:
        st.write("두 팀은 각자의 시대에서 **비슷한 수준의 지배력**을 보여줬습니다.")
    elif z_diff > 0:
        st.write(f"**{team_a_data['Season']} {team_a_data['Team']}**이(가) 당시 리그를 더 압도적으로 지배했습니다.")
    else:
        st.write(f"**{team_b_data['Season']} {team_b_data['Team']}**이(가) 당시 리그를 더 압도적으로 지배했습니다.")