import streamlit as st
import pandas as pd
from github import Github # พระเอกของเรา ตัวเชื่อม GitHub
import io

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Inventory System", page_icon="🏥", layout="wide")

# --- Config ---
# ชื่อไฟล์ที่จะบันทึกลง GitHub (ระบบจะบังคับให้เป็นชื่อนี้เสมอ เพื่อความง่าย)
TARGET_FILE_NAME = "InvLotFrmByLot.xlsx" 

# --- ฟังก์ชันเชื่อมต่อ GitHub ---
def upload_to_github(file_content):
    try:
        # ดึงกุญแจจาก Secrets
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]
        
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        # ลองหาไฟล์เดิมก่อน
        try:
            contents = repo.get_contents(TARGET_FILE_NAME)
            # ถ้ามีไฟล์เดิม -> ทำการ Update
            repo.update_file(contents.path, "Update data from Streamlit App", file_content, contents.sha)
            return True, "อัปเดตไฟล์เดิมสำเร็จ!"
        except:
            # ถ้าไม่มีไฟล์เดิม -> สร้างไฟล์ใหม่
            repo.create_file(TARGET_FILE_NAME, "Initial upload", file_content)
            return True, "สร้างไฟล์ใหม่สำเร็จ!"
            
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการเชื่อมต่อ GitHub: {str(e)}"

# --- ฟังก์ชันโหลดข้อมูล (อ่านจาก GitHub โดยตรง) ---
@st.cache_data(ttl=0) # ttl=0 คือไม่จำค่า (ให้โหลดใหม่ทุกครั้งที่มีการอัปเดต)
def load_data_from_github():
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]
        
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        # อ่านไฟล์
        contents = repo.get_contents(TARGET_FILE_NAME)
        file_content = contents.decoded_content
        
        # แปลงเป็น DataFrame
        df = pd.read_excel(io.BytesIO(file_content))
        return df
        
    except Exception as e:
        return None

# ==========================================
# ส่วนเมนู Admin (Sidebar)
# ==========================================
st.sidebar.title("🔧 เมนูเจ้าหน้าที่คลัง")
st.sidebar.info("เข้าสู่ระบบเพื่ออัปเดตข้อมูล")

if st.sidebar.checkbox("Login (Admin Only)"):
    password = st.sidebar.text_input("รหัสผ่าน Admin", type="password")
    if password == "rb,kp@10884":
        st.sidebar.success("✅ Login สำเร็จ")
        st.sidebar.markdown("---")
        st.sidebar.write("📤 **อัปเดตฐานข้อมูล**")
        
        # Upload File
        uploaded_file = st.sidebar.file_uploader("เลือกไฟล์ Excel ล่าสุด", type=['xlsx', 'xls'])
        
        if uploaded_file:
            if st.sidebar.button("🚀 ยืนยันการอัปโหลดเข้า Server"):
                with st.sidebar.status("กำลังเชื่อมต่อ GitHub...", expanded=True) as status:
                    # อ่านไฟล์เป็น Bytes
                    bytes_data = uploaded_file.getvalue()
                    
                    # ส่งขึ้น GitHub
                    status.write("กำลังส่งข้อมูล...")
                    success, msg = upload_to_github(bytes_data)
                    
                    if success:
                        status.update(label="✅ เสร็จสมบูรณ์!", state="complete", expanded=False)
                        st.sidebar.success(msg)
                        st.cache_data.clear() # ล้างความจำเก่า
                        st.rerun() # รีเฟรชหน้าจอ
                    else:
                        status.update(label="❌ ล้มเหลว", state="error", expanded=False)
                        st.sidebar.error(msg)
    elif password:
        st.sidebar.error("รหัสผ่านไม่ถูกต้อง")

# ==========================================
# ส่วนแสดงผล (User ทั่วไป)
# ==========================================
st.title("🏥 ระบบสืบค้นคลังยา (Smart Search)")

# โหลดข้อมูล
with st.spinner('กำลังดึงข้อมูลล่าสุด...'):
    df = load_data_from_github()

