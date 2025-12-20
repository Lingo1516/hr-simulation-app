import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. 網頁設定 ---
st.set_page_config(page_title="HR 離職戰情室", layout="wide", initial_sidebar_state="expanded")
st.title("🚀 HR 員工離職分析戰情室")
st.caption("EMBA 課程專用：自動化數據分析平台")

# --- 2. 自動讀取老師上傳的檔案 ---
@st.cache_data
def load_data():
    # 這是您上傳的檔案名稱 (必須跟 GitHub 上的檔名一模一樣，差一個字都不行)
    file_name = 'HR-Employee-Attrition-完美中文版.xlsx - 工作表 1 - HR-Employee-Attrition-完.csv'
    
    # 檢查檔案是否真的存在
    if os.path.exists(file_name):
        try:
            # header=1 跳過第一列標題，從第二列開始讀
            df = pd.read_csv(file_name, header=1)
            # 欄位正名
            if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)
            return df
        except Exception as e:
            st.error(f"檔案讀取失敗，請檢查格式: {e}")
            return None
    else:
        return None

df = load_data()

# --- 3. 介面顯示邏輯 ---

if df is None:
    # 如果這裡亮紅燈，代表 GitHub 上的檔名跟程式裡的檔名不對
    st.error("⚠️ 系統找不到預設檔案！")
    st.warning(f"請老師檢查 GitHub 上是否已有檔案，且名稱是否為：\nHR-Employee-Attrition-完美中文版.xlsx - 工作表 1 - HR-Employee-Attrition-完.csv")
    
    # 緊急備用：讓學生手動傳
    uploaded = st.file_uploader("開啟緊急手動上傳模式", type=['csv'])
    if uploaded:
        df = pd.read_csv(uploaded, header=1)
        if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)

# --- 4. 戰情室主畫面 (資料成功載入後顯示) ---
if df is not None:
    
    # === 左側篩選器 (Sidebar) ===
    st.sidebar.header("🔍 分析篩選器")
    
    # 1. 部門
    all_depts = list(df['部門'].unique())
    sel_depts = st.sidebar.multiselect("選擇部門", all_depts, default=all_depts)
    
    # 2. 加班
    ot_opt = st.sidebar.radio("是否加班", ["全部", "是", "否"], horizontal=True)
    
    # 3. 滿意度
    if '工作滿意度' in df.columns:
        sat_score = st.sidebar.slider("工作滿意度 (1低 - 4高)", 1, 4, (1, 4))

    # === 資料過濾 ===
    mask = df['部門'].isin(sel_depts)
    if ot_opt != "全部":
        mask = mask & (df['加班'] == ot_opt)
    if '工作滿意度' in df.columns:
        mask = mask & df['工作滿意度'].between(sat_score[0], sat_score[1])
        
    filtered_df = df[mask]

    # === 關鍵指標 (KPI) ===
    total = len(filtered_df)
    left_count = len(filtered_df[filtered_df['離職']=='是'])
    rate = (left_count / total * 100) if total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 篩選後人數", f"{total} 人")
    col2.metric("👋 離職人數", f"{left_count} 人")
    col3.metric("⚠️ 離職率", f"{rate:.1f}%")
    
    st.markdown("---")

    # === 互動圖表區 (Plotly - 無亂碼保證) ===
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📊 各部門離職狀況")
        if not filtered_df.empty:
            # 橫向長條圖 (字不會擠在一起)
            fig = px.histogram(filtered_df, y="部門", color="離職", 
                             orientation='h',
                             color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'},
                             title="部門離職分佈 (滑鼠移動可看數據)",
                             text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.subheader("🎂 年齡層分佈")
        if not filtered_df.empty and '年齡' in df.columns:
            fig2 = px.histogram(filtered_df, x="年齡", color="離職",
                              color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'},
                              title="年齡層離職風險",
                              nbins=20)
            st.plotly_chart(fig2, use_container_width=True)

    # === 詳細資料表 ===
    with st.expander("📋 點擊展開：查看詳細員工名單"):
        st.dataframe(filtered_df)
