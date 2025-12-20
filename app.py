import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. 頁面設定 ---
st.set_page_config(page_title="HR 離職戰情室 (互動版)", layout="wide")
st.title("🚀 HR 員工離職分析戰情室 (互動圖表版)")
st.caption("使用 Plotly 技術：解決中文字型問題，並支援滑鼠互動查看數據")
st.markdown("---")

# --- 2. 讀取資料 ---
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

# --- 3. 側邊欄篩選 (維持原有的強大功能) ---
if df is not None:
    st.sidebar.title("🔍 篩選面板")
    mask = pd.Series([True] * len(df))
    
    # 1. 組織
    with st.sidebar.expander("🏢 1. 部門與職位", expanded=True):
        all_depts = list(df['部門'].unique())
        sel_depts = st.multiselect("部門", all_depts, default=all_depts)
        mask = mask & df['部門'].isin(sel_depts)
        
        if '職位角色' in df.columns:
            all_roles = sorted(list(df['職位角色'].unique()))
            sel_roles = st.multiselect("職位角色", all_roles, default=all_roles)
            mask = mask & df['職位角色'].isin(sel_roles)

    # 2. 工作負擔
    with st.sidebar.expander("🔥 2. 工作負擔"):
        ot_opt = st.radio("是否加班", ["全部", "是", "否"], horizontal=True)
        if ot_opt != "全部": mask = mask & (df['加班'] == ot_opt)
        
        if '出差頻率' in df.columns:
            all_travel = list(df['出差頻率'].unique())
            sel_travel = st.multiselect("出差頻率", all_travel, default=all_travel)
            mask = mask & df['出差頻率'].isin(sel_travel)

    # 3. 滿意度
    with st.sidebar.expander("❤️ 3. 滿意度 (1-4)"):
        if '工作滿意度' in df.columns:
            js = st.slider("工作滿意度", 1, 4, (1, 4))
            mask = mask & df['工作滿意度'].between(js[0], js[1])

    # 4. 薪資
    with st.sidebar.expander("💰 4. 薪資範圍"):
        if '月薪' in df.columns:
            min_pay, max_pay = int(df['月薪'].min()), int(df['月薪'].max())
            pay = st.slider("月薪", min_pay, max_pay, (min_pay, max_pay))
            mask = mask & df['月薪'].between(pay[0], pay[1])

    # 5. 年齡與背景
    with st.sidebar.expander("👤 5. 個人背景"):
        if '年齡' in df.columns:
            age = st.slider("年齡", 18, 60, (18, 60))
            mask = mask & df['年齡'].between(age[0], age[1])
        if '性別' in df.columns:
            g_opt = st.radio("性別", ["全部", "男性", "女性"], horizontal=True)
            if g_opt != "全部": mask = mask & (df['性別'] == g_opt)

    # 套用篩選
    filtered_df = df[mask]
    
    # --- 4. 儀表板與互動圖表 ---
    
    # KPI 區塊
    total = len(filtered_df)
    left_count = len(filtered_df[filtered_df['離職'] == '是'])
    rate = (left_count / total * 100) if total > 0 else 0
    avg_salary = filtered_df['月薪'].mean() if '月薪' in df.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 總人數", f"{total}")
    col2.metric("👋 離職人數", f"{left_count}")
    col3.metric("⚠️ 離職率", f"{rate:.1f}%")
    col4.metric("💰 平均月薪", f"${avg_salary:,.0f}")
    
    st.markdown("---")

    # 圖表區 (改用 Plotly)
    c1, c2 = st.columns(2)
    
    with c1:
        st.info("🏢 部門離職分佈")
        if total > 0:
            # 資料聚合
            dept_data = filtered_df.groupby(['部門', '離職']).size().reset_index(name='人數')
            # 繪製堆疊長條圖
            fig1 = px.bar(dept_data, x='人數', y='部門', color='離職', 
                          orientation='h', # 橫向顯示
                          title="各部門離職狀況 (滑鼠懸停可看數字)",
                          color_discrete_map={'是': '#FF6B6B', '否': '#4ECDC4'},
                          text='人數')
            st.plotly_chart(fig1, use_container_width=True)
            
    with c2:
        st.info("🎂 年齡分佈")
        if total > 0 and '年齡' in df.columns:
            fig2 = px.histogram(filtered_df, x="年齡", color="離職", 
                                title="年齡層分佈",
                                nbins=15,
                                color_discrete_map={'是': '#FF6B6B', '否': '#4ECDC4'},
                                barmode='overlay', opacity=0.7)
            st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    
    with c3:
        st.info("💰 薪資分佈 (箱型圖)")
        if total > 0 and '月薪' in df.columns:
            fig3 = px.box(filtered_df, x="離職", y="月薪", color="離職",
                          title="離職 vs 在職 薪資比較",
                          color_discrete_map={'是': '#FF6B6B', '否': '#4ECDC4'})
            st.plotly_chart(fig3, use_container_width=True)
            
    with c4:
        st.info("⏳ 在公司年資")
        if total > 0 and '在公司年資' in df.columns:
            fig4 = px.histogram(filtered_df, x="在公司年資", color="離職",
                                title="在公司年資分佈",
                                color_discrete_map={'是': '#FF6B6B', '否': '#4ECDC4'})
            st.plotly_chart(fig4, use_container_width=True)

    # 詳細資料
    st.subheader("📋 詳細資料表")
    st.dataframe(filtered_df)

else:
    st.stop()
