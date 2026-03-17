import streamlit as st
import graphviz

st.set_page_config(page_title="계측구성도 설계기", layout="wide")

# ==========================================
# 1. 초기 세션 상태(Session State) 설정
# ==========================================
if 'equipments' not in st.session_state:
    st.session_state.equipments =[]

# 입력 폼의 값들을 유지하기 위한 세션 상태
if 'new_name' not in st.session_state: st.session_state.new_name = "공기압축기"
if 'new_kw' not in st.session_state: st.session_state.new_kw = "55kW"
if 'new_desc' not in st.session_state: st.session_state.new_desc = "#1"
if 'new_type' not in st.session_state: st.session_state.new_type = "기존설비"
if 'new_has_w' not in st.session_state: st.session_state.new_has_w = True

# 설비 추가 버튼 클릭 시 실행될 콜백 함수 (입력한 설비명, 용량을 그대로 유지함)
def add_equipment():
    st.session_state.equipments.append({
        'name': st.session_state.new_name,
        'desc': st.session_state.new_desc,
        'kw': st.session_state.new_kw,
        'type': st.session_state.new_type,
        'has_w': st.session_state.new_has_w,
        'rtu': st.session_state.new_rtu
    })
    # '호기' 부분만 자동으로 다음 숫자로 올려줍니다.
    st.session_state.new_desc = f"#{len(st.session_state.equipments) + 1}"

# ==========================================
# 2. 메인 화면 레이아웃 시작
# ==========================================
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("1. 공정 및 RTU 설정")
    process_name = st.text_input("메인 공정명", "반도체 공정")
    rtu_count = st.number_input("RTU 개수", min_value=1, max_value=5, value=2) # 기본 2개
    
    # RTU 개수 변경에 맞춰 기존 설비들의 RTU 연결도 안전하게 보정
    for eq in st.session_state.equipments:
        rtu_num = int(eq['rtu'].split('-')[1])
        if rtu_num > rtu_count:
            eq['rtu'] = "RTU-1"

    st.subheader("2. 설비 추가")
    # st.form을 빼고 세션 상태를 직접 연결하여 입력값이 날아가지 않게 수정!
    st.text_input("설비명", key='new_name')
    st.text_input("호기", key='new_desc')
    st.text_input("용량", key='new_kw')
    st.selectbox("구분",["기존설비", "효율설비", "연동설비"], key='new_type')
    st.checkbox("전력량계(W) 설치 (체크 해제 시 설비만 직접 연결)", key='new_has_w')
    
    rtu_list = [f"RTU-{i+1}" for i in range(rtu_count)]
    st.selectbox("연결할 RTU", rtu_list, key='new_rtu')
    
    # 버튼을 누르면 위 add_equipment 함수가 실행됨
    st.button("➕ 설비 추가", on_click=add_equipment, type="primary")

    if st.button("🗑️ 전체 초기화"):
        st.session_state.equipments =[]
        st.session_state.new_desc = "#1"
        st.rerun()

    st.markdown("---")
    st.subheader("3. 추가된 설비 개별 수정")
    for i, eq in enumerate(st.session_state.equipments):
        st.write(f"**{eq['desc']} ({eq['name']})**")
        c1, c2 = st.columns(2)
        
        # 구분 변경 (3가지만 남김)
        new_type = c1.selectbox(
            "구분",["기존설비", "효율설비", "연동설비"], 
            index=["기존설비", "효율설비", "연동설비"].index(eq['type']), key=f"t_{i}"
        )
        # RTU 연결 변경 기능 추가
        current_rtu_idx = rtu_list.index(eq['rtu']) if eq['rtu'] in rtu_list else 0
        new_rtu = c2.selectbox(
            "RTU", rtu_list,
            index=current_rtu_idx, key=f"r_{i}"
        )

        if new_type != eq['type'] or new_rtu != eq['rtu']:
            st.session_state.equipments[i]['type'] = new_type
            st.session_state.equipments[i]['rtu'] = new_rtu
            st.rerun()

