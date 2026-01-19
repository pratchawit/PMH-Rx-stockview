import streamlit as st
import pandas as pd
from github import Github
import io

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Inventory System", page_icon="🏥", layout="wide")

# --- CSS: Sticky Header & Styling ---
st.markdown(
    """
    <style>
    header {visibility: hidden;}
    
    .sticky-top-container {
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: white;
        padding: 15px 0;
        border-bottom: 3px solid #047857;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .date-badge {
        background-color: #d1fae5;
        color: #065f46;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1rem;
        border: 1px solid #34d399;
        display: inline-block;
    }

    .app-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f2937;
        margin-bottom: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Config ---
TARGET_FILE_NAME = "InvLotFrmByLot.xlsx" 

# --- ฟังก์ชันแก้ภาษาต่างดาว ---
def fix_thai_encoding(text):
    if not isinstance(text, str):
        return text
    try:
        return text.encode('cp1252').decode('cp874')
    except:
        return text

# --- ฟังก์ชันเชื่อมต่อ GitHub ---
def upload_to_github(file_content):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        try:
            contents = repo.get_contents(TARGET_FILE_NAME)
            repo.update_file(contents.path, "Update data", file_content, contents.sha)
            return True, "อัปเดตไฟล์เดิมสำเร็จ!"
        except:
            repo.create_file(TARGET_FILE_NAME, "Initial upload", file_content)
            return True, "สร้างไฟล์ใหม่สำเร็จ!"
    except Exception as e:
        return False, f"GitHub Error: {str(e)}"

# --- ฟังก์ชันโหลดข้อมูล ---
@st.cache_data(ttl=0)
def load_data_from_github():
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        contents = repo.get_contents(TARGET_FILE_NAME)
        file_content = contents.decoded_content
        
        try:
            df = pd.read_excel(io.BytesIO(file_content))
        except:
            df = pd.read_excel(io.BytesIO(file_content), engine='xlrd')
        
        # แก้ภาษาต่างดาว
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(fix_thai_encoding)
        df.columns = [fix_thai_encoding(c) for c in df.columns]
            
        return df
    except Exception as e:
        return None

# ==========================================
# Sidebar (Admin)
# ==========================================
st.sidebar.title("🔧 เมนูเจ้าหน้าที่")

if st.sidebar.checkbox("เข้าสู่ระบบ (Admin)"):
    password = st.sidebar.text_input("รหัสผ่าน", type="password")
    if password == "rb,kp@10884":
        st.sidebar.success("✅ Login สำเร็จ")
        st.sidebar.markdown("---")
        st.sidebar.write("📤 **อัปเดตฐานข้อมูล**")
        
        uploaded_file = st.sidebar.file_uploader("เลือกไฟล์ Excel", type=['xlsx', 'xls'])
        
        if uploaded_file:
            if st.sidebar.button("🚀 อัปโหลดเข้า Server"):
                with st.sidebar.status("กำลังทำงาน...", expanded=True) as status:
                    bytes_data = uploaded_file.getvalue()
                    success, msg = upload_to_github(bytes_data)
                    if success:
                        status.update(label="✅ เสร็จสมบูรณ์", state="complete")
                        st.sidebar.success(msg)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        status.update(label="❌ ล้มเหลว", state="error")
                        st.sidebar.error(msg)

# ==========================================
# Main Logic
# ==========================================
with st.spinner('กำลังดึงข้อมูล...'):
    df = load_data_from_github()

report_date_str = "รอการอัปเดต"

if df is not None:
    # Clean & Prepare
    df.columns = df.columns.astype(str).str.strip()
    
    # 1. Date
    if 'd1' in df.columns and not df.empty:
        try:
            raw_date = df['d1'].iloc[0]
            if pd.notnull(raw_date):
                if isinstance(raw_date, pd.Timestamp):
                    report_date_str = raw_date.strftime('%d/%m/%Y')
                else:
                    date_text = fix_thai_encoding(str(raw_date))
                    try:
                        dt = pd.to_datetime(date_text)
                        report_date_str = dt.strftime('%d/%m/%Y')
                    except:
                        report_date_str = date_text
        except:
            pass

    # 2. Prepare Columns
    trade_col = next((c for c in df.columns if c.lower().replace(" ", "") == "tradename"), None)
    if trade_col: df['TradeName'] = df[trade_col].fillna("-")
    else: df['TradeName'] = "-"

    df['LotNo'] = df.get('LotNo', pd.Series(['-']*len(df))).fillna("-")
    df['price'] = df.get('price', pd.Series([0]*len(df))).fillna(0)
    
    name_col = df['NAME1'].astype(str) if 'NAME1' in df.columns else ""
    content_col = df['CONTENT'].fillna("").astype(str) if 'CONTENT' in df.columns else ""
    type_col = df['TYPE'].fillna("").astype(str) if 'TYPE' in df.columns else ""
    df['DisplayName'] = name_col + " " + content_col + " " + type_col
    
    amt_col = df['Amount1'].astype(str) if 'Amount1' in df.columns else "0"
    unit_col = df['minofLotPack'].astype(str) if 'minofLotPack' in df.columns else ""
    df['QtyDisplay'] = amt_col + " x " + unit_col

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
        search_query = st.text_input("🔍 ค้นหาด่วน", "", placeholder="ชื่อยา, รหัส, Lot...", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

if df is not None:
    # Filter
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
        # Prepare Table Data
        cols_map = {
            'DisplayName': 'ชื่อรายการ', 'CODE1': 'รหัส', 'TradeName': 'Tradename',
            'QtyDisplay': 'คงเหลือ', 'price': 'ทุน', 'LotNo': 'Lot', 'ExpDate': 'EXP'
        }
        
        valid_cols = [c for c in cols_map.keys() if c in display_df.columns]
        table_data = display_df[valid_cols].copy()
        table_data.rename(columns=cols_map, inplace=True)
        
        desired_order = ['ชื่อรายการ', 'รหัส', 'Tradename', 'คงเหลือ', 'ทุน', 'Lot', 'EXP']
        final_cols = [c for c in desired_order if c in table_data.columns]
        table_data = table_data[final_cols]
        
        # Reset Index (สำคัญมากสำหรับการทำสี)
        table_data = table_data.reset_index(drop=True)

        # --- Logic การลงสี (Group Banding) ---
        # 1. สร้าง ID ให้แต่ละกลุ่มยา (ถ้าชื่อยาเปลี่ยน = ขึ้นกลุ่มใหม่)
        group_ids = (table_data['ชื่อรายการ'] != table_data['ชื่อรายการ'].shift()).cumsum()
        
        # 2. หาว่ากลุ่มไหนเป็นเลขคี่ (เพื่อระบายสี)
        rows_to_color = table_data.index[group_ids % 2 == 1]

        # 3. สร้าง Pandas Styler
        styler = table_data.style.format(precision=2)
        
        # Format วันที่และราคา
        if 'EXP' in table_data.columns:
            styler = styler.format({'EXP': lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "-"})
        if 'ทุน' in table_data.columns:
            styler = styler.format({'ทุน': '{:,.2f}'})

        # Apply Background Color (สีฟ้าอ่อนๆ สบายตา)
        # ใช้ subset เพื่อประสิทธิภาพที่ดีกว่า apply map ทีละช่อง
        styler = styler.set_properties(
            subset=pd.IndexSlice[rows_to_color, :], 
            **{'background-color': '#f0f9ff', 'color': 'black'}
        )

        # แสดงผล
        st.dataframe(
            styler,
            use_container_width=True,
            hide_index=True,
            height=650
        )
    else:
        st.warning(f"ไม่พบข้อมูล '{search_query}'")
else:
    st.info("👋 กรุณา Login เพื่ออัปโหลดข้อมูล")
