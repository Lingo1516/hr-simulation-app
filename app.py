import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import os
import platform

# --- 1. 自動下載並設定中文字型 (解決亂碼與方框問題) ---
def set_chinese_font_auto():
    # 設定字型檔案名稱
    font_name = "NotoSansTC-Regular.ttf"
    
    # 如果檔案不存在，從 Google Fonts 下載 (大約 2-3 秒)
    if not os.path.exists(font_name):
        import urllib.request
        url = "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC-Regular.ttf"
        try:
            # 顯示下載進度以免使用者以為當機
            with st.spinner("正在下載中文字型檔，請稍候..."):
                urllib.request.urlretrieve(url, font_name)
        except:
            # 如果下載失敗，嘗試使用系統字型
            pass

    # 如果有下載到字型，就加入系統
    if os.path.exists(font_name):
        fm.fontManager.addfont(font_name)
        plt.rcParams['font.family'] = 'Noto Sans TC'
    else:
        # 備用方案：根據作業系統嘗試內建字型
        system_name = platform.system()
        if system_name == "Windows":
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
        elif system_name == "Darwin": 
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        else:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
            
    plt.rcParams['axes.unicode_minus'] = False # 解決負號顯示問題

# 執行字型設定
set_chinese_font_auto()

# --- 2. 頁面設定 ---
st.set_page_config(page_title="HR 離職分析戰情室 (終極版)", layout="wide")
st.title("🚀 HR 員工離職分析戰情室 (功能全開版)")
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

