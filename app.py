import streamlit as st
import pandas as pd
import re
from datetime import datetime
from ortools.sat.python import cp_model

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Phòng khám Hàng Bông - Vận hành", layout="wide")

if 'patients_list' not in st.session_state:
    st.session_state.patients_list = []

# --- HÀM HỖ TRỢ ---
def analyze_bottlenecks(df, doctor_list, durations):
    reasons = []
    # 1. Kiểm tra tải chuyên môn
    specialized_patients = df[df["Dịch vụ"].isin(["Điều trị theo vùng", "Điều trị chuyên sâu"])]
    if len(specialized_patients) > 3 * 34: # 3 bác sĩ chuyên môn * 34 block
        reasons.append("- Số ca Điều trị chuyên sâu/vùng quá lớn so với số lượng Bác sĩ có chuyên môn (chỉ có 3 BS đảm nhận).")
    
    # 2. Kiểm tra tổng tải
    total_req = sum(durations.get(s, 3) for s in df["Dịch vụ"])
    if total_req > len(doctor_list) * 34:
        reasons.append(f"- Tổng thời gian yêu cầu ({total_req} block) vượt quá năng lực làm việc tối đa ({len(doctor_list)*34} block).")
        
    return reasons

# --- GIAO DIỆN CHÍNH ---
st.title("🏥 Hệ thống Tối ưu hóa - Phòng khám Hàng Bông")

tab1, tab2, tab3 = st.tabs(["📋 Đặt lịch", "📅 Danh sách chờ", "🚀 Chạy Tối ưu hóa"])

with tab1:
    with st.form("booking_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Họ tên *")
        service_type = c2.selectbox("Dịch vụ *", ["Khám mới", "Tái khám", "Điều trị theo vùng", "Điều trị chuyên sâu"])
        doctor_select = st.selectbox("Bác sĩ (Để trống nếu tự tối ưu)", [None] + ["TS Đặng Hữu Phúc", "Th.S Nguyễn Thảo Dương", "BS Đỗ Phi Hưng", "BS Nguyễn Thu Hương", "BS Thương yêu", "Th.s Vương Ngọc Toàn", "BS Quan Thị Giao Linh", "BS Nguyễn Nhật Anh"])
        exam_date = st.date_input("Ngày Khám *", min_value=datetime.today())
        
        if st.form_submit_button("Lưu đặt lịch"):
            st.session_state.patients_list.append({
                "Họ tên": full_name, "Dịch vụ": service_type, "Bác sĩ": doctor_select, "Ngày Khám/Trị liệu": str(exam_date)
            })
            st.success("Đã thêm!")

with tab2:
    uploaded = st.file_uploader("Upload file khách hàng", type=['xlsx', 'csv'])
    if uploaded:
        df = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
        st.session_state.patients_list = df.to_dict('records')
    if st.session_state.patients_list:
        st.dataframe(pd.DataFrame(st.session_state.patients_list), use_container_width=True)

with tab3:
    target_date = st.date_input("Chọn ngày chạy:", min_value=datetime.today())
    if st.button("Chạy Tối ưu hóa"):
        df_today = pd.DataFrame(st.session_state.patients_list)
        df_today["Ngày Khám/Trị liệu"] = pd.to_datetime(df_today["Ngày Khám/Trị liệu"]).dt.date
        df_today = df_today[df_today["Ngày Khám/Trị liệu"] == target_date]
        
        if df_today.empty: st.warning("Danh sách trống!"); st.stop()
        
        doctor_list = ["TS Đặng Hữu Phúc", "Th.S Nguyễn Thảo Dương", "BS Đỗ Phi Hưng", "BS Nguyễn Thu Hương", "BS Thương yêu", "Th.s Vương Ngọc Toàn", "BS Quan Thị Giao Linh", "BS Nguyễn Nhật Anh"]
        durations = {"Khám mới": 3, "Tái khám": 3, "Điều trị theo vùng": 5, "Điều trị chuyên sâu": 8}
        
        model = cp_model.CpModel()
        x, horizon = {}, 34
        
        for i, row in df_today.iterrows():
            d_dur = durations.get(row["Dịch vụ"], 3)
            # Ràng buộc bác sĩ
            valid_docs = [doctor_list.index(row["Bác sĩ"])] if pd.notna(row["Bác sĩ"]) and row["Bác sĩ"] in doctor_list else range(len(doctor_list))
            if row["Dịch vụ"] in ["Điều trị theo vùng", "Điều trị chuyên sâu"]:
                valid_docs = [d for d in valid_docs if d <= 2]
            
            for d in valid_docs:
                for t in range(horizon - d_dur + 1):
                    x[i, d, t] = model.NewBoolVar(f'x_p{i}_d{d}_t{t}')
        
        for i in range(len(df_today)): model.Add(sum(x[i, d, t] for (p, d, t) in x if p == i) == 1)
        for d in range(len(doctor_list)):
            for t in range(horizon):
                model.Add(sum(x[i, doc, start] for (i, doc, start) in x if doc == d and start <= t < start + durations.get(df_today.iloc[i]["Dịch vụ"], 3)) <= 1)

        solver = cp_model.CpSolver()
        if solver.Solve(model) == cp_model.OPTIMAL:
            st.success("Tối ưu hóa hoàn thành!")
            # [Hiển thị kết quả...]
        else:
            st.error("⚠️ Không tìm thấy phương án tối ưu!")
            reasons = analyze_bottlenecks(df_today, doctor_list, durations)
            st.write("Nguyên nhân có thể bao gồm:")
            for reason in reasons: st.write(reason)
            st.info("💡 Lời khuyên: Hãy kiểm tra lại lịch làm việc hoặc chia bớt bệnh nhân sang ngày khác.")

    if st.button("Xóa danh sách"):
        st.session_state.patients_list = []
        st.rerun()

st.markdown("---")
st.caption("Ứng dụng quản trị phòng khám - CP-SAT Solver")
