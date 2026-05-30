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

# --- CẤU HÌNH DỮ LIỆU CỐ ĐỊNH ---
DOCTOR_LIST = ["TS Đặng Hữu Phúc", "Th.S Nguyễn Thảo Dương", "BS Đỗ Phi Hưng", "BS Nguyễn Thu Hương", "BS Thương yêu", "Th.s Vương Ngọc Toàn", "BS Quan Thị Giao Linh", "BS Nguyễn Nhật Anh"]
DURATIONS = {"Khám mới": 3, "Tái khám": 3, "Điều trị theo vùng": 5, "Điều trị chuyên sâu": 8}
HORIZON = 34 

st.title("🏥 Hệ thống Tối ưu hóa Phân công - Phòng khám Hàng Bông")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Đặt lịch khách hàng", "📅 Danh sách chờ", "🚀 Chạy Tối ưu hóa"])

with tab1:
    with st.form("booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Họ tên *")
        gender = c2.selectbox("Giới tính", ["Nam", "Nữ", "Khác"])
        c3, c4 = st.columns(2)
        dob = c3.date_input("Ngày sinh", min_value=datetime(1900, 1, 1))
        phone = c4.text_input("Số điện thoại *")
        c5, c6 = st.columns(2)
        service_type = c5.selectbox("Dịch vụ *", list(DURATIONS.keys()))
        doctor_select = c6.selectbox("Bác sĩ (Để trống nếu tự tối ưu)", [None] + DOCTOR_LIST)
        c7, c8 = st.columns(2)
        exam_date = c7.date_input("Ngày Khám/Trị liệu *", min_value=datetime.today())
        reason = st.text_area("Lý do")
        
        if st.form_submit_button("Lưu đặt lịch"):
            if not full_name or not phone: st.error("Điền đầy đủ các trường (*)")
            else:
                st.session_state.patients_list.append({
                    "Họ tên": full_name, "Giới tính": gender, "Ngày sinh": str(dob), 
                    "Số điện thoại": phone, "Dịch vụ": service_type, "Bác sĩ": doctor_select, 
                    "Ngày Khám/Trị liệu": str(exam_date), "Lý do": reason
                })
                st.success("Đã thêm khách hàng!")

with tab2:
    uploaded_patients = st.file_uploader("Upload file khách hàng", type=['xlsx', 'csv'])
    if uploaded_patients:
        df_new = pd.read_excel(uploaded_patients) if uploaded_patients.name.endswith('.xlsx') else pd.read_csv(uploaded_patients)
        st.session_state.patients_list = df_new.to_dict('records')
        st.success("Đã nạp file!")
    
    if len(st.session_state.patients_list) > 0:
        df_p = pd.DataFrame(st.session_state.patients_list)
        df_p["Số điện thoại"] = df_p["Số điện thoại"].astype(str).str.replace(r'\.0$', '', regex=True).apply(lambda x: x.zfill(10))
        df_p["TT"] = range(1, len(df_p) + 1)
        st.dataframe(df_p, use_container_width=True, hide_index=True)

with tab3:
    target_date = st.date_input("Chọn ngày chạy tối ưu:", min_value=datetime.today())
    if st.button("Chạy Thuật toán Phân công"):
        df_today = pd.DataFrame(st.session_state.patients_list)
        df_today["Ngày Khám/Trị liệu"] = pd.to_datetime(df_today["Ngày Khám/Trị liệu"]).dt.date
        df_today = df_today[df_today["Ngày Khám/Trị liệu"] == target_date]
        
        if df_today.empty: st.warning("Danh sách trống!"); st.stop()
        
        model = cp_model.CpModel()
        x = {}
        # Solver sử dụng Boolean Variables (0/1)
        for i, row in df_today.iterrows():
            d_dur = DURATIONS.get(row["Dịch vụ"], 3)
            # Logic: Nếu chọn BS thì ép buộc, nếu để trống thì lấy tất cả BS phù hợp chuyên môn
            valid_docs = [DOCTOR_LIST.index(row["Bác sĩ"])] if pd.notna(row["Bác sĩ"]) and row["Bác sĩ"] in DOCTOR_LIST else range(len(DOCTOR_LIST))
            if row["Dịch vụ"] in ["Điều trị theo vùng", "Điều trị chuyên sâu"]:
                valid_docs = [d for d in valid_docs if d <= 2] # Chỉ 3 BS đầu
            
            for d in valid_docs:
                for t in range(HORIZON - d_dur + 1):
                    if not (t >= 16 and t < 22): # Bỏ qua nghỉ trưa
                        x[i, d, t] = model.NewBoolVar(f'x_p{i}_d{d}_t{t}')
        
        # Ràng buộc: Mỗi người 1 lịch
        for i in range(len(df_today)): model.Add(sum(x[i, d, t] for (p, d, t) in x if p == i) == 1)
        # Ràng buộc: Không trùng lịch BS
        for d in range(len(DOCTOR_LIST)):
            for t in range(HORIZON):
                model.Add(sum(x[i, doc, start] for (i, doc, start) in x if doc == d and start <= t < start + DURATIONS.get(df_today.iloc[i]["Dịch vụ"], 3)) <= 1)

        solver = cp_model.CpSolver()
        if solver.Solve(model) == cp_model.OPTIMAL:
            st.success("Tối ưu hóa thành công!")
            results = []
            for i, row in df_today.iterrows():
                for (p, d, t) in x:
                    if p == i and solver.Value(x[p, d, t]) == 1:
                        h, m = 8 + (t * 15) // 60, (t * 15) % 60
                        results.append({"Họ tên": row["Họ tên"], "Giờ": f"{h:02d}:{m:02d}", "Bác sĩ": DOCTOR_LIST[d]})
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.error("⚠️ Không tìm thấy phương án!")
            st.info("Nguyên nhân: Danh sách quá tải hoặc thiếu Bác sĩ chuyên môn (3 bác sĩ đầu làm dịch vụ khó).")

    if st.button("Xóa toàn bộ"):
        st.session_state.patients_list = []
        st.rerun()

st.markdown("---")
st.caption("Ứng dụng quản trị phòng khám - CP-SAT Solver")
