import streamlit as st
import pandas as pd
import os

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Inventory System", page_icon="🏥", layout="wide")

# --- ฟังก์ชันโหลดข้อมูล (ปรับปรุงให้อ่านไฟล์ชื่อ InvLotFrmByLot) ---
@st.cache_data(ttl="10m") # จำข้อมูลไว้ 10 นาที (ถ้ามีการอัปเดตไฟล์ใหม่ ระบบจะรู้เองเมื่อผ่านไปสักพัก)
def load_data():
    # กำหนดชื่อไฟล์เป้าหมาย (ระบบจะลองหาทั้ง .xlsx และ .xls)
    target_files = ["InvLotFrmByLot.xlsx", "InvLotFrmByLot.xls"]
    
    file_path = None
    for f in target_files:
        if os.path.exists(f):
            file_path = f
            break
            
    if not file_path:
        return None, f"ไม่พบไฟล์ข้อมูลใน GitHub (กรุณาอัปโหลดไฟล์ชื่อ 'InvLotFrmByLot.xlsx' หรือ '.xls')"
    
    try:
        # อ่านไฟล์ Excel
        df = pd.read_excel(file_path)
        df.columns = df.columns.astype(str).str.strip() # ลบช่องว่างหัวตาราง

        # ตรวจสอบคอลัมน์สำคัญ
        required_cols = ['CODE1', 'NAME1', 'Amount1', 'minofLotPack']
        if not all(col in df.columns for col in required_cols):
            return None, "ข้อมูลในไฟล์ไม่ครบ (ต้องมี CODE1, NAME1, Amount1, minofLotPack)"

        # --- จัดการข้อมูล ---
        # 1. TradeName (หาชื่อที่ใกล้เคียง)
        trade_col = next((c for c in df.columns if c.lower().replace(" ", "") == "tradename"), None)
        if trade_col:
            df['TradeName'] = df[trade_col].fillna("-")
        else:
            df['TradeName'] = "-"

        # 2. LotNo & Price
        df['LotNo'] = df.get('LotNo', pd.Series(['-']*len(df))).fillna("-")
        df['price'] = df.get('price', pd.Series([0]*len(df))).fillna(0)
        
        # 3. ExpDate
        if 'ExpDate' in df.columns:
            df['ExpDate'] = pd.to_datetime(df['ExpDate'], errors='coerce')
        else:
            df['ExpDate'] = pd.NaT

        # 4. DisplayName (Name + Content + Type)
        type_col = df['TYPE'].fillna("").astype(str) if 'TYPE' in df.columns else ""
        content_col = df['CONTENT'].fillna("").astype(str) if 'CONTENT' in df.columns else ""
        df['DisplayName'] = df['NAME1'].astype(str) + " " + content_col + " " + type_col
        
        # 5. QtyDisplay
        df['QtyDisplay'] = df['Amount1'].astype(str) + " x " + df['minofLotPack'].astype(str)

        return df, "OK"
    except Exception as e:
        return None, str(e)

# ==========================================
# ส่วนแสดงผลหน้าเว็บ
# ==========================================
st.title("🏥 ระบบสืบค้นคลังยา (Smart Search)")

# โหลดข้อมูลอัตโนมัติ
df, status = load_data()

if df is not None:
    # Header แจ้งสถานะ
    st.success(f"✅ เชื่อมต่อฐานข้อมูลสำเร็จ (อ่านจากไฟล์: InvLotFrmByLot) | จำนวน: {len(df):,} รายการ")

    # ช่องค้นหา
    search_query = st.text_input("🔍 ค้นหา (พิมพ์ชื่อยา, รหัส, หรือชื่อการค้า)", "", placeholder="พิมพ์คำค้นหา...")

    # Logic การค้นหา
    if search_query:
        mask = (
            df['DisplayName'].str.contains(search_query, case=False, na=False) |
            df['CODE1'].astype(str).str.contains(search_query, case=False, na=False) |
            df['TradeName'].str.contains(search_query, case=False, na=False)
        )
        display_df = df[mask]
    else:
        display_df = df # ถ้าไม่ค้น แสดงทั้งหมด

    # --- แสดงตาราง ---
    if not display_df.empty:
        # เลือกคอลัมน์และเรียงลำดับ
        table_data = display_df[[
            'DisplayName', 'CODE1', 'TradeName', 'QtyDisplay', 'price', 'LotNo', 'ExpDate'
        ]].copy()

        # เปลี่ยนชื่อหัวตารางไทย
        table_data.columns = [
            'ชื่อรายการ', 'รหัสรายการ', 'Tradename', 'จำนวนคงเหลือ', 
            'ราคาทุน', 'เลขที่ Lot', 'วันหมดอายุ'
        ]

        # Format ข้อมูลให้อ่านง่าย
        table_data['วันหมดอายุ'] = table_data['วันหมดอายุ'].dt.strftime('%d/%m/%Y').fillna("-")
        table_data['ราคาทุน'] = table_data['ราคาทุน'].apply(lambda x: f"{x:,.2f}")

        # แสดงผล
        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
            height=600
        )
    else:
        st.warning("ไม่พบข้อมูลที่ค้นหา")

else:
    # กรณีหาไฟล์ไม่เจอ หรือมี Error
    st.error(f"❌ เกิดข้อผิดพลาด: {status}")
    st.info("💡 วิธีแก้ไข: กรุณาอัปโหลดไฟล์ Excel ชื่อ 'InvLotFrmByLot.xlsx' (หรือ .xls) ขึ้น GitHub ในที่เก็บไฟล์เดียวกับ app.py")