# ==========================================
# 3. 우측 다이어그램 생성 파트
# ==========================================
with col2:
    if st.session_state.equipments:
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.4', ranksep='0.8')
        dot.attr('node', fontname='NanumGothic', shape='box', style='filled', fillcolor='white', fontsize='9')

        # 핵심 계통 노드들
        dot.node('KEPCO', '한전', fillcolor='#FFD700', width='1.0')
        dot.node('MOF', 'MOF', fillcolor='#E0E0E0', width='1.0')
        
        dot.edge('KEPCO', 'MOF')

        # 공정과 RTU를 정확히 같은 가로선(rank='same')에 배치
        with dot.subgraph() as s_mid:
            s_mid.attr(rank='same')
            s_mid.node('PROCESS', process_name, fillcolor='#E0E0E0', width='1.0')
            for r in range(rtu_count):
                rtu_name = f"RTU-{r+1}"
                s_mid.node(rtu_name, 'R', shape='square', color='coral', style='filled', fillcolor='white', width='0.3')
        
        # MOF에서 공정과 RTU로 내려오는 선
        dot.edge('MOF', 'PROCESS')
        for r in range(rtu_count):
            dot.edge('MOF', f"RTU-{r+1}", style='dashed', color='saddlebrown')

        # 설비 클러스터 테두리
        with dot.subgraph(name='cluster_equip') as c:
            c.attr(style='dashed', color='gray') 
            color_map = {"기존설비": "#B0C4DE", "효율설비": "#C1E1C1", "연동설비": "#A9A9A9"}
            
            # [해결 핵심 1] W 층 뼈대 고정
            with c.subgraph() as s_w:
                s_w.attr(rank='same')
                for i, eq in enumerate(st.session_state.equipments):
                    if eq['has_w']:
                        s_w.node(f'W_{i}', 'W', shape='circle', width='0.4')
                    else:
                        # W가 없는 설비는 '투명한 점(0사이즈)'을 만들어서 수직 라인 뼈대를 유지함
                        s_w.node(f'W_{i}', '', shape='none', width='0', height='0')

            # [해결 핵심 2] 설비 층 뼈대 고정
            with c.subgraph() as s_eq:
                s_eq.attr(rank='same')
                for i, eq in enumerate(st.session_state.equipments):
                    s_eq.node(f'EQ_{i}', f"{eq['name']}\n{eq['desc']}\n({eq['kw']})", 
                              fillcolor=color_map.get(eq['type']), style='filled', shape='box', width='0.8')

            # [해결 핵심 3] 설비들이 무조건 #1, #2, #3 순서대로 왼쪽에서 오른쪽으로만 나오게 투명 끈으로 묶음
            for i in range(len(st.session_state.equipments) - 1):
                c.edge(f'W_{i}', f'W_{i+1}', style='invis')
                c.edge(f'EQ_{i}', f'EQ_{i+1}', style='invis')

            # 뼈대에 실선/점선 입히기
            for i, eq in enumerate(st.session_state.equipments):
                # 공정 -> W (투명 W든 진짜 W든 선을 긋는다)
                dot.edge('PROCESS', f'W_{i}')
                # W -> 설비 (가장 무거운 가중치(weight=100)를 주어 수직으로만 떨어지게 강제)
                c.edge(f'W_{i}', f'EQ_{i}', weight='100')
                
                # W가 있는 경우에만 RTU 통신선 연결
                if eq['has_w']:
                    dot.edge(eq['rtu'], f'W_{i}', style='dashed', color='blue')

        st.graphviz_chart(dot)
        st.download_button("📥 이미지 다운로드", data=dot.pipe(format='png'), file_name="계측구성도.png", mime="image/png")
    else:
        st.info("👈 왼쪽 패널에서 설비를 추가하면 구성도가 나타납니다.")
