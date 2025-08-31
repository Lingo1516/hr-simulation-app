import streamlit as st
import pandas as pd

# 設定頁面標題和佈局
st.set_page_config(page_title="人力資源策略模擬", layout="wide")

# 初始化 session state
if 'results' not in st.session_state:
    st.session_state.results = None

# --- 頁面標題與說明 ---
st.title("人力資源策略模擬")
st.markdown("---")
st.write("請輸入你的姓名與策略預算，並執行模擬。")

# --- 使用者輸入介面 ---
player_name = st.text_input("玩家姓名", key="player_name")
round_number = st.number_input("回合數", min_value=1, value=1, key="round_number")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    salary_budget = st.slider("薪資預算 (百萬)", 0, 20, 10, key="salary_budget")
with col2:
    training_budget = st.slider("培訓預算 (百萬)", 0, 10, 5, key="training_budget")

# --- 核心模擬運算 ---
if st.button("執行模擬"):
    if not player_name:
        st.warning("請輸入你的姓名！")
    else:
        # 簡單的運算邏輯：預算越高，流動率越低，滿意度越高
        turnover_rate = 50 - (salary_budget * 1.5) - (training_budget * 2.0)
        satisfaction = 60 + (salary_budget * 1.0) + (training_budget * 1.5)

        # 將結果儲存到 session state
        st.session_state.results = pd.DataFrame({
            "指標": ["員工流動率", "員工滿意度"],
            "結果": [f"{turnover_rate:.2f}%", f"{satisfaction:.2f}分"]
        })

        st.success(f"模擬成功！你的結果已顯示。")

# 顯示結果
if st.session_state.results is not None:
    st.header("模擬結果")
    st.dataframe(st.session_state.results, hide_index=True)
