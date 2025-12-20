import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import os

# --- 1. 自動下載並設定中文字型 (解決亂碼關鍵) ---
def set_chinese_font_auto():
    # 字型檔案名稱
    font_name = "NotoSansTC-Regular.ttf"
    # 如果檔案不存在，從 Google Fonts 下載
    if not os.path.exists(font_name):
        import urllib.request
        url = "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC-Regular.ttf"
        try:
            with st.spinner("正在下載中文字型，請稍候..."):
                urllib.request.urlretrieve(url, font_name)
        except:
            st.error("字型下載失敗，圖表可能無法顯示中文")
            return

    # 加入字型
    fm.fontManager.addfont(font_name)
    plt.rcParams['font.family'] = 'Noto Sans TC'
    plt.rcParams['axes.unicode_minus'] = False # 解決負號顯示問題

# 執行字型設定
set_chinese_font_auto()

# --- 2. 頁面設定 ---
st.set_page_config(page_title="HR 深度離職分析 Pro", layout="wide")
st.title("🚀 HR 員工離職分析戰情室 (字型修復版)")
st.markdown("---")

# --- 3. 讀取資料 ---
@st.cache_data
def load_data():
    file_name = 'HR-Employee-Attrition-完美中文版.xlsx - 工作表 1 - HR-Employee-Attrition-完.csv'
    if not os.path.exists(file_name):
        return None
    try:
        df = pd.read_csv(file_name, header=1)
        if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)
        return df
    except:
        return None

df = load_data()

# 處理無檔案情況
if df is None:
    st.warning("⚠️ 找不到預設檔案，請上傳 CSV")
    uploaded_file = st.file_uploader("上傳檔案", type=['csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file, header=1)
        if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)

# --- 4. 完整篩選功能 ---
if df is not None:
    st.sidebar.title("🔍 篩選條件")
    
    # 建立遮罩
    mask = pd.Series([True] * len(df))
    
    # === 組織結構 ===
    with st.sidebar.expander("🏢 1. 部門與職位", expanded=True):
        all_depts = list(df['部門'].unique())
        sel_depts = st.multiselect("部門", all_depts, default=all_depts)
        mask = mask & df['部門'].isin(sel_depts)
        
        if '職位角色' in df.columns:
            all_roles = sorted(list(df['職位角色'].unique()))
            sel_roles = st.multiselect("職位角色", all_roles, default=all_roles)
            mask = mask & df['職位角色'].isin(sel_roles)

    # === 工作負擔 ===
    with st.sidebar.expander("🔥 2. 加班與出差"):
        ot_opt = st.radio("是否加班", ["全部", "是", "否"], horizontal=True)
        if ot_opt != "全部": mask = mask & (df['加班'] == ot_opt)
        
        if '出差頻率' in df.columns:
            all_travel = list(df['出差頻率'].unique())
            sel_travel = st.multiselect("出差頻率", all_travel, default=all_travel)
            mask = mask & df['出差頻率'].isin(sel_travel)

    # === 薪資 ===
    with st.sidebar.expander("💰 3. 薪資範圍"):
        if '月薪' in df.columns:
            min_pay, max_pay = int(df['月薪'].min()), int(df['月薪'].max())
            pay_range = st.slider("月薪", min_pay, max_pay, (min_pay, max_pay))
            mask = mask & df['月薪'].between(pay_range[0], pay_range[1])

    # === 年齡 ===
    with st.sidebar.expander("👤 4. 年齡層"):
         if '年齡' in df.columns:
            age_range = st.slider("年齡", 18, 60, (18, 60))
            mask = mask & df['年齡'].between(age_range[0], age_range[1])

    # 套用篩選
    filtered_df = df[mask]
    
    # --- 5. 儀表板與圖表 (針對顯示優化) ---
    
    # KPI
    total = len(filtered_df)
    left_count = len(filtered_df[filtered_df['離職'] == '是'])
    rate = (left_count / total * 100) if total > 0 else 0
    avg_salary = filtered_df['月薪'].mean() if '月薪' in df.columns else 0
    
    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👥 人數", f"{total}")
        c2.metric("👋 離職數", f"{left_count}")
        c3.metric("⚠️ 離職率", f"{rate:.1f}%")
        c4.metric("💰 平均月薪", f"${avg_salary:,.0f}")
    
    st.markdown("---")

    # 圖表區
    chart1, chart2 = st.columns(2)
    
    # 圖表 1：部門離職率 (橫向長條圖，字比較不會擠在一起)
    with chart1:
        st.subheader("🏢 部門離職分佈")
        if total > 0:
            fig, ax = plt.subplots(figsize=(6, 5)) # 調整圖表大小
            sns.countplot(y='部門', hue='離職', data=filtered_df, ax=ax, palette='Set2')
            plt.title("各部門離職人數", fontsize=14)
            plt.xlabel("人數")
            plt.ylabel("部門")
            plt.tight_layout() # 自動調整間距，防止字被切掉
            st.pyplot(fig)
        else:
            st.info("無資料")

    # 圖表 2：年齡分佈 (文字旋轉)
    with chart2:
        st.subheader("🎂 年齡與離職關係")
        if total > 0 and '年齡' in df.columns:
            fig, ax = plt.subplots(figsize=(6, 5))
            # 將年齡分組以便閱讀
            filtered_df['年齡組'] = pd.cut(filtered_df['年齡'], bins=[0,25,35,45,60], labels=['25歲下','26-35','36-45','46歲上'])
            sns.countplot(x='年齡組', hue='離職', data=filtered_df, ax=ax, palette='Pastel1')
            plt.title("各年齡層離職狀況", fontsize=14)
            plt.xticks(rotation=0) # 設定文字角度
            plt.tight_layout()
            st.pyplot(fig)

    # 圖表 3 & 4
    chart3, chart4 = st.columns(2)
    
    with chart3:
        st.subheader("💰 薪資分佈 (箱型圖)")
        if total > 0 and '月薪' in df.columns:
            fig, ax = plt.subplots(figsize=(6, 5))
            sns.boxplot(x='離職', y='月薪', data=filtered_df, ax=ax, palette='Set3')
            plt.title("離職與在職薪資比較", fontsize=14)
            plt.tight_layout()
            st.pyplot(fig)
            
    with chart4:
        st.subheader("⏳ 年資分佈")
        if total > 0 and '在公司年資' in df.columns:
            fig, ax = plt.subplots(figsize=(6, 5))
            sns.histplot(data=filtered_df, x='在公司年資', hue='離職', multiple="stack", bins=10, ax=ax)
            plt.title("在公司年資分佈", fontsize=14)
            plt.tight_layout()
            st.pyplot(fig)

    st.markdown("---")
    st.subheader(f"📋 詳細資料表 ({total} 筆)")
    st.dataframe(filtered_df)
