import streamlit as st
import pandas as pd
from github import Github
import io

# --- ตั้งค่าหน้าเว็บ (ต้องอยู่บรรทัดแรกสุดของการรัน) ---
st.set_page_config(page_title="Inventory System", page_icon="🏥", layout="wide")

# ==========================================
# 1. ระบบ THEME & COLORS
# ==========================================
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# กำหนด Palette สี (ปรับให้สบายตาขึ้น ไม่ขาวจั๊วะ)
if st.session_state.theme == 'dark':
    theme_colors = {
        'bg_main': '#0f1116',        # พื้นหลังหลัก (Dark grey)
        'bg_sidebar': '#161b22',     # พื้นหลัง Sidebar
        'text_main': '#e6edf3',      # สีตัวหนังสือ
        'card_bg': '#21262d',        # พื้นหลังการ์ด/Input
        'header_bg': '#161b22',      # Sticky Header
        'table_bg_norm': '#0d1117',  # พื้นตารางปกติ
        'table_bg_alt': '#1f2428',   # พื้นตารางสลับสี
        'accent': '#238636'          # สีเขียวเน้น
    }
else:
    # Light Mode (Eye Comfort)
    theme_colors = {
        'bg_main': '#f8fafc',        # เทาอมฟ้าจางๆ (ไม่ขาวโอโม่)
        'bg_sidebar': '#f1f5f9',     # เทาอ่อน Sidebar
        'text_main': '#334155',      # เทาเข้ม (อ่านง่ายกว่าดำสนิท)
        'card_bg': '#ffffff',        # กล่องข้อความสีขาว
        'header_bg': '#ffffff',      # Header สีขาว
        'table_bg_norm': '#ffffff',  # พื้นตารางปกติ
        'table_bg_alt': '#e2e8f0',   # พื้นตารางสลับสี (เทาฟ้าอ่อนๆ)
        'accent': '#059669'          # สีเขียวมรกต
    }

