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
        dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.3', ranksep='0.4')
        dot.attr('node', fontname='NanumGothic', shape='box', style='filled', fillcolor='white', fontsize='9')
        
        # 1. 범례 (Legend) 독립 배치
        # 겹치지 않게 노드명 앞에 LEG_ 접두사 사용
        dot.node('LEG_W', 'W: 전력량계', shape='circle', style='filled', fillcolor='white', width='0.4', height='0.4')
        dot.node('LEG_R', 'R: RTU', shape='square', style='filled', fillcolor='#FFDAB9', color='coral')
        dot.node('LEG_G', '■: 기존설비', shape='box', style='filled', fillcolor='#B0C4DE')
        dot.node('LEG_E', '■: 효율설비', shape='box', style='filled', fillcolor='#C1E1C1')
        
        # 범례 정렬 (왼쪽 끝에 세로로 정렬)
        with dot.subgraph() as l:
            l.attr(rank='same')
            l.edge('LEG_W', 'LEG_R', style='invis')
            l.edge('LEG_R', 'LEG_G', style='invis')
            l.edge('LEG_G', 'LEG_E', style='invis')

        # 2. 메인 구조
        dot.node('KEPCO', '한전', fillcolor='#FFD700', width='1.0')
        dot.node('MOF', 'MOF', fillcolor='#E0E0E0', width='1.0')
        dot.node('PROCESS', process_name, fillcolor='#E0E0E0', width='1.0')
        
        dot.edge('KEPCO', 'MOF')
        dot.edge('MOF', 'PROCESS')

        # 3. RTU 및 설비
        for r in range(rtu_count):
            rtu_name = f"RTU-{r+1}"
            dot.node(rtu_name, 'R', shape='square', color='coral', style='filled', fillcolor='#FFDAB9')
            dot.edge('MOF', rtu_name, style='dashed', color='saddlebrown')

        with dot.subgraph(name='cluster_equip') as c:
            c.attr(style='dashed', color='gray', label='')
            for i, eq in enumerate(st.session_state.equipments):
                eq_id = f'EQ_{i}'
                # 색상 매핑
                color_map = {"기존설비": "#B0C4DE", "교체(신규)설비": "#FFDAB9", "효율설비": "#C1E1C1", "연동설비": "#A9A9A9"}
                c.node(eq_id, f"{eq['name']}\n{eq['desc']}\n({eq['kw']})", 
                       fillcolor=color_map.get(eq['type'], 'white'), style='filled', shape='box', width='0.8')
                
                if eq['has_w']:
                    w_id = f'W_{i}'
                    c.node(w_id, 'W', shape='circle', width='0.4')
                    c.edge(w_id, eq_id)
                    dot.edge('PROCESS', w_id)
                    dot.edge(eq['rtu'], w_id, style='dashed', color='darkblue')
        
        st.graphviz_chart(dot)
        st.download_button("📥 이미지 다운로드", data=dot.pipe(format='png'), file_name="계측구성도.png", mime="image/png")
