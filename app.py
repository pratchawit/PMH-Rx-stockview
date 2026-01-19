import streamlit as st
import pandas as pd

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Inventory System", page_icon="🏥", layout="wide")

# --- 1. ระบบตรวจสอบรหัสผ่าน (แก้ไขใหม่) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    def password_entered():
        # แก้ไขรหัสผ่านตามที่ระบุ
        if st.session_state["password"] == "rb,kp@10884":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.text_input("🔑 กรุณาระบุรหัสผ่าน", type="password", on_change=password_entered, key="password")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. ฟังก์ชันโหลดข้อมูล ---
@st.cache_data
def load_data(file):
    try:
        # อ่านไฟล์ Excel (รองรับทั้ง xls และ xlsx)
        df = pd.read_excel(file)
        
        # ลบช่องว่างหัวตาราง (เผื่อใน Excel มีเว้นวรรคหน้าหลังโดยไม่ตั้งใจ)
        df.columns = df.columns.astype(str).str.strip()

        # ตรวจสอบว่ามี Column สำคัญครบหรือไม่ (ระบุชื่อตรงๆ)
        required_cols = ['CODE1', 'NAME1', 'Amount1', 'minofLotPack', 'TradeName']
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            return None, f"ไม่พบคอลัมน์: {missing} (กรุณาตรวจสอบชื่อหัวตารางใน Excel)"

        # --- จัดการข้อมูล ---
        
        # สร้าง DisplayName (ชื่อ + ความแรง + รูปแบบ)
        # ตรวจสอบว่ามีคอลัมน์ TYPE กับ CONTENT ไหม ถ้าไม่มีให้ใส่ค่าว่าง
        df['TYPE'] = df['TYPE'].fillna("").astype(str) if 'TYPE' in df.columns else ""
        df['CONTENT'] = df['CONTENT'].fillna("").astype(str) if 'CONTENT' in df.columns else ""
        
        # สูตร: NAME1 + CONTENT + TYPE
        df['DisplayName'] = df['NAME1'].astype(str) + " " + df['CONTENT'] + " " + df['TYPE']
        
        # สร้าง QtyDisplay
        df['QtyDisplay'] = df['Amount1'].astype(str) + " x " + df['minofLotPack'].astype(str)
        
        # จัดการวันที่ (ExpDate)
        if 'ExpDate' in df.columns:
            df['ExpDate'] = pd.to_datetime(df['ExpDate'], errors='coerce')
        
        # จัดการราคา (Price)
        if 'price' not in df.columns:
            df['price'] = 0
            
        # จัดการ LotNo
        if 'LotNo' not in df.columns:
            df['LotNo'] = "-"
        else:
            df['LotNo'] = df['LotNo'].fillna("-")

        # จัดการ TradeName (เผื่อมีช่องว่าง)
        df['TradeName'] = df['TradeName'].fillna("-")

        return df, "OK"

    except Exception as e:
        return None, f"เกิดข้อผิดพลาด: {str(e)}"

# --- 3. ส่วนแสดงผล ---
st.title("🏥 ระบบสืบค้นคลังยา (Smart Search)")

uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์ Excel (.xls / .xlsx)", type=['xlsx', 'xls'])

if uploaded_file:
    df, status = load_data(uploaded_file)
    
    if df is not None:
        st.success(f"✅ โหลดข้อมูลสำเร็จ ({len(df)} รายการ)")
        
        # ช่องค้นหา
        search_text = st.text_input("🔍 ค้นหา (พิมพ์ชื่อยา, รหัส, หรือชื่อการค้า)", "")
        
        # กรองข้อมูล
        if search_text:
            # ค้นหาใน DisplayName, CODE1, และ TradeName
            mask = df['DisplayName'].astype(str).str.contains(search_text, case=False, na=False) | \
                   df['CODE1'].astype(str).str.contains(search_text, case=False, na=False) | \
                   df['TradeName'].astype(str).str.contains(search_text, case=False, na=False)
            result = df[mask]
        else:
            result = df # ถ้าไม่ค้นหา ให้แสดงทั้งหมด

        st.write(f"ผลลัพธ์: {len(result)} รายการ")
        
        # แสดงผลแบบการ์ด (จำกัด 100 รายการแรก เพื่อความลื่นไหล)
        for index, row in result.head(100).iterrows():
            with st.container():
                # ส่วนหัวการ์ด
                c1, c2 = st.columns([0.8, 0.2])
                c1.subheader(f"💊 {row['DisplayName']}")
                
                # ตรวจสอบวันหมดอายุ
                if 'ExpDate' in row and pd.notnull(row['ExpDate']):
                    exp_date = row['ExpDate'].strftime('%d/%m/%Y')
                    if row['ExpDate'] < pd.Timestamp.now():
                         c2.error(f"EXP: {exp_date}") # แดง = หมดอายุ
                    else:
                         c2.success(f"EXP: {exp_date}") # เขียว = ปกติ
                else:
                    c2.info("EXP: -")

                # รายละเอียด
                st.caption(f"Code: {row['CODE1']} | TradeName: {row['TradeName']}")
                
                # ข้อมูลตัวเลข
                m1, m2, m3 = st.columns(3)
                m1.metric("📦 คงเหลือ", row['QtyDisplay'])
                m2.metric("💰 ราคา", f"{row['price']:,.2f}")
                m3.metric("🏷️ Lot", str(row['LotNo']))
                
                st.divider()

    else:
        st.error(f"⚠️ อ่านไฟล์ไม่ได้: {status}")
else:
    st.info("👋 กรุณาอัปโหลดไฟล์ Excel เพื่อเริ่มใช้งาน")
