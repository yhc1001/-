import streamlit as st
import graphviz
import os
import shutil
import tempfile

st.set_page_config(page_title="계측구성도 설계기", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPHVIZ_ASSET_PATH = os.path.join(tempfile.gettempdir(), "meter_diagram_graphviz_assets")
IMAGE_ALIASES = {
    'EER.png': 'eer.png',
    'MOF.png': 'mof.png',
    'RTU.png': 'rtu.png',
    '한전.png': 'kepco.png',
    '전력량계.png': 'wattmeter.png',
    '기존공기압축기.png': 'compressor_existing.png',
    '효율공기압축기.png': 'compressor_efficiency.png',
}

def ensure_graphviz_assets():
    os.makedirs(GRAPHVIZ_ASSET_PATH, exist_ok=True)
    for source_name, alias_name in IMAGE_ALIASES.items():
        source_path = os.path.join(BASE_DIR, source_name)
        alias_path = os.path.join(GRAPHVIZ_ASSET_PATH, alias_name)
        if (
            os.path.exists(source_path)
            and (
                not os.path.exists(alias_path)
                or os.path.getmtime(source_path) > os.path.getmtime(alias_path)
            )
        ):
            shutil.copyfile(source_path, alias_path)

def graphviz_image_name(image_name):
    alias_name = IMAGE_ALIASES.get(image_name, image_name)
    return os.path.join(GRAPHVIZ_ASSET_PATH, alias_name).replace('\\', '/')

ensure_graphviz_assets()

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

def make_legend_label(legend_scale):
    font_size = max(7, int(10 * legend_scale))
    icon_size = max(12, int(18 * legend_scale))
    return f'''<
<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="2" CELLPADDING="3">
  <TR>
    <TD WIDTH="{icon_size}" HEIGHT="{icon_size}"><FONT POINT-SIZE="{font_size}">W</FONT></TD>
    <TD ALIGN="LEFT"><FONT POINT-SIZE="{font_size}">전력량계</FONT></TD>
  </TR>
  <TR>
    <TD WIDTH="{icon_size}" HEIGHT="{icon_size}"><FONT POINT-SIZE="{font_size}" COLOR="red">R</FONT></TD>
    <TD ALIGN="LEFT"><FONT POINT-SIZE="{font_size}">RTU</FONT></TD>
  </TR>
  <TR>
    <TD WIDTH="{icon_size}" HEIGHT="{icon_size}" BGCOLOR="#B0C4DE"></TD>
    <TD ALIGN="LEFT"><FONT POINT-SIZE="{font_size}">기존설비</FONT></TD>
  </TR>
  <TR>
    <TD WIDTH="{icon_size}" HEIGHT="{icon_size}" BGCOLOR="#C1E1C1"></TD>
    <TD ALIGN="LEFT"><FONT POINT-SIZE="{font_size}">효율설비</FONT></TD>
  </TR>
  <TR>
    <TD WIDTH="{icon_size}" HEIGHT="{icon_size}" BGCOLOR="#D3D3D3"></TD>
    <TD ALIGN="LEFT"><FONT POINT-SIZE="{font_size}">연동설비</FONT></TD>
  </TR>
</TABLE>
>'''

# ==========================================
# 2. 메인 화면 레이아웃
# ==========================================
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("🎨 디자인 테마 선택")
    theme = st.radio("테마",["기본 도형 (버전 1)", "커스텀 아이콘 (버전 2)"], horizontal=True, label_visibility="collapsed")
    
    with st.expander("도면 세부 조정", expanded=True):
        legend_scale = st.slider("범례 크기", min_value=0.55, max_value=1.00, value=0.70, step=0.05)
        show_boundary = st.checkbox("사업장 경계 표시", value=True)
        boundary_margin = st.slider("사업장 경계 여백", min_value=0, max_value=40, value=10, step=2)
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
        # 🟢[버전 1] 기본 도형 테마
        # ---------------------------------------------------------
        if theme == "기본 도형 (버전 1)":
            dot = graphviz.Digraph(format='png')
            dot.attr(newrank='true') 
            dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.15', ranksep='0.5')
            dot.attr('node', fontname='NanumGothic', shape='box', style='filled', fillcolor='white', fontsize='9')

            dot.node('LEGEND', make_legend_label(legend_scale), shape='plain')

            with dot.subgraph() as top_align:
                top_align.attr(rank='same')
                top_align.node('LEGEND') 
                top_align.node('KEPCO', '한전', fillcolor='#FFD700', width='1.0')
                top_align.edge('LEGEND', 'KEPCO', style='invis', minlen='4')

            dot.node('MOF', 'MOF', fillcolor='#E0E0E0', width='1.0')
            dot.edge('KEPCO', 'MOF', weight='100')

            with dot.subgraph() as s_mid:
                s_mid.attr(rank='same')
                s_mid.node('PROCESS', process_name, fillcolor='#E0E0E0', width='1.0')
                
                rtu_nodes =[]
                for r in range(rtu_count):
                    rtu_name = f"RTU-{r+1}"
                    s_mid.node(rtu_name, 'R', shape='square', color='coral', fontcolor='red', style='bold,filled', fillcolor='white', width='0.3')
                    rtu_nodes.append(rtu_name)
                
                s_mid.node('EER', 'EER 서버\n(한국에너지공단)', fillcolor='#ADD8E6', width='1.2')
                
                if rtu_count > 0:
                    s_mid.edge('PROCESS', rtu_nodes[0], style='invis', minlen='2')
                    for r in range(rtu_count - 1):
                        s_mid.edge(rtu_nodes[r], rtu_nodes[r+1], style='invis', minlen='1')
                    s_mid.edge(rtu_nodes[-1], 'EER', style='invis', minlen='2')
                else:
                    s_mid.edge('PROCESS', 'EER', style='invis', minlen='3')

            dot.edge('MOF', 'PROCESS', weight='100')
            
            # [수정 1] 불필요한 MOF->RTU, MOF->EER 점선 삭제 (데이터 흐름 최적화)
            for r in range(rtu_count):
                rtu_name = f"RTU-{r+1}"
                # 통신선: RTU -> EER 서버만 유지
                dot.edge(rtu_name, 'EER', style='dashed', color='saddlebrown', constraint='false') 

            with dot.subgraph(name='cluster_equip') as c:
                boundary_style = 'dashed' if show_boundary else 'invis'
                c.attr(style=boundary_style, color='gray', margin=str(boundary_margin)) 
                color_map = {"기존설비": "#B0C4DE", "효율설비": "#C1E1C1", "연동설비": "#D3D3D3"} 
                
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
                        dot.edge('PROCESS', f'W_{i}') 
                        c.edge(f'W_{i}', f'EQ_{i}', weight='100') 
                        dot.edge(eq['rtu'], f'W_{i}', style='dashed', color='blue', constraint='false')
                    else:
                        dot.edge('PROCESS', f'EQ_{i}')

            st.graphviz_chart(dot)
            st.download_button("📥 이미지 다운로드 (버전 1)", data=dot.pipe(format='png'), file_name="계측구성도_버전1.png", mime="image/png")


        # ---------------------------------------------------------
        # 🔴 [버전 2] 캔바 커스텀 아이콘 테마
        # ---------------------------------------------------------
        else:
            dot = graphviz.Digraph(format='png')
            dot.attr(newrank='true')
            dot.attr(rankdir='TB', splines='ortho', fontname='NanumGothic', nodesep='0.15', ranksep='0.5')
            dot.attr('node', fontname='NanumGothic', fontsize='10')

            def draw_v2_node(node_id, label, v2_img, v2_w, v2_h):
                if v2_img == 'PROCESS_PILL':
                    dot.node(node_id, label, shape='box', style='rounded,filled', fillcolor='#E0E0E0', width='1.5', height='0.5')
                else:
                    img_path = os.path.join(BASE_DIR, v2_img)
                    image_name = graphviz_image_name(v2_img)
                    if os.path.exists(img_path):
                        dot.node(node_id, label, shape='none', image=image_name, labelloc='b', imagescale='true', fixedsize='true', width=v2_w, height=v2_h)
                    else:
                        dot.node(node_id, f"[이미지 누락]\n{v2_img}", shape='box', color='red', fontcolor='red')

            dot.node('LEGEND', make_legend_label(legend_scale), shape='plain')

            with dot.subgraph() as top_align:
                top_align.attr(rank='same')
                top_align.node('LEGEND') 
                
                img_path = os.path.join(BASE_DIR, '한전.png')
                if os.path.exists(img_path):
                    top_align.node('KEPCO', '', shape='none', image=graphviz_image_name('한전.png'), labelloc='b', imagescale='true', fixedsize='true', width='1.2', height='0.6')
                else:
                    top_align.node('KEPCO', "[이미지 누락]\n한전.png", shape='box', color='red', fontcolor='red')
                
                top_align.edge('LEGEND', 'KEPCO', style='invis', minlen='4')

            draw_v2_node('MOF', '', 'MOF.png', '1.2', '0.6')
            dot.edge('KEPCO', 'MOF', weight='100')

            with dot.subgraph() as s_mid:
                s_mid.attr(rank='same')
                draw_v2_node('PROCESS', process_name, 'PROCESS_PILL', '1.5', '0.5')
                
                rtu_nodes =[]
                for r in range(rtu_count):
                    rtu_name = f"RTU-{r+1}"
                    draw_v2_node(rtu_name, '', 'RTU.png', '0.8', '0.8')
                    rtu_nodes.append(rtu_name)
                
                draw_v2_node('EER', '', 'EER.png', '1.5', '1.0')
                
                if rtu_count > 0:
                    s_mid.edge('PROCESS', rtu_nodes[0], style='invis', minlen='3')
                    for r in range(rtu_count - 1):
                        s_mid.edge(rtu_nodes[r], rtu_nodes[r+1], style='invis', minlen='2')
                    s_mid.edge(rtu_nodes[-1], 'EER', style='invis', minlen='3')
                else:
                    s_mid.edge('PROCESS', 'EER', style='invis', minlen='4')

            dot.edge('MOF', 'PROCESS', weight='100')
            
            # [수정 1] 불필요한 MOF 점선 삭제 (테마 2도 동일 적용)
            for r in range(rtu_count):
                rtu_name = f"RTU-{r+1}"
                dot.edge(rtu_name, 'EER', style='dashed', color='red', constraint='false')

            with dot.subgraph(name='cluster_equip') as c:
                boundary_style = 'dashed' if show_boundary else 'invis'
                c.attr(style=boundary_style, color='gray', margin=str(boundary_margin)) 
                
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
                        s_eq.edge(f'EQ_{i}', f'EQ_{i+1}', style='invis', minlen='3')

                for i, eq in enumerate(st.session_state.equipments):
                    if eq['has_w']:
                        dot.edge('PROCESS', f'W_{i}')
                        c.edge(f'W_{i}', f'EQ_{i}', weight='100')
                        dot.edge(eq['rtu'], f'W_{i}', style='solid', color='red', constraint='false')
                    else:
                        dot.edge('PROCESS', f'EQ_{i}')

            png_data = dot.pipe(format='png')
            st.image(png_data, use_container_width=False) 
            st.download_button("📥 이미지 다운로드 (버전 2)", data=png_data, file_name="계측구성도_버전2.png", mime="image/png")

    else:
        st.info("👈 왼쪽 패널에서 설비를 추가하면 구성도가 나타납니다.")
