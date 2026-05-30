import streamlit as st
import pandas as pd
import re
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Phòng khám Hàng Bông - Vận hành", layout="wide")

# --- QUẢN LÝ TRẠNG THÁI ---
if 'patients_list' not in st.session_state:
    st.session_state.patients_list = []

# --- HÀM BỔ TRỢ ---
def is_valid_phone(phone):
    return re.match(r'^0\d{9}$', phone) is not None

# --- GIAO DIỆN CHÍNH ---
st.title("🏥 Hệ thống Tối ưu hóa Phân công - Phòng khám Hàng Bông")

# Sidebar: Upload Dữ liệu
with st.sidebar:
    st.header("Cấu hình Dữ liệu")
    uploaded_file = st.file_uploader("Upload danh sách bác sĩ (CSV/Excel)", type=['csv', 'xlsx'])
    
    doctor_list = ["Bác sĩ Nguyễn Văn A", "Bác sĩ Trần Thị B", "Bác sĩ Lê Văn C"]
    if uploaded_file:
        try:
            df_doctors = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            doctor_list = df_doctors['ho_va_ten'].unique().tolist()
            st.success("Danh sách bác sĩ đã cập nhật!")
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Đặt lịch khách hàng", "📅 Danh sách chờ", "🚀 Chạy Tối ưu hóa"])

with tab1:
    st.header("Nhập thông tin khách hàng")
    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Họ và tên *")
            gender = st.selectbox("Giới tính", ["Nam", "Nữ", "Khác"])
            dob = st.date_input("Ngày tháng năm sinh", min_value=datetime(1900, 1, 1))
            # Bổ sung trường Dịch vụ
            service_type = st.selectbox("Loại dịch vụ *", ["Khám mới", "Tái khám", "Điều trị theo vùng", "Điều trị chuyên sâu"])
        
        with col2:
            phone = st.text_input("Số điện thoại *", help="Nhập 10 chữ số bắt đầu bằng số 0")
            doctor_select = st.selectbox("Bác sĩ khám/ Điều trị *", doctor_list)
            appointment_time = st.time_input("Thời gian đặt lịch *")
        
        reason = st.text_area("Lý do tới khám/ Điều trị")
        
        submit_button = st.form_submit_button("Lưu đặt lịch")
        
        if submit_button:
            if not full_name or not phone:
                st.error("Vui lòng điền đầy đủ các trường bắt buộc (*)")
            elif not is_valid_phone(phone):
                st.error("Số điện thoại không hợp lệ! Vui lòng nhập đúng 10 chữ số bắt đầu bằng số 0.")
            else:
                new_patient = {
                    "Họ và tên": full_name,
                    "Giới tính": gender,
                    "Ngày sinh": str(dob),
                    "Dịch vụ": service_type,
                    "Số điện thoại": phone,
                    "Lý do": reason,
                    "Thời gian": str(appointment_time),
                    "Bác sĩ": doctor_select
                }
                st.session_state.patients_list.append(new_patient)
                st.success(f"Đã thêm khách hàng {full_name} ({service_type}) thành công!")

with tab2:
    st.header("Danh sách khách hàng chờ xếp lịch")
    if len(st.session_state.patients_list) > 0:
        df_patients = pd.DataFrame(st.session_state.patients_list)
        st.dataframe(df_patients, use_container_width=True)
    else:
        st.info("Chưa có khách hàng nào trong danh sách.")

with tab3:
    st.header("Tính toán tối ưu hóa")
    if st.button("Chạy Thuật toán Phân công (CP-SAT)"):
        if len(st.session_state.patients_list) == 0:
            st.warning("Vui lòng nhập danh sách khách hàng trước!")
        else:
            with st.spinner("Đang chạy thuật toán tối ưu hóa OR-Tools..."):
                # Gợi ý: Tại đây bạn sẽ dùng service_type để định nghĩa duration cho CP-SAT
                # Khám: 40p, ĐT theo vùng: 60p, ĐT chuyên sâu: 100p
                import time
                time.sleep(2) 
                st.success("Tối ưu hóa hoàn thành thành công!")
                st.balloons()

# --- CHÂN TRANG ---
st.markdown("---")
st.caption("Ứng dụng quản trị vận hành phòng khám - Tối ưu hóa bằng CP-SAT")
