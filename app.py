import streamlit as st
import pandas as pd
import re
from datetime import datetime, time, timedelta

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Phòng khám Hàng Bông - Vận hành", layout="wide")

# --- QUẢN LÝ TRẠNG THÁI ---
if 'patients_list' not in st.session_state:
    st.session_state.patients_list = []

# --- HÀM BỔ TRỢ ---
def is_valid_phone(phone):
    return re.match(r'^0\d{9}$', str(phone)) is not None

# --- GIAO DIỆN CHÍNH ---
st.title("🏥 Hệ thống Tối ưu hóa Phân công - Phòng khám Hàng Bông")

# Sidebar
with st.sidebar:
    st.header("Cấu hình Dữ liệu")
    uploaded_file = st.file_uploader("Upload danh sách bác sĩ (CSV/Excel)", type=['csv', 'xlsx'])
    doctor_list = ["TS Đặng Hữu Phúc", "Th.S Nguyễn Thảo Dương", "BS Đỗ Phi Hưng", "BS Nguyễn Thu Hương", "BS Thương yêu", "Th.s Vương Ngọc Toàn", "BS Quan Thị Giao Linh", "BS Nguyễn Nhật Anh"]
    if uploaded_file:
        try:
            df_doctors = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            doctor_list = df_doctors['ho_va_ten'].unique().tolist()
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Đặt lịch khách hàng", "📅 Danh sách chờ", "🚀 Chạy Tối ưu hóa"])

with tab1:
    st.info("⏰ Giờ hoạt động: Sáng (08:00 - 12:00) | Chiều (13:30 - 18:00)")
    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            # Thứ tự yêu cầu: Họ tên, Giới tính, Ngày sinh, Số điện thoại, Dịch vụ
            full_name = st.text_input("Họ tên *")
            gender = st.selectbox("Giới tính", ["Nam", "Nữ", "Khác"])
            dob = st.date_input("Ngày sinh", min_value=datetime(1900, 1, 1))
            phone = st.text_input("Số điện thoại *")
            service_type = st.selectbox("Dịch vụ *", ["Khám mới", "Tái khám", "Điều trị theo vùng", "Điều trị chuyên sâu"])
        
        with col2:
            # Thứ tự yêu cầu: Bác sĩ, Ngày Khám/Trị liệu, Giờ Khám/Trị liệu, Lý do
            doctor_select = st.selectbox("Bác sĩ *", doctor_list)
            exam_date = st.date_input("Ngày Khám/Trị liệu *", min_value=datetime.today())
            
            # Tạo mốc thời gian (bước 15 phút)
            time_options = []
            curr = datetime.combine(datetime.today(), time(8, 0))
            end_morning = datetime.combine(datetime.today(), time(12, 0))
            while curr <= end_morning:
                time_options.append(curr.time()); curr += timedelta(minutes=15)
            curr = datetime.combine(datetime.today(), time(13, 30))
            end_evening = datetime.combine(datetime.today(), time(18, 0))
            while curr <= end_evening:
                time_options.append(curr.time()); curr += timedelta(minutes=15)
            
            appointment_time = st.select_slider("Giờ Khám/Trị liệu *", options=time_options, format_func=lambda x: x.strftime('%H:%M'))
            reason = st.text_area("Lý do")
        
        submit_button = st.form_submit_button("Lưu đặt lịch")
        
        if submit_button:
            if not full_name or not phone:
                st.error("Vui lòng điền đầy đủ các trường bắt buộc (*)")
            elif not is_valid_phone(phone):
                st.error("Số điện thoại không hợp lệ!")
            else:
                new_patient = {
                    "Họ tên": full_name, "Giới tính": gender, "Ngày sinh": str(dob), "Số điện thoại": phone,
                    "Dịch vụ": service_type, "Bác sĩ": doctor_select, "Ngày Khám/Trị liệu": str(exam_date),
                    "Giờ Khám/Trị liệu": str(appointment_time), "Lý do": reason
                }
                st.session_state.patients_list.append(new_patient)
                st.success("Đã thêm khách hàng thành công!")

with tab2:
    st.header("Danh sách khách hàng chờ xếp lịch")
    uploaded_patients = st.file_uploader("Upload file khách hàng", type=['xlsx', 'csv'])
    
    if uploaded_patients:
        try:
            df_new = pd.read_excel(uploaded_patients) if uploaded_patients.name.endswith('.xlsx') else pd.read_csv(uploaded_patients)
            for _, row in df_new.iterrows():
                st.session_state.patients_list.append(row.to_dict())
            st.success("Đã thêm dữ liệu từ file!")
        except Exception as e:
            st.error(f"Lỗi file: {e}")

    if len(st.session_state.patients_list) > 0:
        df_patients = pd.DataFrame(st.session_state.patients_list)
        # Thứ tự cột yêu cầu
        display_cols = ["Họ tên", "Giới tính", "Ngày sinh", "Số điện thoại", "Dịch vụ", "Bác sĩ", "Ngày Khám/Trị liệu", "Giờ Khám/Trị liệu", "Lý do"]
        available_cols = [c for c in display_cols if c in df_patients.columns]
        st.dataframe(df_patients[available_cols], use_container_width=True)
    else:
        st.info("Chưa có khách hàng nào.")

with tab3:
    st.header("Tính toán tối ưu hóa")
    if st.button("Xóa toàn bộ danh sách"):
        st.session_state.patients_list = []
        st.rerun()

st.markdown("---")
st.caption("Ứng dụng quản trị vận hành phòng khám - Tối ưu hóa bằng CP-SAT")
