import streamlit as st
import pandas as pd
import re
from datetime import datetime, time

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
    st.info("⏰ Giờ hoạt động: Sáng (08:00 - 12:00) | Chiều (13:30 - 18:00)")
    st.header("Nhập thông tin khách hàng")
    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Họ và tên *")
            gender = st.selectbox("Giới tính", ["Nam", "Nữ", "Khác"])
            service_type = st.selectbox("Loại dịch vụ *", ["Khám mới", "Tái khám", "Điều trị theo vùng", "Điều trị chuyên sâu"])
        
        with col2:
            phone = st.text_input("Số điện thoại *")
            doctor_select = st.selectbox("Bác sĩ khám/ Điều trị *", doctor_list)
            # Ràng buộc thời gian nhập liệu (User cần chọn giờ hợp lệ)
            appointment_time = st.time_input("Thời gian đặt lịch *", value=time(8, 0))
        
        reason = st.text_area("Lý do tới khám/ Điều trị")
        submit_button = st.form_submit_button("Lưu đặt lịch")
        
        if submit_button:
            # Kiểm tra khung giờ hoạt động
            appt = appointment_time
            is_valid_time = (time(8, 0) <= appt <= time(12, 0)) or (time(13, 30) <= appt <= time(18, 0))
            
            if not full_name or not phone:
                st.error("Vui lòng điền đầy đủ các trường bắt buộc (*)")
            elif not is_valid_phone(phone):
                st.error("Số điện thoại không hợp lệ! Vui lòng nhập đúng 10 chữ số bắt đầu bằng số 0.")
            elif not is_valid_time:
                st.error("Thời gian đặt lịch không hợp lệ! Vui lòng chọn trong khung giờ 08:00-12:00 hoặc 13:30-18:00.")
            else:
                new_patient = {
                    "Họ và tên": full_name, "Giới tính": gender, "Dịch vụ": service_type,
                    "Số điện thoại": phone, "Thời gian": str(appointment_time), "Bác sĩ": doctor_select
                }
                st.session_state.patients_list.append(new_patient)
                st.success(f"Đã thêm khách hàng {full_name} thành công!")

with tab2:
    st.header("Danh sách khách hàng chờ xếp lịch")
    if len(st.session_state.patients_list) > 0:
        st.dataframe(pd.DataFrame(st.session_state.patients_list), use_container_width=True)

with tab3:
    st.header("Tính toán tối ưu hóa")
    if st.button("Chạy Thuật toán Phân công (CP-SAT)"):
        # Logic OR-Tools tiếp theo sẽ cần xử lý 2 khoảng thời gian này
        # Bằng cách loại bỏ các 'time_slot' từ 12:00 đến 13:30
        st.write("Đang thực hiện cấu hình ràng buộc thời gian...")
        st.success("Đã thiết lập khung giờ hoạt động cho thuật toán.")

# --- CHÂN TRANG ---
st.markdown("---")
st.caption("Ứng dụng quản trị vận hành phòng khám - Tối ưu hóa bằng CP-SAT")
