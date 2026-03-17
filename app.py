import streamlit as st
import graphviz

st.set_page_config(page_title="계측구성도 설계기", layout="wide")

# ==========================================
# 1. 초기 세션 상태(Session State) 설정
# ==========================================
if 'equipments' not in st.session_state:
    st.session_state.equipments =[]

if 'new_name' not in st.session_state: st.session_state.new_name = "공기압축기"
if 'new_kw' not in st.session_state: st.session_state.new_kw = "55kW"
if 'new_desc' not in st.session_state: st.session_state.new_desc = "#1"
if 'new_type' not in st.session_state: st.session_state.new_type = "기존설비"
if 'new_has_w' not in st.session_state: st.session_state.new_has_w = True

def add_equipment():
    st.session_state.equipments.append({
        'name': st.session_state.new_name,
        'desc': st.session_state.new_desc,
        'kw': st.session_state.new_kw,
        'type': st.session_state.new_type,
        'has_w': st.session_state.new_has_w,
        'rtu': st.session_state.new_rtu
    })
    st.session_state.new_desc = f"#{len(st.session_state.equipments) + 1}"

# ==========================================
# 2. 메인 화면 레이아웃
# ==========================================
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("1. 공정 및 RTU 설정")
    process_name = st.text_input("메인 공정명", "반도체 공정")
    rtu_count = st.number_input("RTU 개수", min_value=1, max_value=5, value=1) 
    
    for eq in st.session_state.equipments:
        rtu_num = int(eq['rtu'].split('-')[1])
        if rtu_num > rtu_count:
            eq['rtu'] = "RTU-1"

    st.subheader("2. 설비 추가")
    st.text_input("설비명", key='new_name')
    st.text_input("호기", key='new_desc')
    st.text_input("용량", key='new_kw')
    st.selectbox("구분", ["기존설비", "효율설비", "연동설비"], key='new_type')
    st.checkbox("전력량계(W) 설치 (체크 해제 시 설비만 직접 연결됨)", key='new_has_w')
    
    rtu_list =[f"RTU-{i+1}" for i in range(rtu_count)]
    st.selectbox("연결할 RTU", rtu_list, key='new_rtu')
    
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
        
        new_type = c1.selectbox(
            "구분",["기존설비", "효율설비", "연동설비"], 
            index=["기존설비", "효율설비", "연동설비"].index(eq['type']), key=f"t_{i}"
        )
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
# 3. 우측 다이어그램 생성
# ==========================================
with col2:
    if st.session_state.equipments:
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.5', ranksep='0.8')
        dot.attr('node', fontname='NanumGothic', shape='box', style='filled', fillcolor='white', fontsize='9')

        dot.node('KEPCO', '한전', fillcolor='#FFD700', width='1.0')
        dot.node('MOF', 'MOF', fillcolor='#E0E0E0', width='1.0')
        dot.edge('KEPCO', 'MOF')

        # [추가] EER 서버 노드 생성 및 MOF와 연결
        dot.node('EER', 'EER 서버\n(한국에너지공단)', fillcolor='#ADD8E6', width='1.2')
        dot.edge('MOF', 'EER', style='dashed', color='saddlebrown')

        #[안정화] 공정과 RTU들을 수평으로 나란히 배치
        with dot.subgraph() as s_mid:
            s_mid.attr(rank='same')
            s_mid.node('PROCESS', process_name, fillcolor='#E0E0E0', width='1.0')
            rtu_nodes =[]
            for r in range(rtu_count):
                rtu_name = f"RTU-{r+1}"
                # [디테일] R 글자색을 사진처럼 빨간색(red)으로 적용
                s_mid.node(rtu_name, 'R', shape='square', color='coral', fontcolor='red', style='bold,filled', fillcolor='white', width='0.3')
                rtu_nodes.append(rtu_name)
            
            # PROCESS 옆에 RTU들이 줄 서도록 투명선 추가
            if rtu_count > 0:
                s_mid.edge('PROCESS', rtu_nodes[0], style='invis')
                for r in range(rtu_count - 1):
                    s_mid.edge(rtu_nodes[r], rtu_nodes[r+1], style='invis')

        dot.edge('MOF', 'PROCESS')
        
        for r in range(rtu_count):
            rtu_name = f"RTU-{r+1}"
            dot.edge('MOF', rtu_name, style='dashed', color='saddlebrown')
            # [추가] 각 RTU에서 EER 서버로 가는 점선 연결
            dot.edge(rtu_name, 'EER', style='dashed', color='saddlebrown')

        # 설비 클러스터 영역
        with dot.subgraph(name='cluster_equip') as c:
            c.attr(style='dashed', color='gray') 
            color_map = {"기존설비": "#B0C4DE", "효율설비": "#C1E1C1", "연동설비": "#A9A9A9"}
            
            with c.subgraph() as s_w:
                s_w.attr(rank='same')
                for i, eq in enumerate(st.session_state.equipments):
                    if eq['has_w']:
                        s_w.node(f'W_{i}', 'W', shape='circle', width='0.4')

            with c.subgraph() as s_eq:
                s_eq.attr(rank='same')
                for i, eq in enumerate(st.session_state.equipments):
                    s_eq.node(f'EQ_{i}', f"{eq['name']}\n{eq['desc']}\n({eq['kw']})", 
                              fillcolor=color_map.get(eq['type']), style='filled', shape='box', width='0.8')
                
                for i in range(len(st.session_state.equipments) - 1):
                    s_eq.edge(f'EQ_{i}', f'EQ_{i+1}', style='invis')

            # 실제 선 연결
            for i, eq in enumerate(st.session_state.equipments):
                if eq['has_w']:
                    dot.edge('PROCESS', f'W_{i}', weight='10')
                    c.edge(f'W_{i}', f'EQ_{i}', weight='10')
                    dot.edge(eq['rtu'], f'W_{i}', style='dashed', color='blue', constraint='false')
                else:
                    dot.edge('PROCESS', f'EQ_{i}', weight='10')

        st.graphviz_chart(dot)
        st.download_button("📥 이미지 다운로드", data=dot.pipe(format='png'), file_name="계측구성도.png", mime="image/png")
    else:
        st.info("👈 왼쪽 패널에서 설비를 추가하면 구성도가 나타납니다.")
