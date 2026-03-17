import streamlit as st
import graphviz

st.set_page_config(page_title="계측구성도 설계기", layout="wide")

if 'equipments' not in st.session_state:
    st.session_state.equipments = []
if 'rtus' not in st.session_state:
    st.session_state.rtus = ['RTU-1'] # 기본 RTU 1개

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("1. 공정 및 RTU 설정")
    process_name = st.text_input("메인 공정명", "반도체 공정")
    rtu_count = st.number_input("RTU 개수", min_value=1, max_value=5, value=1)
    
    st.subheader("2. 설비 추가")
    with st.form("add_form", clear_on_submit=True):
        n = st.text_input("설비명", "공기압축기")
        d = st.text_input("호기", f"#{len(st.session_state.equipments)+1}")
        k = st.text_input("용량", "55kW")
        t = st.selectbox("구분", ["기존설비", "교체(신규)설비", "연동설비"])
        has_w = st.checkbox("전력량계(W) 설치", value=True)
        target_rtu = st.selectbox("연결할 RTU", [f"RTU-{i+1}" for i in range(rtu_count)])
        
        if st.form_submit_button("추가"):
            st.session_state.equipments.append({'name': n, 'desc': d, 'kw': k, 'type': t, 'has_w': has_w, 'rtu': target_rtu})
            st.rerun()

with col2:
    if st.session_state.equipments:
        dot = graphviz.Digraph(format='png')
        # 전체 그래프 설정
        dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.2', ranksep='0.3')
        dot.attr('node', fontname='NanumGothic', shape='box', style='filled', fillcolor='white', fontsize='8')

        # 1. 범례 배치 (rankdir='LR'을 사용하여 왼쪽에서 오른쪽으로 한 줄로 정렬)
        with dot.subgraph(name='cluster_legend') as l:
            l.attr(label='', style='invis', rankdir='LR') # 테두리 숨김
            l.node('LEG_W', 'W: 전력량계', shape='circle', width='0.25', height='0.25', fontsize='8')
            l.node('LEG_R', 'R: RTU', shape='square', width='0.3', height='0.3', fontsize='8')
            l.node('LEG_G', '■: 기존설비', shape='box', fillcolor='#B0C4DE', fontsize='8')
            l.node('LEG_E', '■: 효율설비', shape='box', fillcolor='#C1E1C1', fontsize='8')
            l.node('LEG_Y', '■: 연동설비', shape='box', fillcolor='#A9A9A9', fontsize='8')
            # 일렬로 연결 (수평 정렬)
            l.edge('LEG_W', 'LEG_R', style='invis')
            l.edge('LEG_R', 'LEG_G', style='invis')
            l.edge('LEG_G', 'LEG_E', style='invis')
            l.edge('LEG_E', 'LEG_Y', style='invis')

        # 2. 메인 구조
        dot.node('KEPCO', '한전', fillcolor='#FFD700', width='0.8', height='0.4')
        dot.node('MOF', 'MOF', fillcolor='#E0E0E0', width='0.8', height='0.4')
        dot.node('PROCESS', process_name, fillcolor='#E0E0E0', width='0.8', height='0.4')
        
        dot.edge('KEPCO', 'MOF')
        dot.edge('MOF', 'PROCESS')

        # 3. RTU 및 설비
        for r in range(rtu_count):
            rtu_name = f"RTU-{r+1}"
            dot.node(rtu_name, 'R', shape='square', color='coral', style='filled', fillcolor='white', width='0.3', height='0.3')
            dot.edge('MOF', rtu_name, style='dashed', color='saddlebrown')

         with dot.subgraph(name='cluster_equip') as c:
            c.attr(style='dashed', color='gray', ordering='in') # ordering='in'으로 순서 고정
            
            # 설비들을 순서대로 배치하기 위해 노드 추가 시 번호를 활용
            for i, eq in enumerate(st.session_state.equipments):
                eq_id = f'EQ_{i}'
                # ... (색상 매핑 동일)
                c.node(eq_id, f"{eq['name']}\n{eq['desc']}\n({eq['kw']})", 
                       fillcolor=color_map.get(eq['type'], 'white'), style='filled', shape='box', width='0.7')
                
                if eq['has_w']:
                    w_id = f'W_{i}'
                    # W 노드 크기 고정
                    c.node(w_id, 'W', shape='circle', width='0.3', height='0.3')
                    # 설비와 W 연결 (화살표 꼬임 방지)
                    c.edge(w_id, eq_id, dir='forward')
                    # 공정과 W 연결
                    dot.edge('PROCESS', w_id, dir='forward')
                    # RTU와 W 연결
                    dot.edge(eq['rtu'], w_id, style='dashed', color='blue', dir='forward')
        
        st.graphviz_chart(dot)
        st.download_button("📥 이미지 다운로드", data=dot.pipe(format='png'), file_name="계측구성도.png", mime="image/png")
