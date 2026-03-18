import streamlit as st
import graphviz
import os

st.set_page_config(page_title="계측구성도 설계기", layout="wide")

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

def reset_all():
    st.session_state.equipments =[]
    st.session_state.new_desc = "#1"

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
    st.button("🗑️ 전체 초기화", on_click=reset_all)

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
        
        # ---------------------------------------------------------
        # 🟢 [버전 1] 기본 도형 테마
        # ---------------------------------------------------------
        if theme == "기본 도형 (버전 1)":
            dot = graphviz.Digraph(format='png')
            dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.4', ranksep='0.8')
            dot.attr('node', fontname='NanumGothic', shape='box', style='filled', fillcolor='white', fontsize='9')

            # --- [추가] 버전 1 범례(Legend) 세팅 ---
            with dot.subgraph(name='cluster_legend') as leg:
                leg.attr(label='범례', fontsize='11', fontname='NanumGothic', style='solid', color='black', margin='8')
                items =[('w', '전력량계'), ('r', 'RTU'), ('exist', '기존설비'), ('eff', '효율설비'), ('link', '연동설비')]
                
                for key, text in items:
                    with leg.subgraph() as row:
                        row.attr(rank='same')
                        if key == 'w': row.node(f'leg_i_{key}', 'W', shape='circle', width='0.3', style='filled', fillcolor='white')
                        elif key == 'r': row.node(f'leg_i_{key}', 'R', shape='square', color='coral', fontcolor='red', style='bold,filled', fillcolor='white', width='0.3')
                        elif key == 'exist': row.node(f'leg_i_{key}', '', shape='box', style='filled', fillcolor='#B0C4DE', width='0.4', height='0.3')
                        elif key == 'eff': row.node(f'leg_i_{key}', '', shape='box', style='filled', fillcolor='#C1E1C1', width='0.4', height='0.3')
                        elif key == 'link': row.node(f'leg_i_{key}', '', shape='box', style='filled', fillcolor='#B0C4DE', width='0.4', height='0.3')
                        
                        row.node(f'leg_t_{key}', text, shape='none', fontsize='10')
                        row.edge(f'leg_i_{key}', f'leg_t_{key}', style='invis') # 가로 정렬

                # 세로 줄 맞추기
                for i in range(len(items)-1):
                    leg.edge(f'leg_i_{items[i][0]}', f'leg_i_{items[i+1][0]}', style='invis')

            # --- 범례를 좌측 상단(한전 왼쪽)에 고정 ---
            with dot.subgraph() as top_align:
                top_align.attr(rank='same')
                top_align.node('KEPCO', '한전', fillcolor='#FFD700', width='1.0')
                top_align.edge('leg_t_w', 'KEPCO', style='invis', minlen='2') # 투명선으로 밀어내기

            dot.node('MOF', 'MOF', fillcolor='#E0E0E0', width='1.0')
            dot.edge('KEPCO', 'MOF')

            dot.node('EER', 'EER 서버\n(한국에너지공단)', fillcolor='#ADD8E6', width='1.2')
            dot.edge('MOF', 'EER', style='dashed', color='saddlebrown')

            with dot.subgraph() as s_mid:
                s_mid.attr(rank='same')
                s_mid.node('PROCESS', process_name, fillcolor='#E0E0E0', width='1.0')
                rtu_nodes =[]
                for r in range(rtu_count):
                    rtu_name = f"RTU-{r+1}"
                    s_mid.node(rtu_name, 'R', shape='square', color='coral', fontcolor='red', style='bold,filled', fillcolor='white', width='0.3')
                    rtu_nodes.append(rtu_name)
                
                if rtu_count > 0:
                    s_mid.edge('PROCESS', rtu_nodes[0], style='invis')
                    for r in range(rtu_count - 1):
                        s_mid.edge(rtu_nodes[r], rtu_nodes[r+1], style='invis')

            dot.edge('MOF', 'PROCESS')
            for r in range(rtu_count):
                rtu_name = f"RTU-{r+1}"
                dot.edge('MOF', rtu_name, style='dashed', color='saddlebrown')
                dot.edge(rtu_name, 'EER', style='dashed', color='saddlebrown')

            with dot.subgraph(name='cluster_equip') as c:
                c.attr(style='dashed', color='gray') 
                color_map = {"기존설비": "#B0C4DE", "효율설비": "#C1E1C1", "연동설비": "#B0C4DE"}
                
                with c.subgraph() as s_w:
                    s_w.attr(rank='same')
                    for i, eq in enumerate(st.session_state.equipments):
                        if eq['has_w']:
                            s_w.node(f'W_{i}', 'W', shape='circle', width='0.4')
                        else:
                            s_w.node(f'W_{i}', '', shape='none', width='0', height='0')

                with c.subgraph() as s_eq:
                    s_eq.attr(rank='same')
                    for i, eq in enumerate(st.session_state.equipments):
                        s_eq.node(f'EQ_{i}', f"{eq['name']}\n{eq['desc']}\n({eq['kw']})", 
                                  fillcolor=color_map.get(eq['type']), style='filled', shape='box', width='0.8')
                    
                    for i in range(len(st.session_state.equipments) - 1):
                        s_eq.edge(f'EQ_{i}', f'EQ_{i+1}', style='invis')

                for i, eq in enumerate(st.session_state.equipments):
                    if eq['has_w']:
                        dot.edge('PROCESS', f'W_{i}', weight='10')
                        c.edge(f'W_{i}', f'EQ_{i}', weight='10')
                        dot.edge(eq['rtu'], f'W_{i}', style='dashed', color='blue', constraint='false')
                    else:
                        dot.edge('PROCESS', f'EQ_{i}', weight='10')

            st.graphviz_chart(dot)
            st.download_button("📥 이미지 다운로드 (버전 1)", data=dot.pipe(format='png'), file_name="계측구성도_버전1.png", mime="image/png")


        # ---------------------------------------------------------
        # 🔴[버전 2] 캔바 커스텀 아이콘 테마
        # ---------------------------------------------------------
        else:
            dot = graphviz.Digraph(format='png')
            dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.6', ranksep='0.9', dpi='200')
            dot.attr('node', fontname='NanumGothic', fontsize='10')

            def draw_v2_node(node_id, label, v2_img, v2_w, v2_h):
                if v2_img == 'PROCESS_PILL':
                    dot.node(node_id, label, shape='box', style='rounded,filled', fillcolor='#E0E0E0', width='1.5', height='0.5')
                else:
                    img_path = os.path.join(BASE_DIR, v2_img).replace('\\', '/')
                    if os.path.exists(img_path):
                        dot.node(node_id, label, shape='none', image=img_path, labelloc='b', imagescale='true', fixedsize='true', width=v2_w, height=v2_h)
                    else:
                        dot.node(node_id, f"[이미지 누락]\n{v2_img}", shape='box', color='red', fontcolor='red')

            # --- [추가] 버전 2 범례(Legend) 아이콘 세팅 ---
            with dot.subgraph(name='cluster_legend') as leg:
                leg.attr(label='범례', fontsize='11', fontname='NanumGothic', style='solid', color='black', margin='8')
                items =[('w', '전력량계'), ('r', 'RTU'), ('exist', '기존설비'), ('eff', '효율설비'), ('link', '연동설비')]
                img_map = {'w': '전력량계.png', 'r': 'RTU.png', 'exist': '기존공기압축기.png', 'eff': '효율공기압축기.png', 'link': '기존공기압축기.png'}
                
                for key, text in items:
                    with leg.subgraph() as row:
                        row.attr(rank='same')
                        img_path = os.path.join(BASE_DIR, img_map[key]).replace('\\', '/')
                        if os.path.exists(img_path):
                            row.node(f'leg_i_{key}', '', shape='none', image=img_path, imagescale='true', fixedsize='true', width='0.4', height='0.4')
                        else:
                            row.node(f'leg_i_{key}', 'X', shape='box', color='red', width='0.3', height='0.3')
                        
                        row.node(f'leg_t_{key}', text, shape='none', fontsize='10')
                        row.edge(f'leg_i_{key}', f'leg_t_{key}', style='invis') # 가로 정렬

                # 세로 줄 맞추기
                for i in range(len(items)-1):
                    leg.edge(f'leg_i_{items[i][0]}', f'leg_i_{items[i+1][0]}', style='invis')

            # --- 범례를 좌측 상단(한전 왼쪽)에 고정 ---
            with dot.subgraph() as top_align:
                top_align.attr(rank='same')
                draw_v2_node('KEPCO', '', '한전.png', '1.2', '0.6')
                top_align.edge('leg_t_w', 'KEPCO', style='invis', minlen='2') # 투명선으로 밀어내기

            draw_v2_node('MOF', '', 'MOF.png', '1.2', '0.6')
            draw_v2_node('EER', '', 'EER.png', '1.5', '1.0')

            dot.edge('KEPCO', 'MOF')
            dot.edge('MOF', 'EER', style='dashed', color='saddlebrown')

            with dot.subgraph() as s_mid:
                s_mid.attr(rank='same')
                draw_v2_node('PROCESS', process_name, 'PROCESS_PILL', '1.5', '0.5')
                
                rtu_nodes =[]
                for r in range(rtu_count):
                    rtu_name = f"RTU-{r+1}"
                    draw_v2_node(rtu_name, '', 'RTU.png', '0.8', '0.8')
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

            with dot.subgraph(name='cluster_equip') as c:
                c.attr(style='dashed', color='gray') 
                
                with c.subgraph() as s_w:
                    s_w.attr(rank='same')
                    for i, eq in enumerate(st.session_state.equipments):
                        if eq['has_w']:
                            draw_v2_node(f'W_{i}', '', '전력량계.png', '0.6', '0.6')
                        else:
                            s_w.node(f'W_{i}', '', shape='none', width='0', height='0')

                with c.subgraph() as s_eq:
                    s_eq.attr(rank='same')
                    for i, eq in enumerate(st.session_state.equipments):
                        eq_label = f"{eq['name']}\n{eq['desc']}\n({eq['kw']})"
                        img_file = '효율공기압축기.png' if eq['type'] == '효율설비' else '기존공기압축기.png'
                        draw_v2_node(f'EQ_{i}', eq_label, img_file, '1.2', '1.0')
                    
                    for i in range(len(st.session_state.equipments) - 1):
                        s_eq.edge(f'EQ_{i}', f'EQ_{i+1}', style='invis')

                for i, eq in enumerate(st.session_state.equipments):
                    if eq['has_w']:
                        dot.edge('PROCESS', f'W_{i}', weight='10')
                        c.edge(f'W_{i}', f'EQ_{i}', weight='10')
                        dot.edge(eq['rtu'], f'W_{i}', style='solid', color='red', constraint='false')
                    else:
                        dot.edge('PROCESS', f'EQ_{i}', weight='10')

            png_data = dot.pipe(format='png')
            st.image(png_data) 
            st.download_button("📥 이미지 다운로드 (버전 2)", data=png_data, file_name="계측구성도_버전2.png", mime="image/png")

    else:
        st.info("👈 왼쪽 패널에서 설비를 추가하면 구성도가 나타납니다.")