if df is not None:
    # Clean & Prepare Data (Logic เดิม)
    df.columns = df.columns.astype(str).str.strip()
    
    # 1. TradeName
    trade_col = next((c for c in df.columns if c.lower().replace(" ", "") == "tradename"), None)
    if trade_col: df['TradeName'] = df[trade_col].fillna("-")
    else: df['TradeName'] = "-"

    # 2. Others
    df['LotNo'] = df.get('LotNo', pd.Series(['-']*len(df))).fillna("-")
    df['price'] = df.get('price', pd.Series([0]*len(df))).fillna(0)
    
    if 'ExpDate' in df.columns:
        df['ExpDate'] = pd.to_datetime(df['ExpDate'], errors='coerce')
    else:
        df['ExpDate'] = pd.NaT

    type_col = df['TYPE'].fillna("").astype(str) if 'TYPE' in df.columns else ""
    content_col = df['CONTENT'].fillna("").astype(str) if 'CONTENT' in df.columns else ""
    name_col = df['NAME1'].astype(str) if 'NAME1' in df.columns else ""
    
    df['DisplayName'] = name_col + " " + content_col + " " + type_col
    
    amt_col = df['Amount1'].astype(str) if 'Amount1' in df.columns else "0"
    unit_col = df['minofLotPack'].astype(str) if 'minofLotPack' in df.columns else ""
    df['QtyDisplay'] = amt_col + " x " + unit_col

    # --- UI แสดงผล ---
    st.markdown(f"""
    <div style='padding: 10px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 5px; color: #166534; margin-bottom: 15px;'>
        <strong>สถานะระบบ:</strong> ออนไลน์ ✅ | มีรายการยา {len(df):,} รายการ
    </div>
    """, unsafe_allow_html=True)

    search_query = st.text_input("🔍 ค้นหา (พิมพ์ชื่อยา, รหัส, หรือชื่อการค้า)", "", placeholder="พิมพ์คำค้นหา...")

    if search_query:
        mask = (
            df['DisplayName'].str.contains(search_query, case=False, na=False) |
            df.get('CODE1', pd.Series(['']*len(df))).astype(str).str.contains(search_query, case=False, na=False) |
            df['TradeName'].str.contains(search_query, case=False, na=False)
        )
        display_df = df[mask]
    else:
        display_df = df

    if not display_df.empty:
        # เตรียมตาราง
        cols_to_show = ['DisplayName', 'CODE1', 'TradeName', 'QtyDisplay', 'price', 'LotNo', 'ExpDate']
        # เลือกเฉพาะคอลัมน์ที่มีจริง
        cols_to_show = [c for c in cols_to_show if c in df.columns] 
        
        table_data = display_df[cols_to_show].copy()
        
        # Rename Headers
        rename_map = {
            'DisplayName': 'ชื่อรายการ', 'CODE1': 'รหัสรายการ', 'TradeName': 'Tradename',
            'QtyDisplay': 'จำนวนคงเหลือ', 'price': 'ราคาทุน', 'LotNo': 'เลขที่ Lot', 'ExpDate': 'วันหมดอายุ'
        }
        table_data.rename(columns=rename_map, inplace=True)

        # Format
        if 'วันหมดอายุ' in table_data.columns:
            table_data['วันหมดอายุ'] = table_data['วันหมดอายุ'].dt.strftime('%d/%m/%Y').fillna("-")
        if 'ราคาทุน' in table_data.columns:
            table_data['ราคาทุน'] = table_data['ราคาทุน'].apply(lambda x: f"{x:,.2f}")

        st.dataframe(table_data, use_container_width=True, hide_index=True, height=600)
    else:
        st.warning("ไม่พบข้อมูล")

else:
    st.error("⚠️ ไม่พบฐานข้อมูล หรือการเชื่อมต่อ GitHub มีปัญหา")
    st.info("Admin: กรุณา Login ที่แถบด้านซ้าย เพื่ออัปโหลดไฟล์ครั้งแรก")
