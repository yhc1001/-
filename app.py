import streamlit as st
import graphviz
import os

st.set_page_config(page_title="계측구성도 설계기", layout="wide")

# ==========================================
# [해결 핵심] 현재 코드가 실행 중인 폴더의 '절대 경로'를 알아냅니다.
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 1. 초기 세션 상태 설정
# ==========================================
if 'equipments' not in st.session_state:
    st.session_state.equipments =[]

if 'new_name' not in st.session_state: st.session_state.new_name = "공기압축기"
if 'new_kw' not in st.session_state: st.session_state.new_kw = "75kW"
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
    st.subheader("🎨 디자인 테마 선택")
    theme = st.radio("테마",["기본 도형 (버전 1)", "커스텀 아이콘 (버전 2)"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    st.subheader("1. 공정 및 RTU 설정")
    process_name = st.text_input("메인 공정명", "성형 공정")
    rtu_count = st.number_input("RTU 개수", min_value=1, max_value=5, value=1) 
    
    for eq in st.session_state.equipments:
        rtu_num = int(eq['rtu'].split('-')[1])
        if rtu_num > rtu_count:
            eq['rtu'] = "RTU-1"

    st.subheader("2. 설비 추가")
    st.text_input("설비명", key='new_name')
    st.text_input("호기", key='new_desc')
    st.text_input("용량", key='new_kw')
    st.selectbox("구분",["기존설비", "효율설비", "연동설비"], key='new_type')
    st.checkbox("전력량계(W) 설치 (체크 해제 시 직접 연결)", key='new_has_w')
    
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
        new_type = c1.selectbox("구분",["기존설비", "효율설비", "연동설비"], index=["기존설비", "효율설비", "연동설비"].index(eq['type']), key=f"t_{i}")
        current_rtu_idx = rtu_list.index(eq['rtu']) if eq['rtu'] in rtu_list else 0
        new_rtu = c2.selectbox("RTU", rtu_list, index=current_rtu_idx, key=f"r_{i}")

        if new_type != eq['type'] or new_rtu != eq['rtu']:
            st.session_state.equipments[i]['type'] = new_type
            st.session_state.equipments[i]['rtu'] = new_rtu
            st.rerun()

# ==========================================
# 3. 다이어그램 렌더링 
# ==========================================
with col2:
    if st.session_state.equipments:
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.6', ranksep='0.9')
        dot.attr('node', fontname='NanumGothic', fontsize='10')

        comm_color = 'red' if theme == "커스텀 아이콘 (버전 2)" else 'blue'

        # ----------------------------------------
        # [노드 생성 함수] 이미지 절대 경로 인식 및 오류 디버깅 추가
        # ----------------------------------------
        def draw_node(node_id, label, v1_shape, v1_color, v2_img, v2_w, v2_h):
            if theme == "커스텀 아이콘 (버전 2)":
                if v2_img == 'PROCESS_PILL':
                    # 공정 노드는 이미지 없이 알약 모양
                    dot.node(node_id, label, shape='box', style='rounded,filled', fillcolor='#E0E0E0', width='1.5', height='0.5')
                else:
                    # [해결 핵심] 서버 컴퓨터 환경에 맞게 정확한 파일 주소(절대 경로) 조합
                    img_path = os.path.join(BASE_DIR, v2_img).replace('\\', '/')
                    
                    # 파일이 서버에 실제로 존재하는지 확인!
                    if os.path.exists(img_path):
                        dot.node(node_id, label, shape='none', image=img_path, labelloc='b', imagescale='true', fixedsize='true', width=v2_w, height=v2_h)
                    else:
                        # ⚠️ 만약 파일명 오타 등으로 못 찾으면 빨간색 에러 상자를 띄워줌
                        dot.node(node_id, f"[이미지 누락]\n{v2_img}", shape='box', color='red', fontcolor='red')
            else:
                # 버전 1 
                if v1_shape == 'bold_square': 
                    dot.node(node_id, label, shape='square', color='coral', fontcolor='red', style='bold,filled', fillcolor='white', width='0.3')
                else:
                    dot.node(node_id, label, shape=v1_shape, style='filled', fillcolor=v1_color, width='1.0' if v1_shape=='box' else '0.4')

        # 1. 상단 핵심 노드 배치
        draw_node('KEPCO', '한전' if theme == "기본 도형 (버전 1)" else '', 'box', '#FFD700', '한전.png', '1.2', '0.5')
        draw_node('MOF', 'MOF' if theme == "기본 도형 (버전 1)" else '', 'box', '#E0E0E0', 'MOF.png', '1.2', '0.5')
        draw_node('EER', 'EER 서버\n(한국에너지공단)' if theme == "기본 도형 (버전 1)" else '', 'box', '#ADD8E6', 'EER.png', '1.5', '1.0')

        dot.edge('KEPCO', 'MOF')
        dot.edge('MOF', 'EER', style='dashed', color='saddlebrown')

        # 2. 공정과 RTU 배치
        with dot.subgraph() as s_mid:
            s_mid.attr(rank='same')
            draw_node('PROCESS', process_name, 'box', '#E0E0E0', 'PROCESS_PILL', '1.5', '0.5')
            
            rtu_nodes =[]
            for r in range(rtu_count):
                rtu_name = f"RTU-{r+1}"
                draw_node(rtu_name, 'R' if theme == "기본 도형 (버전 1)" else '', 'bold_square', 'white', 'RTU.png', '0.8', '0.8')
                rtu_nodes.append(rtu_name)
            
            if rtu_count > 0:
                s_mid.edge('PROCESS', rtu_nodes[0], style='invis')
                for r in range(rtu_count - 1):
                    s_mid.edge(rtu_nodes[r], rtu_nodes[r+1], style='invis')

        dot.edge('MOF', 'PROCESS')
        for r in range(rtu_count):
            rtu_name = f"RTU-{r+1}"
            dot.edge('MOF', rtu_name, style='dashed', color='saddlebrown')
            dot.edge(rtu_name, 'EER', style='dashed', color='red')

        # 3. 설비 클러스터 영역
        with dot.subgraph(name='cluster_equip') as c:
            c.attr(style='dashed', color='gray') 
            color_map = {"기존설비": "#B0C4DE", "효율설비": "#C1E1C1", "연동설비": "#B0C4DE"} 
            
            with c.subgraph() as s_w:
                s_w.attr(rank='same')
                for i, eq in enumerate(st.session_state.equipments):
                    if eq['has_w']:
                        draw_node(f'W_{i}', 'W' if theme == "기본 도형 (버전 1)" else '', 'circle', 'white', '전력량계.png', '0.6', '0.6')
                    else:
                        s_w.node(f'W_{i}', '', shape='none', width='0', height='0')

            with c.subgraph() as s_eq:
                s_eq.attr(rank='same')
                for i, eq in enumerate(st.session_state.equipments):
                    eq_label = f"{eq['name']}\n{eq['desc']}\n({eq['kw']})"
                    
                    if theme == "커스텀 아이콘 (버전 2)":
                        img_file = '효율공기압축기.png' if eq['type'] == '효율설비' else '기존공기압축기.png'
                        draw_node(f'EQ_{i}', eq_label, '', '', img_file, '1.2', '1.0')
                    else:
                        bg_color = color_map.get(eq['type'])
                        draw_node(f'EQ_{i}', eq_label, 'box', bg_color, '', '', '')
                
                for i in range(len(st.session_state.equipments) - 1):
                    s_eq.edge(f'EQ_{i}', f'EQ_{i+1}', style='invis')

            # 실제 선 연결
            for i, eq in enumerate(st.session_state.equipments):
                if eq['has_w']:
                    dot.edge('PROCESS', f'W_{i}', weight='10')
                    c.edge(f'W_{i}', f'EQ_{i}', weight='10')
                    dot.edge(eq['rtu'], f'W_{i}', style='solid' if theme == "커스텀 아이콘 (버전 2)" else 'dashed', color=comm_color, constraint='false')
                else:
                    dot.edge('PROCESS', f'EQ_{i}', weight='10')

           png_data = dot.pipe(format='png')
        
            # [핵심] Graphviz 차트 대신, 완성된 사진(png_data)을 화면에 직접 띄웁니다!
            st.image(png_data, use_container_width=True) 
        
            st.download_button("📥 이미지 다운로드", data=png_data, file_name="계측구성도.png", mime="image/png")
        else:
            st.info("👈 왼쪽 패널에서 설비를 추가하면 구성도가 나타납니다.")
