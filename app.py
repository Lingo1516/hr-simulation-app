import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. 網頁設定 ---
st.set_page_config(page_title="HR 離職分析戰情室", layout="wide")
st.title("🚀 HR 員工離職分析戰情室")

# --- 2. 自動讀取 (檔名已更新為您提供的版本) ---
@st.cache_data
def load_data():
    # 這裡改成您剛剛說的簡潔檔名
    file_name = 'HR-Employee-Attrition-完美中文版.csv'
    
    if os.path.exists(file_name):
        try:
            # header=1 是因為原本檔案第一列可能是標題，如果檔案第一列就是欄位名稱，可以拿掉 header=1
            # 保險起見，我們先用標準讀取，如果欄位跑掉再調整
            df = pd.read_csv(file_name) 
            
            # 如果讀出來第一列看起來像標題，需要跳過，請打開下面這行註解：
            # df = pd.read_csv(file_name, header=1)

            # 欄位改名 (確保程式能運作)
            if '流失' in df.columns: df.rename(columns={'流失': '離職'}, inplace=True)
            return df
        except Exception as e:
            st.error(f"❌ 讀取失敗：{e}")
            return None
    else:
        # 如果還是找不到，印出錯誤讓老師知道
        st.error(f"❌ 系統找不到檔案！")
        st.code(f"程式正在找這個檔名：\n{file_name}", language="text")
        st.warning("請老師確認 GitHub 上的檔名是否完全一致 (包含 .csv)")
        return None

df = load_data()

# --- 3. 成功讀取後，直接顯示圖表 ---
if df is not None:
    st.success("✅ 資料連線成功！直接開始分析。")
    
    # 預設全選
    if '部門' in df.columns:
        all_depts = list(df['部門'].unique())
        
        # 側邊欄
        with st.sidebar:
            st.header("🔍 篩選面板")
            sel_depts = st.multiselect("部門篩選", all_depts, default=all_depts)
            if '加班' in df.columns:
                ot_opt = st.radio("加班篩選", ["全部", "是", "否"])
            else:
                ot_opt = "全部"

        # 篩選邏輯
        mask = df['部門'].isin(sel_depts)
        if ot_opt != "全部":
            mask = mask & (df['加班'] == ot_opt)
        filtered_df = df[mask]
        
        # --- 儀表板區 ---
        col1, col2, col3 = st.columns(3)
        
        # 離職率計算
        total = len(filtered_df)
        left = len(filtered_df[filtered_df['離職']=='是']) if '離職' in filtered_df.columns else 0
        rate = (left/total*100) if total > 0 else 0
        
        col1.metric("總人數", total)
        col2.metric("離職人數", left)
        col3.metric("離職率", f"{rate:.1f}%")
        
        st.markdown("---")
        
        # 圖表區
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("📊 部門離職狀況")
            if not filtered_df.empty:
                fig = px.histogram(filtered_df, y="部門", color="離職", 
                                 orientation='h',
                                 color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'},
                                 title="部門離職人數")
                st.plotly_chart(fig, use_container_width=True)
                
        with c2:
            st.subheader("🎂 年齡分佈")
            if not filtered_df.empty and '年齡' in df.columns:
                fig2 = px.histogram(filtered_df, x="年齡", color="離職",
                                  color_discrete_map={'是':'#FF4B4B', '否':'#45aaf2'},
                                  title="年齡層離職風險")
                st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.dataframe(filtered_df)
    else:
        st.error("❌ 檔案欄位不符：找不到「部門」欄位，請檢查 CSV 內容。")
