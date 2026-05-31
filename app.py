import streamlit as st
import pandas as pd
import re
from datetime import datetime, time, timedelta
from ortools.sat.python import cp_model

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Phòng khám Hàng Bông - Vận hành", layout="wide")

# --- ĐỊNH NGHĨA BIẾN CẤU HÌNH (QUAN TRỌNG: ĐẶT Ở ĐÂY ĐỂ TRÁNH NAMEERROR) ---
DOCTOR_LIST = ["TS Đặng Hữu Phúc", "Th.S Nguyễn Thảo Dương", "BS Đỗ Phi Hưng", "BS Nguyễn Thu Hương", "BS Thương yêu", "Th.s Vương Ngọc Toàn", "BS Quan Thị Giao Linh", "BS Nguyễn Nhật Anh"]
DURATIONS = {"Khám mới": 3, "Tái khám": 3, "Điều trị theo vùng": 5, "Điều trị chuyên sâu": 8}
HORIZON = 34 

if 'patients_list' not in st.session_state:
    st.session_state.patients_list = []

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

    if st.button("Chạy Tối ưu hóa Toàn bộ"):
        df_all = pd.DataFrame(st.session_state.patients_list)
        if df_all.empty: st.warning("Danh sách trống!"); st.stop()
        
        # Sắp xếp theo ngày
        df_all["Ngày Khám/Trị liệu"] = pd.to_datetime(df_all["Ngày Khám/Trị liệu"]).dt.date
        df_all = df_all.sort_values(by="Ngày Khám/Trị liệu").reset_index(drop=True)
        
        all_results = []
        for target_date in df_all["Ngày Khám/Trị liệu"].unique():
            df_today = df_all[df_all["Ngày Khám/Trị liệu"] == target_date].reset_index(drop=True)
            model = cp_model.CpModel()
            
            x = {}
            # Logic tối ưu: Mỗi bệnh nhân được gán 1 Bác sĩ và 1 Giờ
            for i, row in df_today.iterrows():
                d_dur = DURATIONS.get(row["Dịch vụ"], 3)
                valid_docs = [DOCTOR_LIST.index(row["Bác sĩ"])] if pd.notna(row["Bác sĩ"]) and row["Bác sĩ"] in DOCTOR_LIST else range(len(DOCTOR_LIST))
                
                # Ràng buộc chuyên môn (3 bác sĩ đầu làm ca khó)
                if row["Dịch vụ"] in ["Điều trị theo vùng", "Điều trị chuyên sâu"]:
                    valid_docs = [d for d in valid_docs if d <= 2]
                
                for d in valid_docs:
                    for t in range(HORIZON - d_dur + 1):
                        # Loại trừ nghỉ trưa (16-22) và đảm bảo kết thúc trước 18h
                        if (t + d_dur <= 16) or (22 <= t and t + d_dur <= 34):
                            x[i, d, t] = model.NewBoolVar(f'x_{i}_{d}_{t}')
            
            # Ràng buộc: Mỗi người 1 lịch
            for i in range(len(df_today)):
                model.Add(sum(x[i, d, t] for (p, d, t) in x if p == i) == 1)
                
            # Ràng buộc: Không trùng lịch Bác sĩ
            for d in range(len(DOCTOR_LIST)):
                for t in range(HORIZON):
                    model.Add(sum(x[i, doc, start] for (i, doc, start) in x 
                              if doc == d and start <= t < start + DURATIONS.get(df_today.iloc[i]["Dịch vụ"], 3)) <= 1)
            
            solver = cp_model.CpSolver()
            if solver.Solve(model) == cp_model.OPTIMAL:
                for i, row in df_today.iterrows():
                    for (p_i, d, t) in x:
                        if p_i == i and solver.Value(x[p_i, d, t]) == 1:
                            h, m = 8 + (t * 15) // 60, (t * 15) % 60
                            all_results.append({
                                "Ngày Khám/Trị liệu": target_date,
                                "Bác sỹ": DOCTOR_LIST[d],
                                "Dịch vụ": row["Dịch vụ"],
                                "Giờ Khám/Trị liệu": f"{h:02d}:{m:02d}",
                                "Khách hàng": row["Họ tên"]
                            })
        
        if all_results:
            st.success("Tối ưu hóa toàn bộ thành công!")
            
            # Tạo DataFrame kết quả
            df_res = pd.DataFrame(all_results)
            
            # 1. Xử lý sắp xếp thời gian (để hiển thị thứ tự giờ trong cây)
            df_res["_sort_time"] = pd.to_datetime(df_res["Giờ Khám/Trị liệu"], format="%H:%M").dt.time
            df_res = df_res.sort_values(by=["Ngày Khám/Trị liệu", "Bác sỹ", "_sort_time"])
            
            # 2. Định dạng lại cấu trúc bảng để hiển thị dạng cây (Multi-Index)
            # Chúng ta đẩy các cột nhóm làm index
            df_display = df_res.set_index(["Ngày Khám/Trị liệu", "Bác sỹ"])
            
            # 3. Giữ lại các cột cần thiết (Dịch vụ, Giờ, Khách hàng)
            df_display = df_display[["Giờ Khám/Trị liệu", "Dịch vụ", "Khách hàng"]]
            
            st.subheader("📋 Lịch khám phân cấp (Ngày -> Bác sĩ -> Khách hàng)")
            
            # Hiển thị bảng dạng cây
            st.dataframe(
                df_display, 
                use_container_width=True
            )
        else:
            st.error("⚠️ Không tìm thấy phương án tối ưu!")

    if st.button("Xóa toàn bộ danh sách"):
        st.session_state.patients_list = []
        st.rerun()

st.markdown("---")
st.caption("Ứng dụng quản trị vận hành phòng khám - Tối ưu hóa bằng CP-SAT")
