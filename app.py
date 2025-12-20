import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 設定網頁 ---
st.set_page_config(page_title="HR 離職分析", layout="wide")
st.title("🚀 HR 員工離職分析系統")

# --- 讀取資料的雙保險機制 ---
@st.cache_data
def load_data():
    # 這是您檔案的標準名稱 (請確認 GitHub 上也是這個名字)
    # 如果您嫌名字太長，可以把 csv 改名成 data.csv 再上傳，這裡改成 'data.csv' 就好
    file_name = 'HR-Employee-Attrition-完美中文版.xlsx - 工作表 1 - HR-Employee-Attrition-完.csv'
    
    # 狀況 A：老師已經把檔案傳到 GitHub 了 -> 自動讀取
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name, header=1)
            if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)
            return df
        except:
            return None
    return None

# 嘗試自動讀取
df = load_data()

# 狀況 B：找不到檔案 -> 顯示上傳按鈕讓學生自己傳
if df is None:
    st.warning("請上傳 HR 資料檔案 (csv)")
    uploaded_file = st.file_uploader("", type=['csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file, header=1)
        if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)

# --- 如果有資料，就顯示分析畫面 ---
if df is not None:
    st.success(f"✅ 資料載入成功！共 {len(df)} 筆")
    
    # === 簡單的側邊欄篩選 ===
    st.sidebar.header("🔍 篩選條件")
    
    # 部門篩選
    all_depts = list(df['部門'].unique())
    sel_depts = st.sidebar.multiselect("部門", all_depts, default=all_depts)
    
    # 加班篩選
    ot_opt = st.sidebar.radio("是否加班", ["全部", "是", "否"])
    
    # 執行篩選
    mask = df['部門'].isin(sel_depts)
    if ot_opt != "全部":
        mask = mask & (df['加班'] == ot_opt)
        
    filtered_df = df[mask]
    
    # === 顯示結果 (使用 Plotly 不會有亂碼) ===
    col1, col2 = st.columns(2)
    
    # 離職率計算
    rate = (len(filtered_df[filtered_df['離職']=='是']) / len(filtered_df) * 100) if len(filtered_df)>0 else 0
    st.metric("目前篩選群體的離職率", f"{rate:.1f}%")

    with col1:
        st.subheader("部門離職狀況")
        if not filtered_df.empty:
            # 簡單的長條圖
            fig = px.histogram(filtered_df, y="部門", color="離職", 
                             barmode="group", height=400,
                             color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'})
            st.plotly_chart(fig, use_container_width=True)
            
    with col2:
        st.subheader("年齡分佈")
        if not filtered_df.empty and '年齡' in df.columns:
            fig2 = px.histogram(filtered_df, x="年齡", color="離職",
                              height=400,
                              color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'})
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("詳細資料表")
    st.dataframe(filtered_df)

else:
    st.info("👈 請在左側上傳檔案，或等待老師上傳預設資料。")
