import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. 網頁設定 ---
st.set_page_config(page_title="HR 離職戰情室", layout="wide")
st.title("🚀 HR 員工離職分析戰情室")

# --- 2. 智慧型讀檔 (會自動試 3 種檔名) ---
@st.cache_data
def load_data():
    # 這是我們要嘗試的檔名清單
    possible_filenames = [
        'HR-Employee-Attrition-完美中文版.csv',  # 1. 短檔名
        'HR-Employee-Attrition-完美中文版.xlsx - 工作表 1 - HR-Employee-Attrition-完.csv', # 2. 長檔名
        'data.csv' # 3. 備用名
    ]
    
    # 開始一個一個找
    for f in possible_filenames:
        if os.path.exists(f):
            try:
                # 找到了！嘗試讀取
                df = pd.read_csv(f)
                # 修正欄位名稱
                if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)
                return df, f # 回傳資料跟檔名
            except:
                continue # 讀失敗就換下一個
                
    return None, None

df, found_filename = load_data()

# --- 3. 顯示結果 ---
if df is not None:
    # 成功畫面
    st.success(f"✅ 成功連線！系統自動找到了檔案：{found_filename}")
    st.info("同學請直接往下滑動，開始分析數據 👇")
    
    # 這裡加入容錯機制
    if '部門' in df.columns:
        all_depts = list(df['部門'].unique())
        sel_depts = st.sidebar.multiselect("部門篩選", all_depts, default=all_depts)
        mask = df['部門'].isin(sel_depts)
        filtered_df = df[mask]
    else:
        filtered_df = df

    # 關鍵數據
    col1, col2 = st.columns(2)
    col1.metric("總人數", len(filtered_df))
    
    if '離職' in filtered_df.columns:
        left = len(filtered_df[filtered_df['離職']=='是'])
        col2.metric("離職人數", left)
        
        # 畫圖
        st.subheader("📊 部門離職分析")
        fig = px.histogram(filtered_df, y="部門", color="離職", orientation='h',
                           color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'})
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(filtered_df)

else:
    # 失敗畫面 (真的都找不到)
    st.error("❌ 還是找不到檔案！")
    st.warning("請老師看一下您的 GitHub 檔案列表，檔名到底是下面哪一個？")
    st.code("1. HR-Employee-Attrition-完美中文版.csv\n2. HR-Employee-Attrition-完美中文版.xlsx - 工作表 1 - HR-Employee-Attrition-完.csv", language="text")
    
    # 最後備案：讓學生自己傳
    st.markdown("---")
    st.subheader("👇 沒關係，請手動上傳檔案：")
    uploaded = st.file_uploader("", type=['csv'])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.write("預覽資料：", df.head())
