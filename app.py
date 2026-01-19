import streamlit as st
import pandas as pd

# --------------------------------------------------------
# 1. ส่วนตั้งค่า CSS (ปรับแต่งสี Admin และ File Uploader)
# --------------------------------------------------------
st.markdown("""
    <style>
        /* ปรับแต่งช่อง Upload File ให้เป็น Modern Style */
        [data-testid='stFileUploader'] {
            width: 100%;
        }
        
        /* ส่วนพื้นที่วางไฟล์ (Dropzone) */
        [data-testid='stFileUploader'] section {
            background-color: #ffffff; /* พื้นหลังสีขาว */
            border: 2px dashed #2563EB; /* เส้นขอบประสีน้ำเงิน Modern Blue */
            border-radius: 10px;
            padding: 15px;
            color: #1E293B; /* สีข้อความ */
        }
        
        /* ปรับปุ่ม Browse files */
        [data-testid='stFileUploader'] button {
            background-color: #2563EB; /* สีปุ่มน้ำเงิน */
            color: white; /* ตัวหนังสือขาว */
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        
        [data-testid='stFileUploader'] button:hover {
            background-color: #1D4ED8; /* สีเข้มขึ้นเมื่อเอาเมาส์ชี้ */
            color: white;
            border: none;
        }
        
        /* ปรับไอคอน Upload ให้เป็นสีน้ำเงิน */
        [data-testid='stFileUploader'] svg {
            fill: #2563EB !important;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------
# 2. ส่วนแสดงผล Sidebar
# --------------------------------------------------------
with st.sidebar:
    st.header("⚙️ เมนูหลัก")
    
    # Toggle Dark mode (จำลองตามภาพ)
    st.toggle("Dark mode", value=False)
    
    st.markdown("---")
    
    st.subheader("🔐 สำหรับเจ้าหน้าที่")
    
    # --- ส่วนที่ 1: ป้ายสถานะ Admin แบบ Modern Blue ---
    st.markdown("""
        <div style="
            background-color: #E0F2FE; /* พื้นหลังฟ้าอ่อนจางๆ */
            border-left: 5px solid #2563EB; /* แถบสีน้ำเงินด้านซ้าย */
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <span style="color: #2563EB; font-weight: bold; font-size: 1.1em;">
                🛡️ สถานะ: Admin Mode
            </span>
            <p style="margin: 5px 0 0 0; font-size: 0.8em; color: #64748B;">
                คุณมีสิทธิ์เข้าถึงข้อมูลระดับสูง
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- ส่วนที่ 2: ช่อง Upload File (CSS จะทำงานอัตโนมัติ) ---
    st.subheader("📥 อัปเดตฐานข้อมูล")
    st.caption("เลือกไฟล์ Excel")
    
    uploaded_file = st.file_uploader(
        label="Upload Excel", 
        type=['xlsx', 'xls'], 
        label_visibility="collapsed" # ซ่อน Label เดิมเพราะเราใส่หัวข้อข้างบนแล้ว
    )

    if uploaded_file is not None:
        st.success(f"โหลดไฟล์: {uploaded_file.name} เรียบร้อย")

    st.markdown("---")
    
    # ปุ่มออกจากระบบ (ตกแต่งเพิ่มให้เข้าธีม)
    if st.button("ออกจากระบบ", type="primary", use_container_width=True):
        st.write("Logged out...")

# --------------------------------------------------------
# 3. ส่วนแสดงผลหลัก (Main Content Example)
# --------------------------------------------------------
st.title("ระบบสืบค้นคลังยา 🏥")

# (โค้ดแสดงตารางของคุณจะอยู่ส่วนนี้ตามเดิม)
# ตัวอย่าง Mockup ข้อมูลเพื่อให้เห็นภาพ
data = {
    'ชื่อรายการ': ['Amoxycillin 500 mg cap', 'Benadryl 25 mg cap', 'Calcitriol 0.25 mcg cap'],
    'รหัส': ['1000317', '1000219', '1680073'],
    'Tradename': ['MOXI-500', 'Diphenhydramine AP', 'OSSEKA'],
    'คงเหลือ': ['33 x 500', '10 x 1000', '124 x 100']
}
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True)
