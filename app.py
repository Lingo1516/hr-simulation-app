import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import os

# --- 1. 設定中文字型 (嘗試解決雲端中文亂碼問題) ---
def set_chinese_font():
    system_name = platform.system()
    if system_name == "Windows":
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
    elif system_name == "Darwin": 
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    else:
        # Linux/Streamlit Cloud 預設通常沒有中文字型，這行是嘗試
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans'] 
    plt.rcParams['axes.unicode_minus'] = False

set_chinese_font()

# --- 2. 網頁標題 ---
st.title("🚀 HR 員工離職分析系統")
st.markdown("針對 **HR-Employee-Attrition** 資料集的互動分析報告")

# --- 3. 讀取資料 ---
@st.cache_data # 加速讀取
def load_data():
    # 嘗試讀取您上傳的特定檔案名稱
    file_name = 'HR-Employee-Attrition-完美中文版.xlsx - 工作表 1 - HR-Employee-Attrition-完.csv'
    
    # 如果找不到預設檔案，允許使用者上傳
    if not os.path.exists(file_name):
        return None
        
    try:
        # header=1 跳過第一行標題，直接讀欄位
        df = pd.read_csv(file_name, header=1)
        if '流失' in df.columns:
            df.rename(columns={'流失': '離職'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"讀取錯誤: {e}")
        return None

df = load_data()

# 如果找不到檔案，顯示上傳按鈕
if df is None:
    st.warning("⚠️ 找不到預設檔案，請上傳 CSV 檔")
    uploaded_file = st.file_uploader("請上傳您的 HR 資料 csv", type=['csv'])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, header=1)
            if '流失' in df.columns:
                df.rename(columns={'流失': '離職'}, inplace=True)
        except:
            # 嘗試不跳過 header
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            if '流失' in df.columns:
                df.rename(columns={'流失': '離職'}, inplace=True)
else:
    st.success(f"已成功載入資料：{len(df)} 筆")

# --- 4. 分析主介面 (如果資料已載入) ---
if df is not None:
    
    # 側邊欄：篩選條件
    st.sidebar.header("🔍 篩選條件")
    
    dept_list = ['全部'] + list(df['部門'].unique())
    selected_dept = st.sidebar.selectbox("選擇部門", dept_list)
    
    ot_list = ['全部', '是', '否']
    selected_ot = st.sidebar.selectbox("是否加班", ot_list)
    
    # 執行篩選
    filtered_df = df.copy()
    if selected_dept != '全部':
        filtered_df = filtered_df[filtered_df['部門'] == selected_dept]
    if selected_ot != '全部':
        filtered_df = filtered_df[filtered_df['加班'] == selected_ot]
        
    # 計算指標
    total = len(filtered_df)
    left_count = len(filtered_df[filtered_df['離職'] == '是'])
    rate = (left_count / total * 100) if total > 0 else 0
    
    # 顯示關鍵指標 (KPI)
    col1, col2, col3 = st.columns(3)
    col1.metric("篩選後總人數", f"{total} 人")
    col2.metric("離職人數", f"{left_count} 人")
    col3.metric("離職率", f"{rate:.1f}%")
    
    st.markdown("---")
    
    # 分頁顯示不同圖表
    tab1, tab2, tab3 = st.tabs(["📊 加班分析", "🎂 年齡分析", "💰 薪資分佈"])
    
    with tab1:
        st.subheader("加班與離職的關係")
        if '加班' in df.columns:
            # 簡單長條圖
            fig, ax = plt.subplots()
            sns.countplot(x='加班', hue='離職', data=filtered_df, ax=ax, palette='Set2')
            st.pyplot(fig)
            st.caption("觀察重點：有加班的人(是)，橘色條(離職)的比例是否明顯較高？")
            
    with tab2:
        st.subheader("不同年齡層的離職狀況")
        if '年齡' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.histplot(data=filtered_df, x='年齡', hue='離職', multiple="stack", kde=True, ax=ax)
            st.pyplot(fig)
            st.caption("觀察重點：曲線高峰在哪裡？年輕人的離職比例是否較高？")
            
    with tab3:
        st.subheader("薪資與離職關係 (箱型圖)")
        if '月薪' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.boxplot(x='離職', y='月薪', data=filtered_df, ax=ax, palette='Pastel1')
            st.pyplot(fig)
            st.caption("觀察重點：離職群體的平均薪資線(箱子中間的線)是否比在職者低？")

    # 顯示原始資料
    with st.expander("點擊查看詳細資料表"):
        st.dataframe(filtered_df)
