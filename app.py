import streamlit as st
import pandas as pd
from github import Github
import io

# --- 1. ตั้งค่าหน้าเว็บ (บังคับเปิด Sidebar) ---
st.set_page_config(
    page_title="Inventory System", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# ==========================================
# 2. ระบบจัดการ THEME & COLOR PALETTE
# ==========================================
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# กำหนดชุดสีแบบตายตัว (Fixed Palette) ตามที่ User ต้องการ
if st.session_state.theme == 'dark':
    # --- Dark Mode ---
    colors = {
        'bg_app': '#262730',         # พื้นหลัง App (เทาเข้ม)
        'bg_sidebar': '#1e1e1e',     # พื้นหลัง Sidebar
        'text_main': '#ffffff',      # สีตัวหนังสือหลัก (ขาว)
        'input_bg': '#4a4a4a',       # พื้นช่องค้นหา
        'input_text': '#ffffff',     # สีตัวหนังสือช่องค้นหา
        'header_bg': '#262730',      # พื้น Header
        
        # สีตาราง
        'table_bg_norm': '#262730',  # แถวปกติ (เทาเข้มเหมือนพื้น)
        'table_txt_norm': '#ffffff', # ตัวหนังสือแถวปกติ (ขาว)
        
        'table_bg_hightlight': '#fff9c4', # แถวที่เน้น (เหลืองอ่อน)
        'table_txt_highlight': '#000000'  # ตัวหนังสือแถวเน้น (กลับเป็นดำ เพื่อให้อ่านบนพื้นเหลืองได้)
    }
else:
    # --- Light Mode (Default) ---
    colors = {
        'bg_app': '#f0f2f6',         # พื้นหลัง App (เทาอ่อน สบายตา)
        'bg_sidebar': '#ffffff',     # พื้นหลัง Sidebar (ขาว)
        'text_main': '#31333f',      # สีตัวหนังสือหลัก (เทาเข้มเกือบดำ)
        'input_bg': '#ffffff',       # พื้นช่องค้นหา
        'input_text': '#000000',     # สีตัวหนังสือช่องค้นหา
        'header_bg': '#f0f2f6',      # พื้น Header
        
        # สีตาราง
        'table_bg_norm': '#ffffff',  # แถวปกติ (ขาว)
        'table_txt_norm': '#31333f', # ตัวหนังสือปกติ (เทาเข้ม)
        
        'table_bg_hightlight': '#e6e9ef', # แถวที่เน้น (เทาฟ้าจางๆ)
        'table_txt_highlight': '#31333f'  # ตัวหนังสือ
    }

# --- 3. CSS Injection (บังคับค่าสีทุกจุด) ---
st.markdown(
    f"""
    <style>
    /* 1. พื้นหลังหลัก */
    .stApp {{
        background-color: {colors['bg_app']};
        color: {colors['text_main']};
    }}
    
    /* 2. พื้นหลัง Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {colors['bg_sidebar']};
    }}
    
    /* 3. Sticky Header */
    .sticky-top-container {{
        position: sticky;
        top: 0;
        z-index: 990;
        background-color: {colors['header_bg']};
        padding: 10px 0;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    }}
    
    /* 4. ช่องค้นหา (Input Box) */
    div[data-baseweb="input"] {{
        background-color: {colors['input_bg']} !important;
        border: 1px solid #888 !important;
        border-radius: 5px !important;
    }}
    
    /* ตัวหนังสือในช่องค้นหา */
    input[type="text"] {{
        color: {colors['input_text']} !important;
        caret-color: {colors['input_text']} !important;
    }}
    
    /* Header ของตาราง */
    thead tr th {{
        background-color: {colors['bg_app']} !important;
        color: {colors['text_main']} !important;
    }}
    
    /* ข้อความทั่วไป */
    h1, h2, h3, p, div, span, label {{
        color: {colors['text_main']};
    }}
    
    </style>
    """,
    unsafe_allow_html=True
)

# --- Config & Functions ---
TARGET_FILE_NAME = "InvLotFrmByLot.xlsx" 

def fix_thai_encoding(text):
    if not isinstance(text, str): return text
    try: return text.encode('cp1252').decode('cp874')
    except: return text

def upload_to_github(file_content):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]
        g = Github(token)
        repo = g.get_repo(repo_name)
        try:
            contents = repo.get_contents(TARGET_FILE_NAME)
            repo.update_file(contents.path, "Update data", file_content, contents.sha)
            return True, "อัปเดตสำเร็จ!"
        except:
            repo.create_file(TARGET_FILE_NAME, "Initial upload", file_content)
            return True, "สร้างไฟล์ใหม่สำเร็จ!"
    except Exception as e:
        return False, f"GitHub Error: {str(e)}"

@st.cache_data(ttl=0)
def load_data_from_github():
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]
        g = Github(token)
        repo = g.get_repo(repo_name)
        contents = repo.get_contents(TARGET_FILE_NAME)
        file_content = contents.decoded_content
        try: df = pd.read_excel(io.BytesIO(file_content))
        except: df = pd.read_excel(io.BytesIO(file_content), engine='xlrd')
        
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(fix_thai_encoding)
        df.columns = [fix_thai_encoding(c) for c in df.columns]
        return df
    except Exception as e:
        return None

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.header("⚙️ การแสดงผล")
    
    # Theme Switcher
    is_dark = st.session_state.theme == 'dark'
    if st.toggle("🌙 โหมดกลางคืน (Dark Mode)", value=is_dark):
        st.session_state.theme = 'dark'
        st.rerun() # รีโหลดหน้าทันทีเพื่อเปลี่ยนสี
    else:
        if st.session_state.theme == 'dark': # ถ้าเปลี่ยนจาก dark -> light
            st.session_state.theme = 'light'
            st.rerun()

    st.divider()
    
    st.header("🔐 Admin")
    if "logged_in" not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        password = st.text_input("รหัสผ่าน", type="password")
        if password == "rb,kp@10884":
            st.session_state.logged_in = True
            st.success("Login สำเร็จ")
            st.rerun()
    else:
        st.success("สถานะ: Admin")
        st.write("📥 **อัปโหลดไฟล์ Excel**")
        uploaded_file = st.file_uploader("เลือกไฟล์", type=['xlsx', 'xls'])
        if uploaded_file and st.button("บันทึกข้อมูล"):
            with st.status("กำลังบันทึก...", expanded=True) as status:
                success, msg = upload_to_github(uploaded_file.getvalue())
                if success:
                    status.update(label="✅ สำเร็จ", state="complete")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)
        
        if st.button("ออกจากระบบ"):
            st.session_state.logged_in = False
            st.rerun()

