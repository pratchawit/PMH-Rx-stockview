import streamlit as st
import pandas as pd
from github import Github
import io
import os

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Inventory System", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. จัดการ THEME (Hybrid System)
# ==========================================
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# กำหนดสีพื้นหลังหลัก (Main Background)
if st.session_state.theme == 'dark':
    main_bg = '#262730'      # พื้นหลังสีเทาเข้ม
    main_text = '#ffffff'    # ตัวหนังสือหัวข้อสีขาว
    header_bg = '#262730'    # Header สีเดียวกับพื้นหลัง
else:
    main_bg = '#f0f2f6'      # พื้นหลังสีเทาอ่อนสบายตา
    main_text = '#31333f'    # ตัวหนังสือหัวข้อสีเทาเข้ม
    header_bg = '#f0f2f6'

# --- Fixed Colors (สีที่บังคับให้เหมือนเดิมตลอดกาล) ---
fixed_colors = {
    'sidebar_bg': '#f8fafc',     # Sidebar สีเทาขาวเสมอ
    'sidebar_text': '#1e293b',   # Sidebar ตัวหนังสือเข้มเสมอ
    'input_bg': '#ffffff',       # ช่องค้นหา/Login ขาวเสมอ
    'input_text': '#000000',     # ตัวหนังสือในช่องค้นหาดำเสมอ
    'table_bg_norm': '#ffffff',  # ตารางพื้นขาว
    'table_bg_alt': '#f1f5f9',   # ตารางสลับสีเทาอ่อน
    'table_text': '#1e293b'      # ตัวหนังสือในตารางสีเข้ม
}

