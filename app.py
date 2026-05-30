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
        doctor_select = c6.selectbox("Bác sĩ *", doctor_list)
        
        c7, c8 = st.columns(2)
        exam_date = c7.date_input("Ngày Khám/Trị liệu *", min_value=datetime.today())
        
        time_options = []
        curr = datetime.combine(datetime.today(), time(8, 0))
        end_morning = datetime.combine(datetime.today(), time(12, 0))
        while curr <= end_morning:
            time_options.append(curr.time()); curr += timedelta(minutes=15)
        curr = datetime.combine(datetime.today(), time(13, 30))
        end_evening = datetime.combine(datetime.today(), time(18, 0))
        while curr <= end_evening:
            time_options.append(curr.time()); curr += timedelta(minutes=15)
            
        appointment_time = c8.select_slider("Giờ Khám/Trị liệu *", options=time_options, format_func=lambda x: x.strftime('%H:%M'))
        
        reason = st.text_area("Lý do")
        submit_button = st.form_submit_button("Lưu đặt lịch")
        
        if submit_button:
            if not full_name or not phone:
                st.error("Vui lòng điền đầy đủ các trường bắt buộc (*)")
            elif not is_valid_phone(phone):
                st.error("Số điện thoại không hợp lệ!")
            else:
                new_patient = {
                    "Họ tên": full_name, "Giới tính": gender, "Ngày sinh": str(dob), 
                    "Số điện thoại": phone, "Dịch vụ": service_type, "Bác sĩ": doctor_select, 
                    "Ngày Khám/Trị liệu": str(exam_date), "Giờ Khám/Trị liệu": str(appointment_time), "Lý do": reason
                }
                st.session_state.patients_list.append(new_patient)
                st.success(f"Đã thêm khách hàng {full_name} thành công!")

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
        df_patients["Số điện thoại"] = df_patients["Số điện thoại"].astype(str).str.replace(r'\.0$', '', regex=True)
        df_patients["Số điện thoại"] = df_patients["Số điện thoại"].apply(lambda x: x.zfill(10) if len(x) < 10 else x)
        df_patients["TT"] = range(1, len(df_patients) + 1)
        display_cols = ["TT", "Họ tên", "Giới tính", "Ngày sinh", "Số điện thoại", "Dịch vụ", "Bác sĩ", "Ngày Khám/Trị liệu", "Giờ Khám/Trị liệu", "Lý do"]
        available_cols = [c for c in display_cols if c in df_patients.columns]
        st.dataframe(df_patients[available_cols], use_container_width=True, hide_index=True)

with tab3:
    st.header("🚀 Chạy Tối ưu hóa")
    target_date = st.date_input("Chọn ngày tối ưu hóa:", min_value=datetime.today())
    if st.button("Chạy Thuật toán Phân công (CP-SAT)"):
        df_today = pd.DataFrame(st.session_state.patients_list)
        if df_today.empty:
            st.warning("Danh sách trống!")
        else:
            model = cp_model.CpModel()
            horizon = 34
            duration_map = {"Khám mới": 3, "Tái khám": 3, "Điều trị theo vùng": 5, "Điều trị chuyên sâu": 8}
            intervals = []
            for idx, row in df_today.iterrows():
                dur = duration_map.get(row["Dịch vụ"], 3)
                start = model.NewIntVar(0, horizon - dur, f"s{idx}")
                end = model.NewIntVar(0, horizon, f"e{idx}")
                interval = model.NewIntervalVar(start, dur, end, f"i{idx}")
                intervals.append({"id": idx, "start": start, "interval": interval, "service": row["Dịch vụ"], "doctor": row["Bác sĩ"]})

            doctor_groups = {}
            for item in intervals:
                doc = item["doctor"]
                if doc not in doctor_groups: doctor_groups[doc] = []
                doctor_groups[doc].append(item["interval"])
            for doc_ints in doctor_groups.values(): model.AddNoOverlap(doc_ints)

            model.AddCumulative([i["interval"] for i in intervals if i["service"] in ["Khám mới", "Tái khám"]], [1]*len(intervals), 3)
            
            solver = cp_model.CpSolver()
            if solver.Solve(model) == cp_model.OPTIMAL:
                st.success("Tối ưu hóa thành công!")
                results = []
                for item in intervals:
                    start_time = solver.Value(item["start"])
                    h = 8 + (start_time * 15) // 60
                    m = (start_time * 15) % 60
                    results.append({"Họ tên": df_today.loc[item["id"], "Họ tên"], "Giờ bắt đầu": f"{h:02d}:{m:02d}", "Bác sĩ": item["doctor"]})
                st.dataframe(pd.DataFrame(results))
            else:
                st.error("⚠️ Không tìm thấy phương án tối ưu!")
                
                # CHẨN ĐOÁN NGUYÊN NHÂN
                total_duration = sum([duration_map.get(row["Dịch vụ"], 3) for _, row in df_today.iterrows()])
                total_capacity = 34 * (3 + 14) # 3 phòng + 14 giường * 34 block
                
                st.write("---")
                st.subheader("🔍 Phân tích nguyên nhân:")
                
                # 1. Kiểm tra quá tải tổng thể
                if total_duration > total_capacity:
                    st.error(f"❌ **Quá tải tài nguyên:** Tổng thời gian yêu cầu của {len(df_today)} bệnh nhân ({total_duration} block) vượt quá năng lực phục vụ của phòng khám ({total_capacity} block).")
                
                # 2. Kiểm tra xung đột bác sĩ cụ thể
                st.write("- **Kiểm tra theo bác sĩ:**")
                load_by_doc = df_today.groupby("Bác sĩ")["Dịch vụ"].count()
                st.write(load_by_doc)
                
                st.info("Gợi ý: Hãy thử tăng số lượng bác sĩ, tăng thời gian làm việc hoặc giảm số lượng bệnh nhân trong ngày.")
                
                # Cung cấp file log chi tiết (nếu cần)
                if st.checkbox("Xem chi tiết lỗi từ Solver"):
                    st.text(solver.ResponseStats())

    if st.button("Xóa toàn bộ danh sách"):
        st.session_state.patients_list = []
        st.rerun()

st.markdown("---")
st.caption("Ứng dụng quản trị vận hành phòng khám - Tối ưu hóa bằng CP-SAT")
