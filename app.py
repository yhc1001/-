import streamlit as st
import graphviz

st.set_page_config(page_title="계측구성도 설계기", layout="wide")

if 'equipments' not in st.session_state:
    st.session_state.equipments = []

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("설비 관리")
    with st.form("add_form", clear_on_submit=True):
        n = st.text_input("설비명", "공기압축기")
        d = st.text_input("호기", f"#{len(st.session_state.equipments)+1}")
        k = st.text_input("용량", "55kW")
        t = st.selectbox("구분", ["기존설비", "교체(신규)설비", "효율설비", "연동설비"])
        has_w = st.checkbox("전력량계(W) 설치", value=True)
        target_rtu = st.selectbox("연결할 RTU", [f"RTU-{i+1}" for i in range(5)])
        if st.form_submit_button("추가"):
            st.session_state.equipments.append({'name': n, 'desc': d, 'kw': k, 'type': t, 'has_w': has_w, 'rtu': target_rtu})
            st.rerun()

    for i, eq in enumerate(st.session_state.equipments):
        new_type = st.selectbox(f"{eq['desc']} 구분 변경", ["기존설비", "교체(신규)설비", "효율설비", "연동설비"], 
                                index=["기존설비", "교체(신규)설비", "효율설비", "연동설비"].index(eq['type']), key=f"t{i}")
        if new_type != eq['type']:
            st.session_state.equipments[i]['type'] = new_type
            st.rerun()

with col2:
    if st.session_state.equipments:
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.5', ranksep='0.8')
        dot.attr('node', fontname='NanumGothic', shape='box', style='filled', fillcolor='white', fontsize='9')

        dot.node('KEPCO', '한전', fillcolor='#FFD700', width='1.0')
        dot.node('MOF', 'MOF', fillcolor='#E0E0E0', width='1.0')
        dot.node('PROCESS', '공정', fillcolor='#E0E0E0', width='1.0')
        dot.edge('KEPCO', 'MOF')
        dot.edge('MOF', 'PROCESS')

        # RTU 생성
        for r in range(5):
            rtu_name = f"RTU-{r+1}"
            dot.node(rtu_name, 'R', shape='square', color='coral', style='filled', fillcolor='white', width='0.3')
            dot.edge('MOF', rtu_name, style='dashed', color='saddlebrown')

        with dot.subgraph(name='cluster_equip') as c:
            c.attr(style='dashed', color='gray', ordering='in') # ordering으로 순서 강제
            color_map = {"기존설비": "#B0C4DE", "교체(신규)설비": "#FFDAB9", "효율설비": "#C1E1C1", "연동설비": "#A9A9A9"}
            
            for i, eq in enumerate(st.session_state.equipments):
                eq_id = f'EQ_{i}'
                c.node(eq_id, f"{eq['name']}\n{eq['desc']}\n({eq['kw']})", 
                       fillcolor=color_map.get(eq['type']), style='filled', shape='box', width='0.8')
                
                if eq['has_w']:
                    w_id = f'W_{i}'
                    c.node(w_id, 'W', shape='circle', width='0.4')
                    c.edge(w_id, eq_id)
                    dot.edge('PROCESS', w_id)
                    dot.edge(eq['rtu'], w_id, style='dashed', color='blue')
                else:
                    # W가 없으면 공정에서 바로 수직 연결
                    dot.edge('PROCESS', eq_id, constraint='true') 
        
        st.graphviz_chart(dot)