# --- CSS Injection (แก้บั๊ก Input สีดำ) ---
st.markdown(
    f"""
    <style>
    /* 1. พื้นหลังหลัก */
    .stApp {{
        background-color: {main_bg};
        color: {main_text};
    }}
    
    /* 2. Sidebar (Fix: Light Mode เสมอ) */
    section[data-testid="stSidebar"] {{
        background-color: {fixed_colors['sidebar_bg']};
    }}
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label {{
        color: {fixed_colors['sidebar_text']} !important;
    }}
    
    /* 3. แก้ไข Input Fields (Login & Search) ให้เป็นขาว/ดำ เสมอ */
    /* กรอบของ Input */
    div[data-baseweb="input"] {{
        background-color: {fixed_colors['input_bg']} !important;
        border: 1px solid #ccc !important;
        border-radius: 6px !important;
    }}
    /* ตัวหนังสือภายใน Input */
    input[type="text"], input[type="password"] {{
        color: {fixed_colors['input_text']} !important;
        -webkit-text-fill-color: {fixed_colors['input_text']} !important;
        caret-color: {fixed_colors['input_text']} !important;
        background-color: {fixed_colors['input_bg']} !important;
    }}
    
    /* 4. Sticky Header */
    .sticky-top-container {{
        position: sticky;
        top: 0;
        z-index: 990;
        background-color: {header_bg};
        padding: 10px 20px;
        border-bottom: 1px solid rgba(128,128,128, 0.2);
        margin-left: -1rem;
        margin-right: -1rem;
    }}
    
    /* 5. Typography */
    .app-title {{
        font-size: 1.8rem;
        font-weight: 800;
        color: {main_text};
        margin-bottom: 5px;
    }}
    .search-label {{
        font-weight: bold; 
        margin-bottom: 5px; 
        font-size: 1.1rem;
        color: {main_text};
    }}
    
    header[data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0);
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
    st.title("⚙️ เมนูหลัก")
    
    # Theme Toggle (เปลี่ยนชื่อปุ่มแล้ว)
    st.write("**การแสดงผล**")
    is_dark = st.session_state.theme == 'dark'
    if st.toggle("🌙 Dark mode", value=is_dark):
        st.session_state.theme = 'dark'
        st.rerun()
    else:
        if st.session_state.theme == 'dark':
            st.session_state.theme = 'light'
            st.rerun()
        
    st.divider()
    
    # Login System
    st.write("🔐 **สำหรับเจ้าหน้าที่**")
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        # Input ตรงนี้จะกลายเป็นสีขาว ตัวหนังสือดำ ตาม CSS ใหม่
        password = st.text_input("รหัสผ่าน Admin", type="password")
        if password == "rb,kp@10884":
            st.session_state.logged_in = True
            st.success("✅ เข้าสู่ระบบแล้ว")
            st.rerun()
    else:
        st.info(f"สถานะ: Admin")
        st.markdown("---")
        st.write("📥 **อัปเดตฐานข้อมูล**")
        uploaded_file = st.file_uploader("เลือกไฟล์ Excel", type=['xlsx', 'xls'])
        
        if uploaded_file:
            if st.button("🚀 อัปโหลดขึ้น Server", type="primary"):
                with st.status("กำลังดำเนินการ...", expanded=True) as status:
                    success, msg = upload_to_github(uploaded_file.getvalue())
                    if success:
                        status.update(label="✅ สำเร็จ", state="complete")
                        st.success(msg)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        status.update(label="❌ ล้มเหลว", state="error")
                        st.error(msg)
        
        if st.button("ออกจากระบบ"):
            st.session_state.logged_in = False
            st.rerun()

# ==========================================
# MAIN CONTENT
# ==========================================
with st.spinner('กำลังโหลดข้อมูล...'):
    df = load_data_from_github()

report_date_str = "-"

if df is not None:
    df.columns = df.columns.astype(str).str.strip()
    
    if 'd1' in df.columns and not df.empty:
        try:
            raw = df['d1'].iloc[0]
            if isinstance(raw, pd.Timestamp): report_date_str = raw.strftime('%d/%m/%Y')
            else: 
                try: report_date_str = pd.to_datetime(fix_thai_encoding(str(raw))).strftime('%d/%m/%Y')
                except: report_date_str = str(raw)
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

# --- UI HEADER (Sticky) ---
st.markdown('<div class="sticky-top-container">', unsafe_allow_html=True)

# Layout: แบ่งเป็น 3 ส่วน (Logo | Title | Search)
# ปรับสัดส่วนเป็น Logo(0.15) | Title(0.5) | Search(0.35)
c_logo, c_title, c_search = st.columns([0.15, 0.5, 0.35])

with c_logo:
    # แสดง Logo (ต้องมีไฟล์ชื่อนี้ในโฟลเดอร์)
    logo_path = "PMH Rxstock LineOA.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=100) 
    else:
        st.write("🏥") # Fallback ถ้าหาไฟล์รูปไม่เจอ

with c_title:
    st.markdown(f'''
        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
            <div class="app-title">ระบบสืบค้นคลังยา</div>
            <div>
                <span style="background-color:#059669; color:white; padding:4px 12px; border-radius:15px; font-weight:bold; font-size: 0.9rem;">
                    📅 ข้อมูลวันที่: {report_date_str}
                </span>
            </div>
        </div>
    ''', unsafe_allow_html=True)

with c_search:
    st.markdown('<div class="search-label">🔍 ค้นหารายการยา</div>', unsafe_allow_html=True)
    # Input ตรงนี้ก็จะเห็นชัดเจนแล้ว
    search_query = st.text_input("Search", "", placeholder="พิมพ์ชื่อยา, รหัส หรือ Lot...", label_visibility="collapsed")

st.markdown('</div>', unsafe_allow_html=True)

# --- RESULT TABLE ---
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

        group_ids = (table['ชื่อรายการ'] != table['ชื่อรายการ'].shift()).cumsum()
        rows_alt = table.index[group_ids % 2 == 1]
        rows_norm = table.index[group_ids % 2 == 0]

        styler = table.style.format(precision=2)
        if 'EXP' in table.columns: 
            styler = styler.format({'EXP': lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "-"})
        if 'ทุน' in table.columns: 
            styler = styler.format({'ทุน': '{:,.2f}'})

        # Apply Colors (Fixed Light Mode Style)
        styler = styler.set_properties(subset=pd.IndexSlice[rows_alt, :], **{'background-color': fixed_colors['table_bg_alt']})
        styler = styler.set_properties(subset=pd.IndexSlice[rows_norm, :], **{'background-color': fixed_colors['table_bg_norm']})
        styler = styler.set_properties(**{'color': fixed_colors['table_text']})

        st.dataframe(styler, use_container_width=True, hide_index=True, height=600)
    else:
        st.warning(f"ไม่พบข้อมูล '{search_query}'")
else:
    st.info("👋 ยินดีต้อนรับ กรุณาให้เจ้าหน้าที่ Login เพื่ออัปโหลดข้อมูลครั้งแรก")
