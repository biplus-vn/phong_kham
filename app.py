import streamlit as st
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Vận hành Phòng khám Hàng Bông", layout="wide")

# --- QUẢN LÝ TRẠNG THÁI ---
if 'patients_list' not in st.session_state:
    st.session_state.patients_list = []

# --- GIAO DIỆN CHÍNH ---
st.title("🏥 Hệ thống Phân công Bác sĩ & Lịch trình")

# Sidebar: Upload Dữ liệu
with st.sidebar:
    st.header("Cấu hình Dữ liệu")
    uploaded_file = st.file_uploader("Upload danh sách bác sĩ (CSV/Excel)", type=['csv', 'xlsx'])
    
    # Giả định danh sách bác sĩ lấy từ file
    doctor_list = ["Bác sĩ Nguyễn Văn A", "Bác sĩ Trần Thị B", "Bác sĩ Lê Văn C"]
    if uploaded_file:
        try:
            df_doctors = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
            doctor_list = df_doctors['ho_va_ten'].unique().tolist()
            st.success("Đã tải danh sách bác sĩ thành công!")
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

# --- TABS GIAO DIỆN ---
tab1, tab2, tab3 = st.tabs(["📋 Đặt lịch khách hàng", "📅 Danh sách chờ", "🚀 Chạy Tối ưu hóa"])

with tab1:
    st.header("Nhập thông tin khách hàng")
    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Họ và tên *")
            gender = st.selectbox("Giới tính", ["Nam", "Nữ", "Khác"])
            dob = st.date_input("Ngày tháng năm sinh", min_value=datetime(1900, 1, 1))
        
        with col2:
            phone = st.text_input("Số điện thoại *")
            doctor_select = st.selectbox("Bác sĩ khám/ Điều trị *", doctor_list)
            appointment_time = st.time_input("Thời gian đặt lịch *")
        
        reason = st.text_area("Lý do tới khám/ Điều trị")
        
        submit_button = st.form_submit_button("Đặt lịch")
        
        if submit_button:
            if not full_name or not phone:
                st.error("Vui lòng điền đầy đủ các trường bắt buộc (*)")
            else:
                new_patient = {
                    "Họ và tên": full_name,
                    "Giới tính": gender,
                    "Ngày sinh": dob,
                    "Số điện thoại": phone,
                    "Lý do": reason,
                    "Thời gian": appointment_time,
                    "Bác sĩ": doctor_select
                }
                st.session_state.patients_list.append(new_patient)
                st.success(f"Đã thêm khách hàng {full_name} vào hệ thống!")

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
                # Tại đây sẽ tích hợp code ortools.sat.python.cp_model
                # Mô phỏng quá trình tính toán
                import time
                time.sleep(2) 
                st.success("Tối ưu hóa thành công! Kết quả phân bổ:")
                st.table(pd.DataFrame(st.session_state.patients_list))

# --- CHÂN TRANG ---
st.markdown("---")
st.caption("Ứng dụng quản trị vận hành phòng khám - Tối ưu hóa bằng CP-SAT")
```eof

### Gợi ý cho bạn:
1.  **Dữ liệu thực tế:** Trong Tab 3, khi bạn viết thuật toán `ortools`, hãy chuyển đổi `st.session_state.patients_list` thành một DataFrame. Từ đó, bạn có thể dễ dàng map (ánh xạ) dữ liệu này vào các biến của `cp_model` (ví dụ: tạo biến quyết định `x[customer_id, doctor_id, time_slot]`).
2.  **Khả năng mở rộng:** Nếu bạn cần xuất lịch phân bổ ra file Excel để gửi cho bác sĩ hoặc điều dưỡng, bạn có thể thêm một nút `st.download_button` ở Tab 3 để tải kết quả dưới dạng file `.xlsx` bằng thư viện `io` và `xlsxwriter`.
