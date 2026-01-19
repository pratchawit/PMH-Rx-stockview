import streamlit as st
import pandas as pd
from github import Github
import io

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Inventory System", page_icon="🏥", layout="wide")

# --- CSS: Sticky Header และจัดหน้าตา ---
st.markdown(
    """
    <style>
    header {visibility: hidden;} /* ซ่อน Header ของ Streamlit */
    
    .sticky-top-container {
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: white;
        padding-top: 10px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e5e7eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .report-date {
        color: #047857; /* สีเขียวเข้ม */
        font-weight: bold;
        font-size: 1.1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Config ---
TARGET_FILE_NAME = "InvLotFrmByLot.xlsx" 

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
            
        return df
    except Exception as e:
        return None

# ==========================================
# ส่วนเมนู Admin (Sidebar)
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
            st.warning("💡 ควร Save As เป็น .xlsx ก่อนอัปโหลดเพื่อแก้ปัญหาภาษาต่างดาว")
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
    elif password:
        st.sidebar.error("รหัสผิด")

# ==========================================
# ส่วนประมวลผลข้อมูล (Data Preparation)
# ==========================================
# โหลดข้อมูลไว้ก่อนแสดงผล
with st.spinner('กำลังดึงข้อมูล...'):
    df = load_data_from_github()

# เตรียมตัวแปรวันที่สำหรับแสดงผล
report_date_str = "ไม่พบข้อมูล"

if df is not None:
    # Clean Column Names
    df.columns = df.columns.astype(str).str.strip()
    
    # --- ดึงวันที่จาก d1 มาเก็บไว้แสดงหัวเว็บ ---
    if 'd1' in df.columns and not df.empty:
        try:
            raw_date = df['d1'].iloc[0] # เอาแถวแรกมาดู
            # ถ้าเป็น DateTime Object
            if isinstance(raw_date, pd.Timestamp):
                report_date_str = raw_date.strftime('%d/%m/%Y')
            else:
                # ถ้าเป็น String ลองแปลงดู
                try:
                    dt_obj = pd.to_datetime(raw_date)
                    report_date_str = dt_obj.strftime('%d/%m/%Y')
                except:
                    # ถ้าแปลงไม่ได้จริงๆ ก็โชว์ดิบๆ
                    report_date_str = str(raw_date)
        except:
            pass
            
    # --- Clean Data สำหรับตาราง ---
    
    # TradeName
    trade_col = next((c for c in df.columns if c.lower().replace(" ", "") == "tradename"), None)
    if trade_col: df['TradeName'] = df[trade_col].fillna("-")
    else: df['TradeName'] = "-"

    # Lot & Price
    df['LotNo'] = df.get('LotNo', pd.Series(['-']*len(df))).fillna("-")
    df['price'] = df.get('price', pd.Series([0]*len(df))).fillna(0)
    
    # DisplayName
    name_col = df['NAME1'].astype(str) if 'NAME1' in df.columns else ""
    content_col = df['CONTENT'].fillna("").astype(str) if 'CONTENT' in df.columns else ""
    type_col = df['TYPE'].fillna("").astype(str) if 'TYPE' in df.columns else ""
    df['DisplayName'] = name_col + " " + content_col + " " + type_col
    
    # Qty
    amt_col = df['Amount1'].astype(str) if 'Amount1' in df.columns else "0"
    unit_col = df['minofLotPack'].astype(str) if 'minofLotPack' in df.columns else ""
    df['QtyDisplay'] = amt_col + " x " + unit_col

# ==========================================
# ส่วนแสดงผล (UI)
# ==========================================

# 1. Sticky Header Container
with st.container():
    st.markdown('<div class="sticky-top-container">', unsafe_allow_html=True)
    
    c1, c2 = st.columns([0.6, 0.4])
    with c1:
        st.title("🏥 ระบบสืบค้นคลังยา")
        # แสดงวันที่ตรงนี้ (ใต้ชื่อระบบ หรือข้างๆ)
        if df is not None:
            st.markdown(f'<span class="report-date">📅 ข้อมูลคงคลัง ณ วันที่: {report_date_str}</span>', unsafe_allow_html=True)
    
    with c2:
        # ช่องค้นหา (ขยับลงมานิดนึงให้สวย)
        st.write("") 
        search_query = st.text_input("🔍 ค้นหาด่วน", "", placeholder="ชื่อยา, รหัส, Lot...", label_visibility="collapsed")
    
    st.markdown('</div>', unsafe_allow_html=True)

# 2. Table Result
if df is not None:
    # --- Filter ---
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
        # เลือก Column (ตัด d1 ออก)
        cols_map = {
            'DisplayName': 'ชื่อรายการ', 
            'CODE1': 'รหัส', 
            'TradeName': 'Tradename',
            'QtyDisplay': 'คงเหลือ', 
            'price': 'ทุน', 
            'LotNo': 'Lot',
            'ExpDate': 'EXP'
        }
        
        # เลือกเฉพาะที่มีจริงใน df
        valid_cols = [c for c in cols_map.keys() if c in display_df.columns]
        
        table_data = display_df[valid_cols].copy()
        table_data.rename(columns=cols_map, inplace=True)
        
        # จัดลำดับคอลัมน์ให้สวยงาม
        desired_order = ['ชื่อรายการ', 'รหัส', 'Tradename', 'คงเหลือ', 'ทุน', 'Lot', 'EXP']
        # กรองเอาเฉพาะที่มีอยู่จริง (กัน Error)
        final_cols = [c for c in desired_order if c in table_data.columns]
        table_data = table_data[final_cols]

        # Format วันหมดอายุ
        if 'EXP' in table_data.columns:
            table_data['EXP'] = pd.to_datetime(table_data['EXP'], errors='coerce').dt.strftime('%d/%m/%Y').fillna("-")
            
        # Format ราคา
        if 'ทุน' in table_data.columns:
            table_data['ทุน'] = table_data['ทุน'].apply(lambda x: f"{float(x):,.2f}" if isinstance(x, (int, float)) else x)

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
            height=700
        )
    else:
        st.warning(f"ไม่พบข้อมูล '{search_query}'")
        
else:
    st.info("👋 กรุณาล็อกอินและอัปโหลดไฟล์ข้อมูล")