# --- CSS Injection (บังคับสี) ---
st.markdown(
    f"""
    <style>
    /* Main Background */
    .stApp {{
        background-color: {theme_colors['bg_main']};
        color: {theme_colors['text_main']};
    }}
    
    /* Sidebar Background */
    section[data-testid="stSidebar"] {{
        background-color: {theme_colors['bg_sidebar']};
    }}
    
    /* Sticky Header */
    header {{visibility: hidden;}}
    .sticky-top-container {{
        position: sticky;
        top: 0;
        z-index: 999;
        background-color: {theme_colors['header_bg']};
        padding: 15px 20px;
        border-bottom: 2px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-left: -1rem;
        margin-right: -1rem;
    }}
    
    /* Input Fields */
    .stTextInput input {{
        background-color: {theme_colors['card_bg']} !important;
        color: {theme_colors['text_main']} !important;
        border: 1px solid #cbd5e1;
    }}
    
    /* Date Badge */
    .date-badge {{
        background-color: {theme_colors['accent']};
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: 500;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }}
    
    /* App Title */
    .app-title {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {theme_colors['text_main']};
        margin-bottom: 5px;
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
# SIDEBAR (เมนูควบคุม)
# ==========================================
with st.sidebar:
    st.header("⚙️ ตั้งค่าการแสดงผล")
    
    # Toggle Theme
    is_dark = st.session_state.theme == 'dark'
    if st.toggle("🌙 โหมดกลางคืน (Dark Mode)", value=is_dark):
        st.session_state.theme = 'dark'
    else:
        st.session_state.theme = 'light'
        
    st.markdown("---")
    
    st.header("🔐 สำหรับเจ้าหน้าที่")
    
    # Login Logic
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        password = st.text_input("รหัสผ่าน Admin", type="password")
        if password == "rb,kp@10884":
            st.session_state.logged_in = True
            st.success("เข้าสู่ระบบแล้ว")
            st.rerun()
    else:
        st.success("✅ สถานะ: Admin")
        if st.button("ออกจากระบบ"):
            st.session_state.logged_in = False
            st.rerun()
            
        st.markdown("### 📤 อัปเดตข้อมูล")
        uploaded_file = st.file_uploader("เลือกไฟล์ Excel", type=['xlsx', 'xls'])
        
        if uploaded_file:
            if st.button("🚀 อัปโหลดขึ้น Server"):
                with st.status("กำลังทำงาน...", expanded=True) as status:
                    success, msg = upload_to_github(uploaded_file.getvalue())
                    if success:
                        status.update(label="✅ เรียบร้อย", state="complete")
                        st.success(msg)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        status.update(label="❌ ผิดพลาด", state="error")
                        st.error(msg)

# ==========================================
# MAIN CONTENT
# ==========================================
with st.spinner('กำลังโหลดข้อมูล...'):
    df = load_data_from_github()

report_date_str = "-"

if df is not None:
    df.columns = df.columns.astype(str).str.strip()
    
    # 1. Date Extraction
    if 'd1' in df.columns and not df.empty:
        try:
            raw = df['d1'].iloc[0]
            if isinstance(raw, pd.Timestamp): report_date_str = raw.strftime('%d/%m/%Y')
            else: 
                try: report_date_str = pd.to_datetime(fix_thai_encoding(str(raw))).strftime('%d/%m/%Y')
                except: report_date_str = str(raw)
        except: pass

    # 2. Data Prep (Safe Method)
    trade_col = next((c for c in df.columns if c.lower().replace(" ", "") == "tradename"), None)
    df['TradeName'] = df[trade_col].fillna("-") if trade_col else "-"
    df['LotNo'] = df.get('LotNo', pd.Series(['-']*len(df))).fillna("-")
    df['price'] = df.get('price', pd.Series([0]*len(df))).fillna(0)
    
    # รวมชื่อสินค้า (Safe String Concat)
    df['DisplayName'] = ""
    if 'NAME1' in df.columns: df['DisplayName'] += df['NAME1'].fillna("").astype(str) + " "
    if 'CONTENT' in df.columns: df['DisplayName'] += df['CONTENT'].fillna("").astype(str) + " "
    if 'TYPE' in df.columns: df['DisplayName'] += df['TYPE'].fillna("").astype(str)
    df['DisplayName'] = df['DisplayName'].str.strip()

    amt = df['Amount1'].astype(str) if 'Amount1' in df.columns else "0"
    unit = df['minofLotPack'].astype(str) if 'minofLotPack' in df.columns else ""
    df['QtyDisplay'] = amt + " x " + unit

# --- UI Header ---
st.markdown('<div class="sticky-top-container">', unsafe_allow_html=True)
c1, c2 = st.columns([0.65, 0.35])
with c1:
    st.markdown(f'''
        <div class="app-title">🏥 ระบบสืบค้นคลังยา</div>
        <span class="date-badge">📅 ข้อมูลวันที่: {report_date_str}</span>
    ''', unsafe_allow_html=True)
with c2:
    st.write("")
    search_query = st.text_input("🔍 ค้นหา", "", placeholder="พิมพ์ชื่อยา, รหัส, หรือ Lot...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# --- Result Table ---
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
        # Select & Rename Columns
        cols_map = {'DisplayName': 'ชื่อรายการ', 'CODE1': 'รหัส', 'TradeName': 'Tradename', 'QtyDisplay': 'คงเหลือ', 'price': 'ทุน', 'LotNo': 'Lot', 'ExpDate': 'EXP'}
        valid_cols = [c for c in cols_map.keys() if c in display_df.columns]
        table = display_df[valid_cols].copy().rename(columns=cols_map)
        
        desired_order = ['ชื่อรายการ', 'รหัส', 'Tradename', 'คงเหลือ', 'ทุน', 'Lot', 'EXP']
        final_cols = [c for c in desired_order if c in table.columns]
        table = table[final_cols].reset_index(drop=True)

        # Apply Styling
        group_ids = (table['ชื่อรายการ'] != table['ชื่อรายการ'].shift()).cumsum()
        rows_alt = table.index[group_ids % 2 == 1] # แถวที่ต้องเปลี่ยนสี
        rows_norm = table.index[group_ids % 2 == 0]

        styler = table.style.format(precision=2)
        if 'EXP' in table.columns: 
            styler = styler.format({'EXP': lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "-"})
        if 'ทุน' in table.columns: 
            styler = styler.format({'ทุน': '{:,.2f}'})

        # Apply Colors from Theme Logic
        styler = styler.set_properties(subset=pd.IndexSlice[rows_alt, :], **{'background-color': theme_colors['table_bg_alt']})
        styler = styler.set_properties(subset=pd.IndexSlice[rows_norm, :], **{'background-color': theme_colors['table_bg_norm']})
        styler = styler.set_properties(**{'color': theme_colors['text_main']})

        st.dataframe(styler, use_container_width=True, hide_index=True, height=600)
    else:
        st.warning(f"ไม่พบข้อมูล '{search_query}'")
else:
    st.info("👋 ยินดีต้อนรับ กรุณาให้เจ้าหน้าที่ Login เพื่ออัปโหลดข้อมูลครั้งแรก")