# ==========================================
# MAIN CONTENT
# ==========================================
with st.spinner('Loading...'):
    df = load_data_from_github()

report_date_str = "-"

if df is not None:
    df.columns = df.columns.astype(str).str.strip()
    if 'd1' in df.columns and not df.empty:
        try:
            raw = df['d1'].iloc[0]
            if isinstance(raw, pd.Timestamp): report_date_str = raw.strftime('%d/%m/%Y')
            else: report_date_str = str(raw)
        except: pass

    trade_col = next((c for c in df.columns if c.lower().replace(" ", "") == "tradename"), None)
    df['TradeName'] = df[trade_col].fillna("-") if trade_col else "-"
    df['LotNo'] = df.get('LotNo', pd.Series(['-']*len(df))).fillna("-")
    df['price'] = df.get('price', pd.Series([0]*len(df))).fillna(0)
    
    df['DisplayName'] = ""
    if 'NAME1' in df.columns: df['DisplayName'] += df['NAME1'].fillna("").astype(str) + " "
    if 'CONTENT' in df.columns: df['DisplayName'] += df['CONTENT'].fillna("").astype(str) + " "
    if 'TYPE' in df.columns: df['DisplayName'] += df['TYPE'].fillna("").astype(str)
    df['DisplayName'] = df['DisplayName'].str.strip()

    amt = df['Amount1'].astype(str) if 'Amount1' in df.columns else "0"
    unit = df['minofLotPack'].astype(str) if 'minofLotPack' in df.columns else ""
    df['QtyDisplay'] = amt + " x " + unit

# --- Header & Search ---
st.markdown('<div class="sticky-top-container">', unsafe_allow_html=True)
c1, c2 = st.columns([0.6, 0.4])
with c1:
    st.markdown(f"### 🏥 คลังยา (วันที่: {report_date_str})")
with c2:
    st.markdown('<span style="font-size:0.9rem; font-weight:bold;">🔍 ค้นหารายการ:</span>', unsafe_allow_html=True)
    search_query = st.text_input("Search", placeholder="ชื่อยา, รหัส...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# --- Table ---
if df is not None:
    if search_query:
        mask = (
            df['DisplayName'].str.contains(search_query, case=False, na=False) |
            df.get('CODE1', pd.Series(['']*len(df))).astype(str).str.contains(search_query, case=False, na=False) |
            df['TradeName'].str.contains(search_query, case=False, na=False) |
            df['LotNo'].astype(str).str.contains(search_query, case=False, na=False)
        )
        display_df = df[mask]
    else:
        display_df = df

    if not display_df.empty:
        cols_map = {'DisplayName': 'ชื่อรายการ', 'CODE1': 'รหัส', 'TradeName': 'Tradename', 'QtyDisplay': 'คงเหลือ', 'price': 'ทุน', 'LotNo': 'Lot', 'ExpDate': 'EXP'}
        valid_cols = [c for c in cols_map.keys() if c in display_df.columns]
        table = display_df[valid_cols].copy().rename(columns=cols_map)
        final_cols = [c for c in ['ชื่อรายการ', 'รหัส', 'Tradename', 'คงเหลือ', 'ทุน', 'Lot', 'EXP'] if c in table.columns]
        table = table[final_cols].reset_index(drop=True)

        # --- Coloring Logic (Pandas Styler) ---
        group_ids = (table['ชื่อรายการ'] != table['ชื่อรายการ'].shift()).cumsum()
        
        # แยกแถวเป็น 2 กลุ่ม: กลุ่มปกติ (Normal) / กลุ่มเน้น (Highlight)
        rows_highlight = table.index[group_ids % 2 == 1]
        rows_normal = table.index[group_ids % 2 == 0]

        styler = table.style.format(precision=2)
        if 'EXP' in table.columns: 
            styler = styler.format({'EXP': lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "-"})
        if 'ทุน' in table.columns: 
            styler = styler.format({'ทุน': '{:,.2f}'})

        # 1. กลุ่ม Highlight (สีเหลืองอ่อนใน Dark Mode / เทาฟ้าใน Light Mode)
        styler = styler.set_properties(
            subset=pd.IndexSlice[rows_highlight, :], 
            **{
                'background-color': colors['table_bg_hightlight'],
                'color': colors['table_txt_highlight'] # บังคับสีตัวหนังสือให้ตัดกับพื้นหลัง
            }
        )
        
        # 2. กลุ่ม Normal (สีตาม Theme)
        styler = styler.set_properties(
            subset=pd.IndexSlice[rows_normal, :], 
            **{
                'background-color': colors['table_bg_norm'],
                'color': colors['table_txt_norm']
            }
        )

        st.dataframe(styler, use_container_width=True, hide_index=True, height=600)
    else:
        st.warning(f"ไม่พบข้อมูล '{search_query}'")
else:
    st.info("กรุณา Login เพื่ออัปโหลดข้อมูล")
