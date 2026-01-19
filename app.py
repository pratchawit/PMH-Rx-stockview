import streamlit as st
import pandas as pd
from github import Github
import io

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Inventory System", page_icon="🏥", layout="wide")

# ==========================================
# 1. จัดการ THEME (Light / Dark)
# ==========================================
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    if st.session_state.theme == 'light':
        st.session_state.theme = 'dark'
    else:
        st.session_state.theme = 'light'

if st.session_state.theme == 'dark':
    theme_colors = {
        'bg_main': '#0e1117',
        'bg_sticky': '#1f2937',
        'text_main': '#e5e7eb',
        'table_bg_1': '#1f2937',
        'table_bg_2': '#374151',
        'border': '#374151',
        'date_badge_bg': '#064e3b',
        'date_badge_txt': '#ecfdf5'
    }
else:
    theme_colors = {
        'bg_main': '#ffffff',
        'bg_sticky': '#ffffff',
        'text_main': '#1f2937',
        'table_bg_1': '#ffffff',
        'table_bg_2': '#f3f4f6',
        'border': '#e5e7eb',
        'date_badge_bg': '#d1fae5',
        'date_badge_txt': '#065f46'
    }

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {theme_colors['bg_main']};
        color: {theme_colors['text_main']};
    }}
    header {{visibility: hidden;}}
    .sticky-top-container {{
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: {theme_colors['bg_sticky']};
        padding: 15px 0;
        border-bottom: 2px solid {theme_colors['border']};
        transition: background-color 0.3s;
    }}
    .date-badge {{
        background-color: {theme_colors['date_badge_bg']};
        color: {theme_colors['date_badge_txt']};
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1rem;
        border: 1px solid {theme_colors['border']};
        display: inline-block;
    }}
    .app-title {{
        font-size: 1.8rem;
        font-weight: bold;
        color: {theme_colors['text_main']};
        margin-bottom: 5px;
    }}
    div[data-baseweb="input"] {{
        background-color: {theme_colors['bg_main']} !important;
        border-color: {theme_colors['border']} !important; 
    }}
    input {{
        color: {theme_colors['text_main']} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Config ---
TARGET_FILE_NAME = "InvLotFrmByLot.xlsx" 

# --- Helper Functions ---
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
# Sidebar
# ==========================================
st.sidebar.title("⚙️ ตั้งค่า")
st.sidebar.write("🎨 **รูปแบบการแสดงผล**")
is_dark = st.session_state.theme == 'dark'
if st.sidebar.toggle("🌙 Dark Mode", value=is_dark):
    st.session_state.theme = 'dark'
else:
    st.session_state.theme = 'light'

st.sidebar.markdown("---")
st.sidebar.title("🔧 เจ้าหน้าที่")
if st.sidebar.checkbox("เข้าสู่ระบบ (Admin)"):
    password = st.sidebar.text_input("รหัสผ่าน", type="password")
    if password == "rb,kp@10884":
        st.sidebar.success("✅ Login สำเร็จ")
        st.sidebar.write("📤 **อัปเดตฐานข้อมูล**")
        uploaded_file = st.sidebar.file_uploader("เลือกไฟล์ Excel", type=['xlsx', 'xls'])
        if uploaded_file:
            if st.sidebar.button("🚀 อัปโหลด"):
                with st.sidebar.status("กำลังทำงาน...", expanded=True) as status:
                    success, msg = upload_to_github(uploaded_file.getvalue())
                    if success:
                        status.update(label="✅ เสร็จสิ้น", state="complete")
                        st.sidebar.success(msg)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.sidebar.error(msg)

# ==========================================
# Main Process
# ==========================================
with st.spinner('Loading...'):
    df = load_data_from_github()

report_date_str = "-"

if df is not None:
    df.columns = df.columns.astype(str).str.strip()
    
    # 1. Date
    if 'd1' in df.columns and not df.empty:
        try:
            raw = df['d1'].iloc[0]
            if isinstance(raw, pd.Timestamp): report_date_str = raw.strftime('%d/%m/%Y')
            else: 
                try: report_date_str = pd.to_datetime(fix_thai_encoding(str(raw))).strftime('%d/%m/%Y')
                except: report_date_str = str(raw)
        except: pass

    # 2. Prepare Data (แก้ Error ตรงนี้ครับ)
    trade_col = next((c for c in df.columns if c.lower().replace(" ", "") == "tradename"), None)
    df['TradeName'] = df[trade_col].fillna("-") if trade_col else "-"
    df['LotNo'] = df.get('LotNo', pd.Series(['-']*len(df))).fillna("-")
    df['price'] = df.get('price', pd.Series([0]*len(df))).fillna(0)
    
    # --- ส่วนที่แก้ไข: รวมชื่อด้วยวิธีดั้งเดิมที่ปลอดภัยกว่า ---
    # สร้างคอลัมน์ว่างก่อน
    df['DisplayName'] = ""
    
    # ค่อยๆ ต่อ string ทีละคอลัมน์
    if 'NAME1' in df.columns:
        df['DisplayName'] += df['NAME1'].fillna("").astype(str) + " "
    if 'CONTENT' in df.columns:
        df['DisplayName'] += df['CONTENT'].fillna("").astype(str) + " "
    if 'TYPE' in df.columns:
        df['DisplayName'] += df['TYPE'].fillna("").astype(str)
        
    df['DisplayName'] = df['DisplayName'].str.strip() # ตัดช่องว่างหัวท้ายทิ้ง
    # ----------------------------------------------------

    amt = df['Amount1'].astype(str) if 'Amount1' in df.columns else "0"
    unit = df['minofLotPack'].astype(str) if 'minofLotPack' in df.columns else ""
    df['QtyDisplay'] = amt + " x " + unit

# ==========================================
# UI Display
# ==========================================
with st.container():
    st.markdown('<div class="sticky-top-container">', unsafe_allow_html=True)
    c1, c2 = st.columns([0.65, 0.35])
    with c1:
        st.markdown('<div class="app-title">🏥 ระบบสืบค้นคลังยา</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="date-badge">📅 ข้อมูลวันที่: {report_date_str}</span>', unsafe_allow_html=True)
    with c2:
        st.write("")
        search_query = st.text_input("🔍 ค้นหา", "", placeholder="ชื่อยา, รหัส, Lot...", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

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

        # Styling
        group_ids = (table['ชื่อรายการ'] != table['ชื่อรายการ'].shift()).cumsum()
        rows_to_color = table.index[group_ids % 2 == 1]
        
        styler = table.style.format(precision=2)
        if 'EXP' in table.columns: styler = styler.format({'EXP': lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "-"})
        if 'ทุน' in table.columns: styler = styler.format({'ทุน': '{:,.2f}'})

        styler = styler.set_properties(subset=pd.IndexSlice[rows_to_color, :], **{'background-color': theme_colors['table_bg_2']})
        rows_normal = table.index[group_ids % 2 == 0]
        styler = styler.set_properties(subset=pd.IndexSlice[rows_normal, :], **{'background-color': theme_colors['table_bg_1']})
        styler = styler.set_properties(**{'color': theme_colors['text_main']})

        st.dataframe(styler, use_container_width=True, hide_index=True, height=650)
    else:
        st.warning(f"ไม่พบข้อมูล '{search_query}'")
else:
    st.info("กรุณา Login เพื่ออัปโหลดข้อมูล")
