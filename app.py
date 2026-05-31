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
            st.success(f"Đã tải thành công {len(df_new)} khách hàng.")
        except Exception as e: st.error(f"Lỗi file: {e}")

    if len(st.session_state.patients_list) > 0:
        df_patients = pd.DataFrame(st.session_state.patients_list)
        st.dataframe(df_patients, use_container_width=True, hide_index=True)

with tab3:
    st.header("🚀 Chạy Tối ưu hóa (Phương pháp chuyên sâu)")

    if st.button("Chạy Tối ưu hóa Toàn bộ"):
        df_all = pd.DataFrame(st.session_state.patients_list)
        if df_all.empty: st.warning("Danh sách trống!"); st.stop()
        
        df_all["Ngày Khám/Trị liệu"] = pd.to_datetime(df_all["Ngày Khám/Trị liệu"]).dt.date
        df_all = df_all.sort_values(by="Ngày Khám/Trị liệu").reset_index(drop=True)
        
        all_results = []
        # Cấu hình tài nguyên vật lý
        PHONG_LIST = ["PK 422", "PK 417", "PK 418"]
        GIUONG_LIST = ["VIP 402", "VIP 416"] + ["ĐT 421-1", "ĐT 421-2", "ĐT 421-3", "ĐT 419-1", "ĐT 419-2", "ĐT 419-3", "ĐT 403-1", "ĐT 403-2", "ĐT 405-1", "ĐT 405-2", "ĐT 407-1", "ĐT 407-2"]
        
        for target_date in df_all["Ngày Khám/Trị liệu"].unique():
            df_today = df_all[df_all["Ngày Khám/Trị liệu"] == target_date].reset_index(drop=True)
            model = cp_model.CpModel()
            x = {}
            
            for i, row in df_today.iterrows():
                is_kham = row["Dịch vụ"] in ["Khám mới", "Tái khám"]
                # Thời lượng = Ca + phát sinh + nghỉ (block 15')
                d_dur = 3 if is_kham else (6 if row["Dịch vụ"] == "Điều trị theo vùng" else 9)
                
                resources = PHONG_LIST if is_kham else GIUONG_LIST
                for r_idx, res_name in enumerate(resources):
                    for t in range(HORIZON - d_dur + 1):
                        if (t + d_dur <= 16) or (22 <= t and t + d_dur <= 34):
                            x[i, r_idx, res_name, t] = model.NewBoolVar(f'x_{i}_{r_idx}_{res_name}_{t}')
            
            # 1. Mỗi bệnh nhân 1 lịch
            for i in range(len(df_today)): 
                model.Add(sum(x[i, r, name, t] for (p_i, r, name, t) in x if p_i == i) == 1)
            
            # 2. Ràng buộc Phòng (Tối đa 3 người/phòng)
            for name in PHONG_LIST:
                for t in range(HORIZON):
                    model.Add(sum(x[i, r, res, start] for (i, r, res, start) in x 
                              if res == name and start <= t < start + 3) <= 3)
            
            # 3. Ràng buộc Giường (Tối đa 1 người/giường)
            for name in GIUONG_LIST:
                for t in range(HORIZON):
                    model.Add(sum(x[i, r, res, start] for (i, r, res, start) in x 
                              if res == name and start <= t < start + 6) <= 1)

            solver = cp_model.CpSolver()
            if solver.Solve(model) == cp_model.OPTIMAL:
                for i, row in df_today.iterrows():
                    for (p_i, r, name, t) in x:
                        if p_i == i and solver.Value(x[p_i, r, name, t]) == 1:
                            h, m = 8 + (t * 15) // 60, (t * 15) % 60
                            all_results.append({
                                "Ngày Khám/Trị liệu": target_date,
                                "Bác sỹ": row["Bác sĩ"] or "Tự động",
                                "Dịch vụ": row["Dịch vụ"],
                                "Giờ Khám/Trị liệu": f"{h:02d}:{m:02d}",
                                "Khách hàng": row["Họ tên"],
                                "Phòng/Giường": name # Tài nguyên
                            })
            else: st.error(f"⚠️ Không thể tối ưu ngày {target_date}!")
        
        if all_results:
            st.success("Tối ưu hóa thành công!")
            df_res = pd.DataFrame(all_results)
            
            # 1. Chuyển đổi giờ để sắp xếp đúng thứ tự thời gian
            df_res["_sort_time"] = pd.to_datetime(df_res["Giờ Khám/Trị liệu"], format="%H:%M").dt.time
            
            # 2. Sắp xếp theo Ngày, Bác sỹ và Giờ
            df_res = df_res.sort_values(by=["Ngày Khám/Trị liệu", "Bác sỹ", "_sort_time"])
            
            # 3. Định dạng lại thứ tự 5 cột theo yêu cầu
            df_res = df_res[["Ngày Khám/Trị liệu", "Bác sỹ", "Dịch vụ", "Giờ Khám/Trị liệu", "Khách hàng", "Phòng/Giường"]]
            
            st.subheader("📋 Lịch khám chi tiết")
            
            # 4. Hiển thị nhóm mà không cần expander (luôn mở)
            # Dùng groupby để nhóm và hiển thị từng bảng con nối tiếp nhau
            for (date, doctor), group in df_res.groupby(["Ngày Khám/Trị liệu", "Bác sỹ"]):
                st.markdown(f"**📅 Ngày: {date} | 👨‍⚕️ Bác sĩ: {doctor}**")
                # Hiển thị bảng luôn mở, không có nút thu gọn
                st.dataframe(
                    group.drop(columns=["Ngày Khám/Trị liệu", "Bác sỹ"]), 
                    use_container_width=True, 
                    hide_index=True
                )
        else:
            st.error("⚠️ Không tìm thấy phương án tối ưu!")

    if st.button("Xóa toàn bộ danh sách"):
        st.session_state.patients_list = []
        st.rerun()

st.markdown("---")
st.caption("Ứng dụng quản trị vận hành phòng khám - Tối ưu hóa bằng CP-SAT")
