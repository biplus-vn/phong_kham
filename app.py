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
    return re.match(r'^0\d{9}$', phone) is not None

# --- GIAO DIỆN CHÍNH ---
st.title("🏥 Hệ thống Tối ưu hóa Phân công - Phòng khám Hàng Bông")

# Sidebar
with st.sidebar:
    st.header("Cấu hình Dữ liệu")
    uploaded_file = st.file_uploader("Upload danh sách bác sĩ (CSV/Excel)", type=['csv', 'xlsx'])
    doctor_list = ["Bác sĩ Nguyễn Văn A", "Bác sĩ Trần Thị B", "Bác sĩ Lê Văn C"]
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
            full_name = st.text_input("Họ và tên *")
            gender = st.selectbox("Giới tính", ["Nam", "Nữ", "Khác"])
            dob = st.date_input("Ngày tháng năm sinh", min_value=datetime(1900, 1, 1))
            service_type = st.selectbox("Loại dịch vụ *", ["Khám mới", "Tái khám", "Điều trị theo vùng", "Điều trị chuyên sâu"])
        
        with col2:
            phone = st.text_input("Số điện thoại *")
            doctor_select = st.selectbox("Bác sĩ khám/ Điều trị *", doctor_list)
            
            # Khởi tạo mốc thời gian (bước 15 phút)
            time_options = []
            curr = datetime.combine(datetime.today(), time(8, 0))
            end_morning = datetime.combine(datetime.today(), time(12, 0))
            while curr <= end_morning:
                time_options.append(curr.time())
                curr += timedelta(minutes=15)
            curr = datetime.combine(datetime.today(), time(13, 30))
            end_evening = datetime.combine(datetime.today(), time(18, 0))
            while curr <= end_evening:
                time_options.append(curr.time())
                curr += timedelta(minutes=15)
            
            appointment_time = st.select_slider("Thời gian đặt lịch *", options=time_options, format_func=lambda x: x.strftime('%H:%M'))
        
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
                st.success(f"Đã thêm khách hàng {full_name} vào hệ thống!")

with tab2:
    st.header("Danh sách khách hàng chờ xếp lịch")
    if len(st.session_state.patients_list) > 0:
        st.dataframe(pd.DataFrame(st.session_state.patients_list), use_container_width=True)
    else:
        st.info("Chưa có khách hàng nào.")

with tab3:
    st.header("Tính toán tối ưu hóa")
    if st.button("Chạy Thuật toán Phân công (CP-SAT)"):
        st.write("Đã sẵn sàng dữ liệu khách hàng cho việc tối ưu hóa.")

# --- CHÂN TRANG ---
st.markdown("---")
st.caption("Ứng dụng quản trị vận hành phòng khám - Tối ưu hóa bằng CP-SAT")
