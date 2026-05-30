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
        except:
            st.error("Lỗi đọc file")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Đặt lịch khách hàng", "📅 Danh sách chờ", "🚀 Chạy Tối ưu hóa"])

with tab1:
    st.info("⏰ Giờ hoạt động: Sáng (08:00 - 12:00) | Chiều (13:30 - 18:00)")
    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Họ và tên *")
            service_type = st.selectbox("Loại dịch vụ *", ["Khám mới", "Tái khám", "Điều trị theo vùng", "Điều trị chuyên sâu"])
        
        with col2:
            phone = st.text_input("Số điện thoại *")
            doctor_select = st.selectbox("Bác sĩ khám/ Điều trị *", doctor_list)
            
            # GIẢI PHÁP: Sử dụng select_slider để giới hạn khung giờ
            # Tạo danh sách các mốc thời gian 5 phút/lần
            time_options = []
            # Sáng: 8h00 - 12h00
            curr = datetime.combine(datetime.today(), time(8, 0))
            end_morning = datetime.combine(datetime.today(), time(12, 0))
            while curr <= end_morning:
                time_options.append(curr.time())
                curr += timedelta(minutes=15)
            # Chiều: 13h30 - 18h00
            curr = datetime.combine(datetime.today(), time(13, 30))
            end_evening = datetime.combine(datetime.today(), time(18, 0))
            while curr <= end_evening:
                time_options.append(curr.time())
                curr += timedelta(minutes=15)
            
            appointment_time = st.select_slider("Thời gian đặt lịch *", options=time_options, format_func=lambda x: x.strftime('%H:%M'))

        submit_button = st.form_submit_button("Lưu đặt lịch")
        
        if submit_button:
            if not full_name or not phone:
                st.error("Vui lòng điền đủ thông tin bắt buộc (*)")
            elif not is_valid_phone(phone):
                st.error("Số điện thoại không hợp lệ (cần 10 số, bắt đầu bằng 0)")
            else:
                new_patient = {
                    "Họ và tên": full_name, "Dịch vụ": service_type,
                    "Số điện thoại": phone, "Thời gian": str(appointment_time), "Bác sĩ": doctor_select
                }
                st.session_state.patients_list.append(new_patient)
                st.success(f"Đã đặt lịch cho {full_name} lúc {appointment_time}")

with tab2:
    if len(st.session_state.patients_list) > 0:
        st.dataframe(pd.DataFrame(st.session_state.patients_list), use_container_width=True)

with tab3:
    st.header("Tính toán tối ưu hóa")
    if st.button("Chạy Thuật toán Phân công (CP-SAT)"):
        st.write("Đã sẵn sàng các ràng buộc về khung giờ hoạt động.")
