import streamlit as st
import pandas as pd
from datetime import datetime

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Inventory Search System", 
    page_icon="🏥", 
    layout="wide"
)

# --- 1. Security Check (Login) ---
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == "admin1234":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔑 กรุณาระบุรหัสผ่าน", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔑 กรุณาระบุรหัสผ่าน", type="password", on_change=password_entered, key="password")
        st.error("😕 รหัสผ่านไม่ถูกต้อง")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- 2. Data Processing Logic ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip() # ลบช่องว่างหัวตาราง
        
        required_cols = ['d1', 'CODE1', 'Amount1', 'minofLotPack', 'price', 
                         'ExpDate', 'NAME1', 'TYPE', 'CONTENT', 'Tradename', 'LotNo']
        
        # ตรวจสอบคอลัมน์แบบยืดหยุ่น (Case Insensitive)
        df_cols_upper = [c.upper() for c in df.columns]
        req_cols_upper = [r.upper() for r in required_cols]
        
        missing_cols = [r for r in required_cols if r.upper() not in df_cols_upper]
        
        if missing_cols:
            return None, f"ไม่พบคอลัมน์: {missing_cols}"

        # --- Data Transformation ---
        df['ExpDate'] = pd.to_datetime(df['ExpDate'], errors='coerce')
        
        # Clean Data
        df['TYPE'] = df['TYPE'].fillna("ไม่ระบุ").astype(str).str.strip()
        df['NAME1'] = df['NAME1'].fillna("").astype(str).str.strip()
        df['CONTENT'] = df['CONTENT'].fillna("").astype(str).str.strip()
        
        # DisplayName = NAME CONTENT TYPE
        df['DisplayName'] = df['NAME1'] + " " + df['CONTENT'] + " " + df['TYPE']
        
        df['QtyDisplay'] = df['Amount1'].astype(str) + " x " + df['minofLotPack'].astype(str)
        df['Tradename'] = df['Tradename'].fillna("-")
        df['LotNo'] = df['LotNo'].fillna("-")

        # Get Last Update
        last_update = df['d1'].iloc[0] if not df.empty else "ไม่ระบุ"
        if isinstance(last_update, pd.Timestamp):
            last_update = last_update.strftime('%d/%m/%Y')
            
        return df, last_update

    except Exception as e:
        return None, str(e)

# --- 3. UI Section ---
st.title("🏥 ระบบสืบค้นคลังยา (Smart Search)")

uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์ Excel (.xlsx)", type=['xlsx', 'xls'])

if uploaded_file:
    df, status = load_data(uploaded_file)
    
    if df is not None:
        st.info(f"🕒 ข้อมูลอัปเดตล่าสุด: {status}")
        
        # Sidebar Filter
        st.sidebar.header("ตัวเลือกการกรอง")
        all_types = sorted(df['TYPE'].unique())
        selected_types = st.sidebar.multiselect("ประเภทเวชภัณฑ์ (TYPE)", options=all_types, default=all_types)
        
        # Logic
        filtered_df = df[df['TYPE'].isin(selected_types)]
        search_query = st.text_input("🔍 ค้นหา (พิมพ์ชื่อ, รหัส, หรือยี่ห้อ)", "", placeholder="พิมพ์คำค้นหา...")

        if search_query:
            mask = (
                filtered_df['DisplayName'].str.contains(search_query, case=False, na=False) |
                filtered_df['CODE1'].astype(str).str.contains(search_query, case=False, na=False) |
                filtered_df['Tradename'].str.contains(search_query, case=False, na=False)
            )
            final_result = filtered_df[mask]
        else:
            final_result = filtered_df

        st.write(f"**พบข้อมูลทั้งหมด: {len(final_result):,} รายการ**")
        
        tab1, tab2 = st.tabs(["📋 มุมมองแบบการ์ด", "📊 มุมมองตารางรวม"])
        
        with tab1:
            if len(final_result) > 200 and not search_query:
                st.warning(f"⚠️ ข้อมูลมีจำนวนมาก ({len(final_result):,}) แสดงผล 200 รายการแรกเพื่อความรวดเร็ว")
            
            for index, row in final_result.head(200).iterrows():
                is_expired = False
                exp_str = "-"
                if pd.notnull(row['ExpDate']):
                    exp_str = row['ExpDate'].strftime('%d/%m/%Y')
                    if row['ExpDate'] < pd.Timestamp.now():
                        is_expired = True

                with st.container():
                    c1, c2 = st.columns([0.7, 0.3])
                    with c1:
                        st.subheader(f"💊 {row['DisplayName']}")
                        st.text(f"CODE: {row['CODE1']} | Trade: {row['Tradename']}")
                    with c2:
                         if is_expired:
                             st.error(f"EXP: {exp_str}")
                         else:
                             st.success(f"EXP: {exp_str}")

                    c_a, c_b, c_c = st.columns(3)
                    c_a.metric("📦 คงเหลือ", row['QtyDisplay'])
                    c_b.metric("💰 ทุน", f"{row['price']:,.2f}")
                    c_c.metric("🏷️ Lot", str(row['LotNo']))
                    st.divider()

        with tab2:
            st.dataframe(final_result)
    else:
        st.error(f"Error: {status}")
else:
    st.info("👋 กรุณาอัปโหลดไฟล์ Excel เพื่อเริ่มใช้งาน")
