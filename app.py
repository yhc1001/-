import streamlit as st
import graphviz

st.set_page_config(page_title="계측구성도 설계기", layout="wide")

if 'equipments' not in st.session_state:
    st.session_state.equipments =[]

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
        t = st.selectbox("구분",["기존설비", "교체(신규)설비", "효율설비", "연동설비"])
        has_w = st.checkbox("전력량계(W) 설치 (체크 해제 시 설비만 직접 연결됨)", value=True)
        target_rtu = st.selectbox("연결할 RTU",[f"RTU-{i+1}" for i in range(rtu_count)])
        
        if st.form_submit_button("➕ 설비 추가"):
            st.session_state.equipments.append({'name': n, 'desc': d, 'kw': k, 'type': t, 'has_w': has_w, 'rtu': target_rtu})
            st.rerun()
            
    if st.button("🗑️ 전체 초기화"):
        st.session_state.equipments =[]
        st.rerun()

    st.markdown("---")
    st.subheader("3. 설비 상태 개별 수정")
    for i, eq in enumerate(st.session_state.equipments):
        new_type = st.selectbox(
            f"{eq['desc']} ({eq['name']}) 구분 변경",["기존설비", "교체(신규)설비", "효율설비", "연동설비"], 
            index=["기존설비", "교체(신규)설비", "효율설비", "연동설비"].index(eq['type']), 
            key=f"t{i}"
        )
        if new_type != eq['type']:
            st.session_state.equipments[i]['type'] = new_type
            st.rerun()

with col2:
    if st.session_state.equipments:
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.4', ranksep='0.8')
        dot.attr('node', fontname='NanumGothic', shape='box', style='filled', fillcolor='white', fontsize='9')

        # 메인 계통 생성
        dot.node('KEPCO', '한전', fillcolor='#FFD700', width='1.0')
        dot.node('MOF', 'MOF', fillcolor='#E0E0E0', width='1.0')
        dot.node('PROCESS', process_name, fillcolor='#E0E0E0', width='1.0')
        
        dot.edge('KEPCO', 'MOF')
        dot.edge('MOF', 'PROCESS')

        # RTU 생성
        for r in range(rtu_count):
            rtu_name = f"RTU-{r+1}"
            dot.node(rtu_name, 'R', shape='square', color='coral', style='filled', fillcolor='white', width='0.3')
            dot.edge('MOF', rtu_name, style='dashed', color='saddlebrown')

        # 설비 클러스터 영역
        with dot.subgraph(name='cluster_equip') as c:
            c.attr(style='dashed', color='gray') 
            color_map = {"기존설비": "#B0C4DE", "교체(신규)설비": "#FFDAB9", "효율설비": "#C1E1C1", "연동설비": "#A9A9A9"}
            
            # [핵심 1] 모든 설비 노드를 '같은 높이(rank=same)'에 강제 배치
            with c.subgraph() as s_eq:
                s_eq.attr(rank='same')
                for i, eq in enumerate(st.session_state.equipments):
                    eq_id = f'EQ_{i}'
                    s_eq.node(eq_id, f"{eq['name']}\n{eq['desc']}\n({eq['kw']})", 
                              fillcolor=color_map.get(eq['type']), style='filled', shape='box', width='0.8')
            
            # [핵심 2] 설비들이 섞이지 않도록 왼쪽부터 오른쪽으로 투명 선(invis)으로 연결 강제
            for i in range(len(st.session_state.equipments) - 1):
                c.edge(f'EQ_{i}', f'EQ_{i+1}', style='invis')
            
            # 선 연결 처리 (W 유무에 따라)
            for i, eq in enumerate(st.session_state.equipments):
                eq_id = f'EQ_{i}'
                if eq['has_w']:
                    w_id = f'W_{i}'
                    c.node(w_id, 'W', shape='circle', width='0.4')
                    c.edge(w_id, eq_id) # W에서 설비로
                    dot.edge('PROCESS', w_id) # 공정에서 W로
                    dot.edge(eq['rtu'], w_id, style='dashed', color='blue') # RTU에서 W로 통신선
                else:
                    # 전력량계가 없다면 공정에서 설비로 바로 연결 (그래도 설비는 튀어 오르지 않음)
                    dot.edge('PROCESS', eq_id)
        
        # 화면 출력 및 다운로드
        st.graphviz_chart(dot)
        st.download_button("📥 이미지 다운로드", data=dot.pipe(format='png'), file_name="계측구성도.png", mime="image/png")
    else:
        st.info("👈 왼쪽 패널에서 설비를 추가하면 구성도가 나타납니다.")
