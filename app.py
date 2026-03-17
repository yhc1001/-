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
        dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.5', ranksep='0.6')
        
        # 1. 좌측 범례 서브그래프 (rank='same'을 이용해 왼쪽 배치)
        with dot.subgraph(name='cluster_legend') as l:
            l.attr(label='범례', style='solid', color='black', fontname='NanumGothic')
            l.node('LEG_W', 'W: 전력량계', shape='circle', width='0.5')
            l.node('LEG_R', 'R: RTU', shape='square', style='filled', fillcolor='white', width='0.5')
            l.node('LEG_C', '교체대상설비', style='filled', fillcolor='#FFEFD5', shape='box')
            l.node('LEG_H', '효율향상설비', style='filled', fillcolor='#90EE90', shape='box')
            l.node('LEG_Y', '연동설비', style='filled', fillcolor='#A9A9A9', shape='box')
            # 범례 항목들을 수직으로 정렬
            l.edge('LEG_W', 'LEG_R', style='invis')
            l.edge('LEG_R', 'LEG_C', style='invis')
            l.edge('LEG_C', 'LEG_H', style='invis')
            l.edge('LEG_H', 'LEG_Y', style='invis')

        # 2. 메인 구조 (한전부터 아래로)
        dot.node('KEPCO', '한전', fillcolor='#ADD8E6', style='filled', shape='box')
        dot.node('MOF', 'MOF', fillcolor='white', style='filled', shape='box')
        dot.node('PROCESS', process_name, fillcolor='#E0FFD4', style='filled', shape='box')
        dot.edge('KEPCO', 'MOF')
        dot.edge('MOF', 'PROCESS')

        # 3. RTU 및 설비
        for r in range(rtu_count):
            rtu_name = f"RTU-{r+1}"
            dot.node(rtu_name, 'R', shape='square', color='red', style='filled', fillcolor='white')
            dot.edge('MOF', rtu_name, style='dashed', color='red')

        with dot.subgraph(name='cluster_equip') as c:
            c.attr(style='dashed', color='gray')
            for i, eq in enumerate(st.session_state.equipments):
                eq_id = f'EQ_{i}'
                # 색상 매핑 수정 (교체/효율/연동)
                color_map = {"교체대상설비": "#FFEFD5", "효율향상설비": "#90EE90", "연동설비": "#A9A9A9"}
                c.node(eq_id, f"{eq['name']}\n{eq['desc']}\n({eq['kw']})", 
                       fillcolor=color_map.get(eq['type'], 'white'), style='filled', shape='box')
                
                if eq['has_w']:
                    w_id = f'W_{i}'
                    c.node(w_id, 'W', shape='circle')
                    c.edge(w_id, eq_id)
                    dot.edge('PROCESS', w_id)
                    dot.edge(eq['rtu'], w_id, color='red')
        
        st.graphviz_chart(dot)
        st.download_button("📥 이미지 다운로드", data=dot.pipe(format='png'), file_name="계측구성도.png", mime="image/png")
