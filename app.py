import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="HR 離職分析戰情室", layout="wide")
st.title("🚀 HR 員工離職分析戰情室")
st.caption("EMBA 課程專用：自動化數據分析平台")

# --- 2. 自動讀取資料 (核心功能) ---
@st.cache_data
def load_data():
    # 這是您上傳到 GitHub 的檔案名稱，必須一模一樣
    file_name = 'HR-Employee-Attrition-完美中文版.xlsx - 工作表 1 - HR-Employee-Attrition-完.csv'
    
    # 檢查：如果老師有把檔案傳到 GitHub，就直接讀取
    if os.path.exists(file_name):
        try:
            # header=1 跳過標題列
            df = pd.read_csv(file_name, header=1)
            # 把欄位名稱統一
            if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)
            return df
        except:
            return None
    return None

df = load_data()

# --- 3. 判斷顯示畫面 ---

# 情況 A：資料還沒抓到 (老師可能忘了上傳，或是檔名不對)
if df is None:
    st.error("⚠️ 系統尚未偵測到預設資料")
    st.info("💡 請老師確認：CSV 檔案是否有上傳到 GitHub？檔名是否正確？")
    
    # 還是留一個手動上傳按鈕當作備用
    uploaded_file = st.file_uploader("或是請同學手動上傳 CSV 檔", type=['csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file, header=1)
        if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)

# 情況 B：資料抓到了 (最完美的狀態！)
if df is not None:
    # 側邊欄會在這裡出現
    st.sidebar.title("🔍 分析篩選器")
    st.sidebar.success("已自動連線資料庫")
    
    # === 左側：篩選條件 (這裡就是您說的左側) ===
    
    # 1. 部門篩選
    all_depts = list(df['部門'].unique())
    sel_depts = st.sidebar.multiselect("選擇部門", all_depts, default=all_depts)
    
    # 2. 加班篩選
    ot_opt = st.sidebar.radio("是否加班?", ["全部", "是", "否"])
    
    # 3. 滿意度篩選 (1-4分)
    if '工作滿意度' in df.columns:
        score = st.sidebar.slider("工作滿意度", 1, 4, (1, 4))
    
    # === 中間：執行篩選邏輯 ===
    mask = df['部門'].isin(sel_depts)
    if ot_opt != "全部":
        mask = mask & (df['加班'] == ot_opt)
    if '工作滿意度' in df.columns:
        mask = mask & df['工作滿意度'].between(score[0], score[1])
        
    filtered_df = df[mask]
    
    # === 右側/中間：顯示漂亮的互動圖表 ===
    
    # 顯示關鍵數字
    total = len(filtered_df)
    left = len(filtered_df[filtered_df['離職']=='是'])
    rate = (left/total*100) if total>0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 篩選人數", f"{total}")
    col2.metric("👋 離職人數", f"{left}")
    col3.metric("⚠️ 離職率", f"{rate:.1f}%")
    
    st.markdown("---")
    
    # 圖表區 (使用 Plotly，解決亂碼問題)
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📊 部門離職狀況")
        if not filtered_df.empty:
            # 互動長條圖
            fig = px.histogram(filtered_df, y="部門", color="離職", 
                             barmode="group", orientation='h',
                             color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'},
                             title="各部門離職人數 (滑鼠移上去看數字)")
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.subheader("🎂 年齡分佈")
        if not filtered_df.empty and '年齡' in df.columns:
            fig2 = px.histogram(filtered_df, x="年齡", color="離職",
                              color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'},
                              title="哪個年紀最容易走？")
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 詳細資料表")
    st.dataframe(filtered_df)
