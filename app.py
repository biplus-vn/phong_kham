import streamlit as st
import pandas as pd
import re
from datetime import datetime, time, timedelta

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Phòng khám Hàng Bông - Vận hành", layout="wide")

if 'patients_list' not in st.session_state:
    st.session_state.patients_list = []

def is_valid_phone(phone):
    return re.match(r'^0\d{9}$', str(phone)) is not None

st.title("🏥 Hệ thống Tối ưu hóa Phân công - Phòng khám Hàng Bông")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Đặt lịch khách hàng", "📅 Danh sách chờ", "🚀 Chạy Tối ưu hóa"])

with tab1:
    # (Giữ nguyên form nhập liệu như cũ...)
    pass 

with tab2:
    st.header("Danh sách khách hàng chờ xếp lịch")
    
    # Phần upload file khách hàng
    col_u1, col_u2 = st.columns([1, 3])
    with col_u1:
        uploaded_patients = st.file_uploader("Upload danh sách (Excel/CSV)", type=['xlsx', 'csv'])
    with col_u2:
        st.write("---")
        if st.button("Tải file mẫu"):
            sample_df = pd.DataFrame(columns=["Họ tên", "Giới tính", "Ngày sinh", "Số điện thoại", "Dịch vụ", "Bác sĩ", "Thời gian", "Lý do"])
            # Gợi ý: Dùng st.download_button để tải file này
            st.info("Hãy chuẩn bị file Excel với các cột: Họ tên, Giới tính, Ngày sinh, Số điện thoại, Dịch vụ, Bác sĩ, Thời gian, Lý do")

    if uploaded_patients:
        try:
            df_new = pd.read_excel(uploaded_patients) if uploaded_patients.name.endswith('.xlsx') else pd.read_csv(uploaded_patients)
            # Chuyển dữ liệu mới vào session state
            for _, row in df_new.iterrows():
                st.session_state.patients_list.append(row.to_dict())
            st.success("Đã thêm dữ liệu từ file vào danh sách!")
        except Exception as e:
            st.error(f"Lỗi file: {e}")

    # Hiển thị danh sách
    if len(st.session_state.patients_list) > 0:
        df = pd.DataFrame(st.session_state.patients_list)
        required_cols = ["Họ tên", "Giới tính", "Ngày sinh", "Số điện thoại", "Dịch vụ", "Bác sĩ", "Thời gian", "Lý do"]
        available_cols = [c for c in required_cols if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)
    else:
        st.info("Chưa có khách hàng nào.")

with tab3:
    # (Giữ nguyên phần chạy tối ưu hóa...)
    pass
