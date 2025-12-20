import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. 網頁設定 ---
st.set_page_config(page_title="HR 離職戰情室 (完整版)", layout="wide")
st.title("🚀 HR 員工離職分析戰情室 (完整互動版)")
st.markdown("---")

# --- 2. 自動讀取 (鎖定您的簡短檔名) ---
@st.cache_data
def load_data():
    # 這是您確認過的檔名
    file_name = 'HR-Employee-Attrition-完美中文版.csv'
    
    if os.path.exists(file_name):
        try:
            # header=1 是因為您的檔案第一列是標題，第二列才是欄位
            df = pd.read_csv(file_name, header=1)
            # 欄位正名
            if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)
            return df
        except Exception as e:
            st.error(f"❌ 讀取失敗：{e}")
            return None
    else:
        st.error(f"❌ 找不到檔案：{file_name}")
        st.warning("請老師確認 GitHub 上的檔名是否完全一致？")
        # 備用上傳按鈕
        return None

df = load_data()

# 如果自動讀取失敗，開啟手動上傳
if df is None:
    uploaded = st.file_uploader("開啟手動上傳救援模式", type=['csv'])
    if uploaded:
        df = pd.read_csv(uploaded, header=1)
        if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)

# --- 3. 超級側邊欄 (全部加回來了！) ---
if df is not None:
    st.sidebar.title("🔍 深度篩選面板")
    st.sidebar.info("已啟用全功能篩選模式")
    
    # 初始化篩選
    mask = pd.Series([True] * len(df))
    
    # === 第一組：組織結構 ===
    with st.sidebar.expander("🏢 1. 部門與職位", expanded=True):
        if '部門' in df.columns:
            all_depts = list(df['部門'].unique())
            sel_depts = st.multiselect("部門", all_depts, default=all_depts)
            mask = mask & df['部門'].isin(sel_depts)
        
        if '職位角色' in df.columns:
            all_roles = sorted(list(df['職位角色'].unique()))
            sel_roles = st.multiselect("職位角色", all_roles, default=all_roles)
            mask = mask & df['職位角色'].isin(sel_roles)

    # === 第二組：工作負擔 ===
    with st.sidebar.expander("🔥 2. 工作負擔與通勤"):
        if '加班' in df.columns:
            ot_opt = st.radio("是否加班", ["全部", "是", "否"], horizontal=True)
            if ot_opt != "全部": mask = mask & (df['加班'] == ot_opt)
        
        if '出差頻率' in df.columns:
            all_travel = list(df['出差頻率'].unique())
            sel_travel = st.multiselect("出差頻率", all_travel, default=all_travel)
            mask = mask & df['出差頻率'].isin(sel_travel)

    # === 第三組：滿意度指標 ===
    with st.sidebar.expander("❤️ 3. 員工滿意度 (1低-4高)"):
        if '工作滿意度' in df.columns:
            js_range = st.slider("工作滿意度", 1, 4, (1, 4))
            mask = mask & df['工作滿意度'].between(js_range[0], js_range[1])
        
        if '環境滿意度' in df.columns:
            es_range = st.slider("環境滿意度", 1, 4, (1, 4))
            mask = mask & df['環境滿意度'].between(es_range[0], es_range[1])

    # === 第四組：薪資福利 ===
    with st.sidebar.expander("💰 4. 薪資範圍"):
        if '月薪' in df.columns:
            min_pay, max_pay = int(df['月薪'].min()), int(df['月薪'].max())
            pay_range = st.slider("月薪範圍", min_pay, max_pay, (min_pay, max_pay))
            mask = mask & df['月薪'].between(pay_range[0], pay_range[1])

    # === 第五組：年資與升遷 ===
    with st.sidebar.expander("⏳ 5. 年資與升遷"):
        if '在公司年資' in df.columns:
            y_comp_range = st.slider("在公司年資 (年)", 0, 40, (0, 40))
            mask = mask & df['在公司年資'].between(y_comp_range[0], y_comp_range[1])
            
        if '上次升遷年資' in df.columns:
            promo_range = st.slider("幾年沒升遷了", 0, 15, (0, 15))
            mask = mask & df['上次升遷年資'].between(promo_range[0], promo_range[1])

    # === 第六組：個人背景 ===
    with st.sidebar.expander("👤 6. 個人背景"):
        if '性別' in df.columns:
            g_opt = st.radio("性別", ["全部", "男性", "女性"], horizontal=True)
            if g_opt != "全部": mask = mask & (df['性別'] == g_opt)
            
        if '年齡' in df.columns:
            age_range = st.slider("年齡", 18, 60, (18, 60))
            mask = mask & df['年齡'].between(age_range[0], age_range[1])

    # --- 4. 儀表板與圖表 (使用 Plotly 解決中文亂碼) ---
    filtered_df = df[mask]
    
    # KPI 指標
    total = len(filtered_df)
    left_count = len(filtered_df[filtered_df['離職'] == '是']) if '離職' in df.columns else 0
    rate = (left_count / total * 100) if total > 0 else 0
    avg_salary = filtered_df['月薪'].mean() if '月薪' in df.columns else 0
    
    with st.container():
        st.subheader("📊 戰情室儀表板")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👥 篩選人數", f"{total}")
        c2.metric("👋 離職人數", f"{left_count}")
        c3.metric("⚠️ 離職率", f"{rate:.1f}%")
        c4.metric("💰 平均月薪", f"${avg_salary:,.0f}")
    
    st.markdown("---")

    # 圖表區 (Plotly 互動圖表)
    chart1, chart2 = st.columns(2)
    
    with chart1:
        st.info("🏢 部門離職分佈 (互動式)")
        if total > 0:
            # 使用 Histogram 確保數據正確聚合
            fig = px.histogram(filtered_df, y="部門", color="離職", 
                             orientation='h',
                             color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'},
                             title="各部門離職狀況 (滑鼠懸停查看)",
                             barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("無資料")

    with chart2:
        st.info("🎂 年齡與離職 (互動式)")
        if total > 0 and '年齡' in df.columns:
            fig = px.histogram(filtered_df, x="年齡", color="離職",
                             color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'},
                             title="年齡層分佈",
                             nbins=20)
            st.plotly_chart(fig, use_container_width=True)

    chart3, chart4 = st.columns(2)
    
    with chart3:
        st.info("💰 薪資分佈 (箱型圖)")
        if total > 0 and '月薪' in df.columns:
            fig = px.box(filtered_df, x="離職", y="月薪", color="離職",
                       color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'},
                       title="離職 vs 在職 薪資比較")
            st.plotly_chart(fig, use_container_width=True)

    with chart4:
        st.info("⏳ 在公司年資")
        if total > 0 and '在公司年資' in df.columns:
            fig = px.histogram(filtered_df, x="在公司年資", color="離職",
                             color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'},
                             title="年資分佈",
                             nbins=15)
            st.plotly_chart(fig, use_container_width=True)

    # 詳細資料
    st.markdown("---")
    st.subheader(f"📋 詳細資料表 ({total} 筆)")
    st.dataframe(filtered_df)
