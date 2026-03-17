import streamlit as st
import graphviz

st.set_page_config(page_title="계측구성도 자동 생성기", layout="wide")

st.title("📊 에너지 효율화 사업 - 계측구성도 자동 생성기")

if 'equipments' not in st.session_state:
    st.session_state.equipments = []

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("1. 공정 및 설비 관리")
    # 공정명 수정 기능 복구
    process_name = st.text_input("메인 공정명", "반도체 공정")
    
    with st.expander("➕ 새 설비 추가", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            n = st.text_input("설비명", "공기압축기")
            d = st.text_input("호기", f"#{len(st.session_state.equipments)+1}")
            k = st.text_input("용량", "55kW")
            t = st.selectbox("구분", ["기존설비", "교체(신규)설비", "연동설비"])
            if st.form_submit_button("추가"):
                st.session_state.equipments.append({'name': n, 'desc': d, 'kw': k, 'type': t})
                st.rerun()

    st.markdown("---")
    st.subheader("2. 설비별 색상/상태 수정")
    for i, eq in enumerate(st.session_state.equipments):
        with st.container():
            c1, c2 = st.columns([2, 1])
            c1.write(f"**{eq['desc']}**")
            new_type = c2.selectbox("변경", ["기존설비", "교체(신규)설비", "연동설비"], 
                                    index=["기존설비", "교체(신규)설비", "연동설비"].index(eq['type']),
                                    key=f"type_{i}")
            if new_type != eq['type']:
                st.session_state.equipments[i]['type'] = new_type
                st.rerun()

with col2:
    if st.session_state.equipments:
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='TB', splines='ortho', fontname='Malgun Gothic', nodesep='0.5', ranksep='0.6')
        dot.attr('node', fontname='Malgun Gothic', shape='box', style='filled', fillcolor='white')
        
        # 최상단: 한전
        dot.node('KEPCO', '한전', fillcolor='#FFD700', width='1.5')
        
        # 중간: MOF와 공정 (공정명은 입력값 사용)
        dot.node('MOF', 'MOF', fillcolor='#E0E0E0', width='1.5')
        dot.node('PROCESS', process_name, fillcolor='#E0E0E0', width='1.5')
        
        # RTU와 EER 서버
        dot.node('RTU', 'R', shape='square', color='coral', fontcolor='red', style='bold,filled', fillcolor='white', width='0.5')
        dot.node('EER', 'EER 서버\n(한국에너지공단)', fillcolor='#ADD8E6', width='1.5')
        
        # 계통 연결 (수직)
        dot.edge('KEPCO', 'MOF')
        dot.edge('MOF', 'PROCESS')
        
        # 통신 연결
        dot.edge('MOF', 'EER', style='dashed', color='saddlebrown')
        dot.edge('RTU', 'EER', style='dashed', color='saddlebrown')
        
        # RTU는 설비들과 연결되므로 process와 같은 위치 근처로 잡아줌
        with dot.subgraph() as s:
            s.attr(rank='same')
            s.node('RTU')
            s.node('PROCESS')

        with dot.subgraph(name='cluster_equip') as c:
            c.attr(style='dashed', color='gray')
            for i, eq in enumerate(st.session_state.equipments):
                w_id = f'W_{i}'
                eq_id = f'EQ_{i}'
                c.node(w_id, 'W', shape='circle', fillcolor='white', style='filled', width='0.4')
                
                color_map = {"기존설비": "#B0C4DE", "교체(신규)설비": "#90EE90", "연동설비": "#D3D3D3"}
                c.node(eq_id, f"{eq['name']}\n{eq['desc']}\n({eq['kw']})", fillcolor=color_map.get(eq['type']), style='filled')
                
                dot.edge('PROCESS', w_id)
                c.edge(w_id, eq_id)
                dot.edge('RTU', w_id, style='dashed', color='darkblue')

        st.graphviz_chart(dot)
        st.download_button("📥 이미지 다운로드", data=dot.pipe(format='png'), file_name="계측구성도.png", mime="image/png")
