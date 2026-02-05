import streamlit as st
import pandas as pd
import numpy as np
import os

# -----------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------
st.set_page_config(page_title="KBO 역대 팀 승률 예측기", page_icon="⚾")

# -----------------------------------------------------------
# 2. 데이터 로드 함수
# -----------------------------------------------------------
@st.cache_data
def load_data():
    file_name = 'KBO_Elo_Custom_Rankings.csv'
    if not os.path.exists(file_name):
        return None
    df = pd.read_csv(file_name)
    return df

# -----------------------------------------------------------
# [핵심 기능] 연도에 따른 "그 시절 팀명" 변환 함수
# -----------------------------------------------------------
def get_historical_name(team_db_name, year):
    # 1. 삼청태현 (현대 계보)
    if team_db_name in ['삼청태현', '현대', '태평양', '청보', '삼미']:
        if year <= 1985: return '삼미'
        elif year <= 1987: return '청보'
        elif year <= 1995: return '태평양'
        else: return '현대'

    # 2. KIA (해태)
    if team_db_name in ['KIA', '해태']:
        return '해태' if year <= 2000 else 'KIA'

    # 3. 두산 (OB)
    if team_db_name in ['두산', 'OB']:
        return 'OB' if year <= 1998 else '두산'

    # 4. LG (MBC)
    if team_db_name in ['LG', 'MBC']:
        return 'MBC' if year <= 1989 else 'LG'

    # 5. 한화 (빙그레)
    if team_db_name in ['한화', '빙그레']:
        return '빙그레' if year <= 1993 else '한화'

    # 6. SSG (SK)
    if team_db_name in ['SSG', 'SK']:
        return 'SK' if year <= 2020 else 'SSG'

    # 7. 키움 (히어로즈 계보)
    if team_db_name in ['키움', '넥센', '히어로즈', '우리']:
        if year <= 2008: return '우리'
        elif year <= 2018: return '넥센'
        else: return '키움'
    
    # 8. 쌍방울 (그대로)
    if team_db_name == '쌍방울':
        return '쌍방울'

    # 삼성, 롯데, NC, KT 등 변경 없는 팀
    return team_db_name

# -----------------------------------------------------------
# 3. 데이터 로드 및 전처리
# -----------------------------------------------------------
df = load_data()

if df is None:
    st.error("csv 파일을 찾을 수 없습니다. 같은 폴더에 'KBO_Elo_Custom_Rankings.csv' 파일을 넣어주세요.")
    st.stop()

# -----------------------------------------------------------
# 4. UI 구성
# -----------------------------------------------------------
st.title("⚾ KBO 역대 최강 팀 매치업 시뮬레이터")
st.markdown("Elo Rating 시스템을 기반으로 **역대 팀 간의 가상 대결 승률**을 예측합니다.")
st.caption("※ 이 시뮬레이션은 시대별 리그 수준 차이를 반영한 절대적 실력 비교가 아닌, **각 시대에서의 리그 지배력(Relative Dominance)을 기반으로 한 가상 대결**입니다.")

st.divider()

# 경기 설정 (중립 구장)
neutral_ground = st.checkbox("🏟️ 중립 구장 (홈 어드밴티지 제거)", value=True)
hfa_value = 0 if neutral_ground else 17.57

st.write("") 

# 연도 리스트
unique_years = sorted(df['Season'].unique(), reverse=True)

col1, col2 = st.columns(2)

# --- [Function] 팀 선택 박스 생성 도우미 ---
def create_team_selector(column, key_prefix, default_year_idx=0, default_team_idx=0):
    with column:
        role = "🏠 홈 팀 (Home)" if key_prefix == 'a' else "✈️ 원정 팀 (Away)"
        st.subheader(role)
        
        # 1. 연도 선택
        selected_year = st.selectbox(
            "연도 선택", 
            unique_years, 
            index=default_year_idx, 
            key=f'year_{key_prefix}'
        )
        
        # 2. 해당 연도 데이터 필터링
        team_df = df[df['Season'] == selected_year].sort_values(by='Final_Elo', ascending=False).copy()
        
        # [핵심] 3. 표시용 실제 이름(Real Name) 생성
        # apply 함수를 써서 각 줄마다 연도에 맞는 이름으로 변환
        team_df['Real_Name'] = team_df.apply(lambda row: get_historical_name(row['Team'], row['Season']), axis=1)
        
        # 4. 라벨 만들기 (예: "해태 (Elo: 1580)")
        team_df['Label'] = team_df['Real_Name'] + " (Elo: " + team_df['Final_Elo'].round(1).astype(str) + ")"
        
        # 5. 팀 선택 박스
        # 데이터가 바뀌었을 때 인덱스 에러 방지
        current_idx = default_team_idx if default_team_idx < len(team_df) else 0
        
        selected_label = st.selectbox(
            "팀 선택", 
            team_df['Label'], 
            index=current_idx, 
            key=f'team_{key_prefix}'
        )
        
        # 6. 선택된 데이터 추출
        selected_data = team_df[team_df['Label'] == selected_label].iloc[0]
        
        # 7. 정보 표시 (여기서도 Real Name 사용)
        st.info(f"**{selected_data['Real_Name']}**\n\nElo: {selected_data['Final_Elo']}\nZ-Score: {selected_data['Z_Score']}")
        
        return selected_data

# --- UI 그리기 ---
team_a_data = create_team_selector(col1, 'a', default_year_idx=0) # 홈팀
team_b_data = create_team_selector(col2, 'b', default_year_idx=0, default_team_idx=1) # 원정팀

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
    
    # 승자 판별 (이름 표시할 때 Real_Name 사용)
    name_a = f"{team_a_data['Season']} {team_a_data['Real_Name']}"
    name_b = f"{team_b_data['Season']} {team_b_data['Real_Name']}"
    
    if win_prob_home > win_prob_away:
        winner = name_a
        prob = win_prob_home
        color = "blue"
    else:
        winner = name_b
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
    st.write(f"🏠 {name_a} ({win_prob_home*100:.1f}%)")
    st.progress(win_prob_home)
    st.write(f"✈️ {name_b} ({win_prob_away*100:.1f}%)")
    
    # Z-Score 비교
    st.divider()
    st.caption("💡 참고: Z-Score(시대 보정 위대함) 비교")
    z_diff = team_a_data['Z_Score'] - team_b_data['Z_Score']
    
    if abs(z_diff) < 0.2:
        st.write("두 팀은 각자의 시대에서 **비슷한 수준의 지배력**을 보여줬습니다.")
    elif z_diff > 0:
        st.write(f"**{name_a}**이(가) 당시 리그를 더 압도적으로 지배했습니다.")
    else:
        st.write(f"**{name_b}**이(가) 당시 리그를 더 압도적으로 지배했습니다.")
