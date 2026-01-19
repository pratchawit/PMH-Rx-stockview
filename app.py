import streamlit as st
import pandas as pd
from github import Github
import io
import os

# =========================
# 1) ตั้งค่าหน้าเว็บ
# =========================
st.set_page_config(
    page_title="Inventory System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

TARGET_FILE_NAME = "InvLotFrmByLot.xlsx"

# =========================
# 2) Session defaults
# =========================
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if "fast_mode" not in st.session_state:
    st.session_state.fast_mode = True

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# =========================
# 3) Theme vars (คำนวณก่อน inject CSS)
# =========================
is_dark = bool(st.session_state.dark_mode)

if is_dark:
    main_bg = "#262730"
    main_text = "#ffffff"
    header_bg = "#262730"
else:
    main_bg = "#f0f2f6"
    main_text = "#31333f"
    header_bg = "#f0f2f6"

fixed_colors = {
    "sidebar_bg": "#f8fafc",
    "sidebar_text": "#1e293b",
    "table_bg_norm": "#ffffff",
    "table_bg_alt": "#f1f5f9",
    "table_text": "#1e293b",
}

# =========================
# 4) CSS Injection (รวม fix eye icon)
# =========================
st.markdown(
    f"""
    <style>
    /* พื้นหลังหลัก */
    .stApp {{ background-color: {main_bg}; color: {main_text}; }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{ background-color: {fixed_colors['sidebar_bg']}; }}
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label {{ color: {fixed_colors['sidebar_text']} !important; }}

    /* --- SEARCH BOX (หน้าหลัก) --- */
    section[data-testid="stMain"] div[data-baseweb="input"] {{
        background-color: #ffffff !important;
        border: 2px solid #CBD5E1 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }}
    section[data-testid="stMain"] input {{
        color: #1e293b !important;
    }}

    /* --- PASSWORD INPUT (Eye icon ชิดขวา + ย่อขนาดได้) --- */
    section[data-testid="stSidebar"] input[type="password"] {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        caret-color: #ffffff !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="input"] {{
        background-color: #334155 !important;
        border: 1px solid #475569 !important;
        border-radius: 6px !important;

        display: flex !important;
        align-items: center !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="input"] > div:first-child {{
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="input"] > div:last-child {{
        flex: 0 0 auto !important;
        margin-left: auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;

        padding-right: 6px !important;
        background: transparent !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="input"] > div:last-child button {{
        width: 28px !important;
        height: 28px !important;
        min-width: 28px !important;

        padding: 0 !important;
        margin: 0 !important;
        border-radius: 6px !important;
        background: transparent !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="input"] > div:last-child svg {{
        width: 16px !important;
        height: 16px !important;

        color: #94a3b8 !important;
        stroke: #94a3b8 !important;
        fill: #94a3b8 !important;
    }}

    /* Sticky Header */
    .sticky-top-container {{
        position: sticky; top: 0; z-index: 990;
        background-color: {header_bg};
        padding: 10px 20px;
        border-bottom: 1px solid rgba(128,128,128, 0.2);
        margin-left: -1rem; margin-right: -1rem;
    }}

    /* Typography */
    .app-title {{ font-size: 1.8rem; font-weight: 800; color: {main_text}; margin-bottom: 5px; }}
    .search-label {{ font-weight: bold; margin-bottom: 5px; font-size: 1.1rem; color: {main_text}; }}
    header[data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}

    /* Toggle panel */
    div[data-testid="stToggle"] {{
        background-color: #E2E8F0; padding: 15px; border-radius: 8px; border: 1px solid #CBD5E1; margin-bottom: 10px;
    }}

    /* Upload Style */
    [data-testid='stFileUploader'] section {{
        background-color: #F0F9FF; border: 2px dashed #2563EB; border-radius: 10px; padding: 15px;
    }}
    [data-testid='stFileUploader'] svg, [data-testid='stFileUploader'] div {{ fill: #2563EB !important; color: #1E3A8A !important; }}
    [data-testid='stFileUploader'] button {{ background-color: #2563EB; color: white !important; border: none; }}

    /* Logout Button */
    section[data-testid="stSidebar"] .stButton:last-of-type button {{
        background-color: #FF5722 !important;
        color: white !important;
        border: none !important;
        font-weight: bold;
    }}

    /* Form Login Button */
    div[data-testid="stForm"] button {{
        width: 100%;
        background-color: #66D9A5 !important;
        color: white !important;
        border: none !important;
        font-weight: bold;
        margin-top: 10px;
    }}
    div[data-testid="stForm"] button:hover {{
        background-color: #57C293 !important;
    }}

    /* Table Header */
    div[data-testid="stDataFrame"] div[role="columnheader"] {{
        font-weight: 900 !important;
        color: {main_text} !important;
        background-color: #e0e0e0 !important;
        justify-content: center !important;
        text-align: center !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# 5) Helpers
# =========================
def fix_thai_encoding(text):
    if not isinstance(text, str):
        return text
    try:
        return text.encode("cp1252").decode("cp874")
    except Exception:
        return text

@st.cache_resource(show_spinner=False)
def get_repo():
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    return Github(token).get_repo(repo_name)

def upload_to_github(file_content: bytes):
    try:
        repo = get_repo()
        try:
            contents = repo.get_contents(TARGET_FILE_NAME)
            repo.update_file(contents.path, "Update data", file_content, contents.sha)
            return True, "อัปเดตสำเร็จ!"
        except Exception:
            repo.create_file(TARGET_FILE_NAME, "Initial upload", file_content)
            return True, "สร้างไฟล์ใหม่สำเร็จ!"
    except Exception as e:
        return False, f"GitHub Error: {str(e)}"

@st.cache_data(ttl=600, show_spinner=False)  # cache 10 นาที
def load_data_from_github():
    """
    โหลดไฟล์จาก GitHub + อ่าน Excel + ทำความสะอาด + สร้างคอลัมน์สำหรับค้นหา
    คืนค่า: (df_prepared, report_date_str)
    """
    try:
        repo = get_repo()
        contents = repo.get_contents(TARGET_FILE_NAME)
        file_bytes = contents.decoded_content

        # อ่าน excel (robust)
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception:
            try:
                df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
            except Exception:
                df = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")

        # Fix encoding
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].apply(fix_thai_encoding)
        df.columns = [fix_thai_encoding(c) for c in df.columns]
        df.columns = df.columns.astype(str).str.strip()

        # report_date
        report_date_str = "-"
        if "d1" in df.columns and not df.empty:
            try:
                raw = df["d1"].iloc[0]
                if isinstance(raw, pd.Timestamp):
                    report_date_str = raw.strftime("%d/%m/%Y")
                else:
                    try:
                        report_date_str = pd.to_datetime(fix_thai_encoding(str(raw))).strftime("%d/%m/%Y")
                    except Exception:
                        report_date_str = str(raw)
            except Exception:
                pass

        # Normalize important columns
        trade_col = next((c for c in df.columns if c.lower().replace(" ", "") == "tradename"), None)
        df["TradeName"] = df[trade_col].fillna("-") if trade_col else "-"
        df["LotNo"] = df.get("LotNo", pd.Series(["-"] * len(df))).fillna("-")
        df["price"] = df.get("price", pd.Series([0] * len(df))).fillna(0)

        # DisplayName
        df["DisplayName"] = ""
        if "NAME1" in df.columns:
            df["DisplayName"] += df["NAME1"].fillna("").astype(str) + " "
        if "CONTENT" in df.columns:
            df["DisplayName"] += df["CONTENT"].fillna("").astype(str) + " "
        if "TYPE" in df.columns:
            df["DisplayName"] += df["TYPE"].fillna("").astype(str)
        df["DisplayName"] = df["DisplayName"].str.strip()

        # QtyDisplay
        amt = df["Amount1"].astype(str) if "Amount1" in df.columns else pd.Series(["0"] * len(df))
        unit = df["minofLotPack"].astype(str) if "minofLotPack" in df.columns else pd.Series([""] * len(df))
        df["QtyDisplay"] = amt.astype(str) + " x " + unit.astype(str)

        # SearchBlob (ค้นหา 1 ครั้งเร็วขึ้น)
        code1 = df.get("CODE1", pd.Series([""] * len(df))).fillna("").astype(str)
        df["SearchBlob"] = (
            df["DisplayName"].fillna("").astype(str)
            + " "
            + code1
            + " "
            + df["TradeName"].fillna("").astype(str)
            + " "
            + df["LotNo"].fillna("").astype(str)
        ).str.lower()

        return df, report_date_str
    except Exception:
        return None, "-"

# =========================
# 6) SIDEBAR
# =========================
with st.sidebar:
    st.title("⚙️ เมนูหลัก")

    # Dark mode / Fast mode (ไม่ต้อง st.rerun() เอง)
    st.toggle("🌙 Dark mode", key="dark_mode")
    st.toggle("⚡ โหมดเร็ว (โหลดไวขึ้น)", key="fast_mode")
    st.divider()

    # Login System (ปลอดภัย: ใช้ secrets/env)
    st.write("🔐 **สำหรับเจ้าหน้าที่**")
    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", os.environ.get("ADMIN_PASSWORD", ""))

    if not st.session_state.logged_in:
        with st.form(key="login_form"):
            password = st.text_input("รหัสผ่าน Admin", type="password")
            submit_button = st.form_submit_button("เข้าสู่ระบบ")

        if submit_button:
            if not ADMIN_PASSWORD:
                st.error("⚠️ ยังไม่ได้ตั้งค่า ADMIN_PASSWORD ใน Secrets/Environment")
            elif password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.success("✅ ยินดีต้อนรับ")
            else:
                st.error("❌ รหัสผ่านไม่ถูกต้อง")
    else:
        st.markdown(
            """
            <div style="
                background-color: #EFF6FF;
                border-left: 5px solid #2563EB;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            ">
                <div style="color: #2563EB; font-weight: bold; font-size: 1.1rem; display: flex; align-items: center;">
                    🛡️ สถานะ: Admin
                </div>
                <div style="color: #60A5FA; font-size: 0.85rem; margin-top: 4px;">
                    พร้อมสำหรับอัปเดตข้อมูล
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("📥 **อัปเดตฐานข้อมูล**")
        uploaded_file = st.file_uploader("เลือกไฟล์ Excel", type=["xlsx", "xls"])

        if uploaded_file:
            if st.button("🚀 อัปโหลดขึ้น Server"):
                with st.status("กำลังดำเนินการ...", expanded=True) as status:
                    success, msg = upload_to_github(uploaded_file.getvalue())
                    if success:
                        status.update(label="✅ สำเร็จ", state="complete")
                        st.success(msg)
                        # เคลียร์ cache เฉพาะข้อมูลที่โหลดจาก GitHub
                        load_data_from_github.clear()
                        st.rerun()
                    else:
                        status.update(label="❌ ล้มเหลว", state="error")
                        st.error(msg)

        st.markdown("---")
        if st.button("ออกจากระบบ", key="logout_btn"):
            st.session_state.logged_in = False
            st.success("ออกจากระบบแล้ว")

# =========================
# 7) MAIN CONTENT
# =========================
with st.spinner("กำลังโหลดข้อมูล..."):
    df, report_date_str = load_data_from_github()

# --- UI HEADER (Sticky) ---
st.markdown('<div class="sticky-top-container">', unsafe_allow_html=True)
c_logo, c_title, c_search = st.columns([0.15, 0.5, 0.35])

with c_logo:
    logo_path = "PMH Rxstock LineOA.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=100)
    else:
        st.write("🏥")

with c_title:
    st.markdown(
        f"""
        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
            <div class="app-title">ระบบสืบค้นคลังยา</div>
            <div>
                <span style="background-color:#059669; color:white; padding:4px 12px; border-radius:15px; font-weight:bold; font-size: 0.9rem;">
                    📅 ข้อมูลวันที่: {report_date_str}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c_search:
    st.markdown('<div class="search-label">🔍 ค้นหารายการยา</div>', unsafe_allow_html=True)

    # Search แบบ form: ไม่ rerun ทุกครั้งที่พิมพ์
    with st.form("search_form", clear_on_submit=False):
        q = st.text_input(
            "Search",
            value=st.session_state.search_query,
            placeholder="พิมพ์ชื่อยา, รหัส หรือ Lot...",
            label_visibility="collapsed",
        )
        col_a, col_b = st.columns([0.65, 0.35])
        with col_a:
            submitted = st.form_submit_button("ค้นหา")
        with col_b:
            cleared = st.form_submit_button("ล้าง")

    if submitted:
        st.session_state.search_query = q.strip()
    if cleared:
        st.session_state.search_query = ""

st.markdown("</div>", unsafe_allow_html=True)

search_query = (st.session_state.search_query or "").strip()

# =========================
# 8) RESULT TABLE
# =========================
if df is None:
    st.info("👋 ยินดีต้อนรับ กรุณาให้เจ้าหน้าที่ Login เพื่ออัปโหลดข้อมูลครั้งแรก")
else:
    if search_query:
        q_lower = search_query.lower()
        mask = df["SearchBlob"].str.contains(q_lower, na=False, regex=False)
        display_df = df.loc[mask].copy()
    else:
        display_df = df.copy()

    if display_df.empty:
        st.warning(f"ไม่พบข้อมูล '{search_query}'")
    else:
        # Exp date
        if "ExpDate" in display_df.columns:
            exp_show = pd.to_datetime(display_df["ExpDate"], errors="coerce").dt.strftime("%d-%m-%Y")
            display_df["EXP_Show"] = exp_show.fillna("-")
        else:
            display_df["EXP_Show"] = "-"

        cols_map = {
            "DisplayName": "ชื่อรายการ",
            "CODE1": "รหัส",
            "TradeName": "Tradename",
            "QtyDisplay": "คงเหลือ",
            "price": "ทุน",
            "LotNo": "Lot",
            "EXP_Show": "EXP",
        }

        valid_cols = [c for c in cols_map.keys() if c in display_df.columns]
        table = display_df[valid_cols].copy().rename(columns=cols_map)

        final_cols = [c for c in ["ชื่อรายการ", "รหัส", "Tradename", "คงเหลือ", "ทุน", "Lot", "EXP"] if c in table.columns]
        table = table[final_cols].reset_index(drop=True)

        # โหมดเร็ว: ไม่ใช้ Styler (เร็วกว่าเยอะ)
        if st.session_state.fast_mode:
            column_config = {}
            if "ทุน" in table.columns:
                column_config["ทุน"] = st.column_config.NumberColumn("ทุน", format="%,.2f")
                # ensure numeric
                table["ทุน"] = pd.to_numeric(table["ทุน"], errors="coerce").fillna(0)

            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
                height=600,
                column_config=column_config if column_config else None,
            )
        else:
            # โหมดสวย: ใช้ styler (ช้ากว่า)
            group_ids = (table["ชื่อรายการ"] != table["ชื่อรายการ"].shift()).cumsum()
            rows_alt = table.index[group_ids % 2 == 1]
            rows_norm = table.index[group_ids % 2 == 0]

            styler = table.style.format(precision=2)
            if "ทุน" in table.columns:
                styler = styler.format({"ทุน": "{:,.2f}"})

            styler = styler.set_properties(
                subset=pd.IndexSlice[rows_alt, :],
                **{"background-color": fixed_colors["table_bg_alt"]},
            )
            styler = styler.set_properties(
                subset=pd.IndexSlice[rows_norm, :],
                **{"background-color": fixed_colors["table_bg_norm"]},
            )
            styler = styler.set_properties(**{"color": fixed_colors["table_text"]})

            st.dataframe(styler, use_container_width=True, hide_index=True, height=600)
