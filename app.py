import streamlit as st
import pandas as pd
import re
from datetime import datetime, time, timedelta
from ortools.sat.python import cp_model

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
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Họ tên *")
        gender = c2.selectbox("Giới tính", ["Nam", "Nữ", "Khác"])
        c3, c4 = st.columns(2)
        dob = c3.date_input("Ngày sinh", min_value=datetime(1900, 1, 1))
        phone = c4.text_input("Số điện thoại *")
        c5, c6 = st.columns(2)
        service_type = c5.selectbox("Dịch vụ *", ["Khám mới", "Tái khám", "Điều trị theo vùng", "Điều trị chuyên sâu"])
        doctor_select = c6.selectbox("Bác sĩ *", [None] + doctor_list)
        c7, c8 = st.columns(2)
        exam_date = c7.date_input("Ngày Khám/Trị liệu *", min_value=datetime.today())
        appointment_time = c8.time_input("Giờ Khám (Nếu có)")
        reason = st.text_area("Lý do")
        
        submit_button = st.form_submit_button("Lưu đặt lịch")
        if submit_button:
            if not full_name or not phone:
                st.error("Vui lòng điền đầy đủ các trường bắt buộc (*)")
            else:
                new_patient = {
                    "Họ tên": full_name, "Giới tính": gender, "Ngày sinh": str(dob), 
                    "Số điện thoại": phone, "Dịch vụ": service_type, "Bác sĩ": doctor_select, 
                    "Ngày Khám/Trị liệu": str(exam_date), "Giờ Khám/Trị liệu": str(appointment_time) if appointment_time else None, "Lý do": reason
                }
                st.session_state.patients_list.append(new_patient)
                st.success(f"Đã thêm khách hàng {full_name} thành công!")

with tab2:
    st.header("Danh sách khách hàng chờ xếp lịch")
    uploaded_patients = st.file_uploader("Upload file khách hàng", type=['xlsx', 'csv'])
    if uploaded_patients:
        try:
            df_new = pd.read_excel(uploaded_patients) if uploaded_patients.name.endswith('.xlsx') else pd.read_csv(uploaded_patients)
            st.session_state.patients_list = df_new.to_dict('records')
            st.success(f"Đã nạp {len(df_new)} khách hàng.")
        except Exception as e: st.error(f"Lỗi file: {e}")

    if len(st.session_state.patients_list) > 0:
        df_patients = pd.DataFrame(st.session_state.patients_list)
        df_patients["TT"] = range(1, len(df_patients) + 1)
        st.dataframe(df_patients, use_container_width=True, hide_index=True)

with tab3:
    st.header("🚀 Chạy Tối ưu hóa (Phương pháp chuyên sâu)")
    target_date = st.date_input("Chọn ngày tối ưu hóa:", min_value=datetime.today())
    
    if st.button("Chạy Thuật toán Phân công"):
        df_today = pd.DataFrame(st.session_state.patients_list)
        df_today = df_today[df_today["Ngày Khám/Trị liệu"] == str(target_date)]
        
        if df_today.empty: st.warning("Danh sách trống!"); st.stop()
        
        model = cp_model.CpModel()
        horizon = 34
        durations = {"Khám mới": 3, "Tái khám": 3, "Điều trị theo vùng": 5, "Điều trị chuyên sâu": 8}
        
        x = {}
        for i, row in df_today.iterrows():
            d_dur = durations.get(row["Dịch vụ"], 3)
            # Nếu đã chọn bác sĩ, chỉ định đúng index
            valid_docs = [doctor_list.index(row["Bác sĩ"])] if pd.notna(row["Bác sĩ"]) and row["Bác sĩ"] in doctor_list else range(len(doctor_list))
            # Ràng buộc dịch vụ khó
            if row["Dịch vụ"] in ["Điều trị theo vùng", "Điều trị chuyên sâu"]:
                valid_docs = [d for d in valid_docs if d <= 2] 
            
            for d in valid_docs:
                for t in range(horizon - d_dur + 1):
                    x[i, d, t] = model.NewBoolVar(f'x_p{i}_d{d}_t{t}')
        
        for i in range(len(df_today)):
            model.Add(sum(x[i, d, t] for (p, d, t) in x if p == i) == 1)
            
        for d in range(len(doctor_list)):
            for t in range(horizon):
                model.Add(sum(x[i, d, start] for (i, doc, start) in x if doc == d and start <= t < start + durations.get(df_today.iloc[i]["Dịch vụ"], 3)) <= 1)

        solver = cp_model.CpSolver()
        if solver.Solve(model) == cp_model.OPTIMAL:
            st.success("Phân bổ tự động hoàn thành!")
            results = []
            for i, row in df_today.iterrows():
                for (p, d, t) in x:
                    if p == i and solver.Value(x[p, d, t]) == 1:
                        h, m = 8 + (t * 15) // 60, (t * 15) % 60
                        results.append({"Họ tên": row["Họ tên"], "Giờ": f"{h:02d}:{m:02d}", "Bác sĩ": doctor_list[d]})
            st.dataframe(pd.DataFrame(results))
        else: st.error("Không tìm thấy phương án tối ưu.")

    if st.button("Xóa toàn bộ danh sách"):
        st.session_state.patients_list = []
        st.rerun()

st.markdown("---")
st.caption("Ứng dụng quản trị vận hành phòng khám - Tối ưu hóa bằng CP-SAT")