# --- 4. 超級側邊欄：6大維度全開 (這裡全部加回來了！) ---
if df is not None:
    st.sidebar.title("🔍 深度篩選面板")
    st.sidebar.info("已啟用全功能篩選模式")
    
    # 初始化篩選遮罩
    mask = pd.Series([True] * len(df))
    
    # === 第一組：組織結構 ===
    with st.sidebar.expander("🏢 1. 部門與職位", expanded=True):
        # 部門
        all_depts = list(df['部門'].unique())
        sel_depts = st.multiselect("部門", all_depts, default=all_depts)
        mask = mask & df['部門'].isin(sel_depts)
        
        # 職位角色
        if '職位角色' in df.columns:
            all_roles = sorted(list(df['職位角色'].unique()))
            sel_roles = st.multiselect("職位角色", all_roles, default=all_roles)
            mask = mask & df['職位角色'].isin(sel_roles)

    # === 第二組：工作負擔 ===
    with st.sidebar.expander("🔥 2. 工作負擔與通勤"):
        # 加班
        ot_opt = st.radio("是否加班", ["全部", "是", "否"], horizontal=True)
        if ot_opt != "全部": mask = mask & (df['加班'] == ot_opt)
        
        # 出差
        if '出差頻率' in df.columns:
            all_travel = list(df['出差頻率'].unique())
            sel_travel = st.multiselect("出差頻率", all_travel, default=all_travel)
            mask = mask & df['出差頻率'].isin(sel_travel)
            
        # 通勤距離
        if '家住距離' in df.columns:
            max_dist = int(df['家住距離'].max())
            dist_range = st.slider("家住距離 (公里)", 0, max_dist, (0, max_dist))
            mask = mask & df['家住距離'].between(dist_range[0], dist_range[1])

    # === 第三組：滿意度指標 ===
    with st.sidebar.expander("❤️ 3. 員工滿意度 (1低-4高)"):
        if '工作滿意度' in df.columns:
            js_range = st.slider("工作滿意度", 1, 4, (1, 4))
            mask = mask & df['工作滿意度'].between(js_range[0], js_range[1])
        
        if '環境滿意度' in df.columns:
            es_range = st.slider("環境滿意度", 1, 4, (1, 4))
            mask = mask & df['環境滿意度'].between(es_range[0], es_range[1])
            
        if '工作生活平衡' in df.columns:
            wlb_range = st.slider("工作生活平衡感", 1, 4, (1, 4))
            mask = mask & df['工作生活平衡'].between(wlb_range[0], wlb_range[1])

    # === 第四組：薪資福利 ===
    with st.sidebar.expander("💰 4. 薪資與福利"):
        if '月薪' in df.columns:
            min_pay, max_pay = int(df['月薪'].min()), int(df['月薪'].max())
            pay_range = st.slider("月薪範圍", min_pay, max_pay, (min_pay, max_pay))
            mask = mask & df['月薪'].between(pay_range[0], pay_range[1])
            
        if '加薪百分比' in df.columns:
            hike_range = st.slider("上次加薪幅度 (%)", 0, 30, (0, 30))
            mask = mask & df['加薪百分比'].between(hike_range[0], hike_range[1])
            
        if '股票選擇權等級' in df.columns:
            stock_opts = sorted(list(df['股票選擇權等級'].unique()))
            sel_stock = st.multiselect("股票選擇權等級", stock_opts, default=stock_opts)
            mask = mask & df['股票選擇權等級'].isin(sel_stock)

    # === 第五組：年資與升遷 ===
    with st.sidebar.expander("⏳ 5. 年資與升遷"):
        if '在公司年資' in df.columns:
            y_comp_range = st.slider("在公司年資 (年)", 0, 40, (0, 40))
            mask = mask & df['在公司年資'].between(y_comp_range[0], y_comp_range[1])
            
        if '上次升遷年資' in df.columns:
            promo_range = st.slider("幾年沒升遷了", 0, 15, (0, 15))
            mask = mask & df['上次升遷年資'].between(promo_range[0], promo_range[1])
            
        if '目前主管年資' in df.columns:
            mgr_range = st.slider("跟隨目前主管 (年)", 0, 20, (0, 20))
            mask = mask & df['目前主管年資'].between(mgr_range[0], mgr_range[1])

    # === 第六組：個人背景 ===
    with st.sidebar.expander("👤 6. 個人背景"):
        if '性別' in df.columns:
            g_opt = st.radio("性別", ["全部", "男性", "女性"], horizontal=True)
            if g_opt != "全部": mask = mask & (df['性別'] == g_opt)
            
        if '婚姻狀態' in df.columns:
            sel_marry = st.multiselect("婚姻狀態", df['婚姻狀態'].unique(), default=df['婚姻狀態'].unique())
            mask = mask & df['婚姻狀態'].isin(sel_marry)
            
        if '教育領域' in df.columns:
            sel_edu = st.multiselect("教育領域", df['教育領域'].unique(), default=df['教育領域'].unique())
            mask = mask & df['教育領域'].isin(sel_edu)
            
        if '年齡' in df.columns:
            age_range = st.slider("年齡", 18, 60, (18, 60))
            mask = mask & df['年齡'].between(age_range[0], age_range[1])

    # --- 5. 儀表板與圖表 (使用優化過的橫向排版) ---
    filtered_df = df[mask]
    
    # KPI 指標
    total = len(filtered_df)
    left_count = len(filtered_df[filtered_df['離職'] == '是'])
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

    # 圖表區 (橫向顯示，確保文字不重疊)
    chart1, chart2 = st.columns(2)
    
    with chart1:
        st.info("🏢 部門離職分佈 (橫向長條圖)")
        if total > 0:
            fig, ax = plt.subplots(figsize=(6, 5))
            # 這裡我們計算離職率，而非僅僅是人數，更具參考價值
            dept_stats = filtered_df.groupby('部門')['離職'].apply(lambda x: (x=='是').sum()).reset_index()
            sns.barplot(x='離職', y='部門', data=dept_stats, palette='Reds', ax=ax)
            plt.xlabel("離職人數")
            plt.ylabel("部門")
            plt.title("各部門離職人數", fontsize=14)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.write("無資料")

    with chart2:
        st.info("🎂 年齡層分佈")
        if total > 0 and '年齡' in df.columns:
            fig, ax = plt.subplots(figsize=(6, 5))
            filtered_df['年齡組'] = pd.cut(filtered_df['年齡'], bins=[0,25,35,45,60], labels=['25歲下','26-35','36-45','46歲上'])
            sns.countplot(x='年齡組', hue='離職', data=filtered_df, ax=ax, palette='Pastel1')
            plt.title("年齡層離職狀況", fontsize=14)
            plt.tight_layout()
            st.pyplot(fig)

    chart3, chart4 = st.columns(2)
    
    with chart3:
        st.info("💰 薪資與離職 (箱型圖)")
        if total > 0 and '月薪' in df.columns:
            fig, ax = plt.subplots(figsize=(6, 5))
            sns.boxplot(x='離職', y='月薪', data=filtered_df, ax=ax, palette='Set3')
            plt.title("薪資分佈比較", fontsize=14)
            plt.tight_layout()
            st.pyplot(fig)

    with chart4:
        st.info("⏳ 年資分佈")
        if total > 0 and '在公司年資' in df.columns:
            fig, ax = plt.subplots(figsize=(6, 5))
            sns.histplot(data=filtered_df, x='在公司年資', hue='離職', multiple="stack", bins=15, ax=ax)
            plt.title("在公司年資分佈", fontsize=14)
            plt.tight_layout()
            st.pyplot(fig)

    # 詳細資料
    st.markdown("---")
    st.subheader(f"📋 篩選後的詳細名單 ({total} 筆)")
    st.dataframe(filtered_df)
