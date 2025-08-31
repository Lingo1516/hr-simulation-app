import streamlit as st
import pandas as pd
from gspread import service_account
from gspread.exceptions import WorksheetNotFound
from config import * # 導入 config.py 的所有設定

# 設定頁面標題和佈局
st.set_page_config(page_title="人力資源策略模擬", layout="wide")

# --- 頁面標題與說明 ---
st.title("人力資源策略模擬")
st.markdown("---")

# --- 讀取並顯示情境 ---
st.header("當前情境")
current_scenario = SCENARIOS.get(st.session_state.round_number, SCENARIOS[1])
st.subheader(current_scenario["名稱"])
st.write(current_scenario["描述"])

# --- 使用者輸入介面 ---
st.header("策略決策")
col1, col2, col3, col4 = st.columns(4)
with col1:
    salary_budget = st.slider("薪資預算", 0, 20, 10, key="salary_budget")
with col2:
    training_budget = st.slider("培訓預算", 0, 10, 5, key="training_budget")
with col3:
    recruitment_efficiency = st.slider("招募效率", 0, 10, 5, key="recruitment_efficiency")
with col4:
    welfare_investment = st.slider("福利投入", 0, 10, 5, key="welfare_investment")

# --- 核心模擬與資料儲存 ---
if st.button("執行模擬"):
    if not st.session_state.player_name:
        st.warning("請輸入你的姓名！")
    else:
        # 計算結果 (已納入情境影響)
        turnover_rate = INITIAL_TURNOVER_RATE - (salary_budget * IMPACT_FACTORS["薪資預算"]["流動率"]) - \
                        (training_budget * IMPACT_FACTORS["培訓預算"]["流動率"]) - \
                        (recruitment_efficiency * IMPACT_FACTORS["招募效率"]["流動率"])
        satisfaction = INITIAL_SATISFACTION + (salary_budget * IMPACT_FACTORS["薪資預算"]["滿意度"]) + \
                       (training_budget * IMPACT_FACTORS["培訓預算"]["滿意度"]) + \
                       (recruitment_efficiency * IMPACT_FACTORS["招募效率"]["滿意度"])
        
        # 考慮情境乘數影響
        turnover_rate *= current_scenario["流動率乘數"]
        satisfaction *= current_scenario["滿意度乘數"]

        # 準備資料
        data_to_add = [
            st.session_state.player_name,
            st.session_state.round_number,
            salary_budget,
            training_budget,
            recruitment_efficiency,
            welfare_investment,
            f"{turnover_rate:.2f}%",
            f"{satisfaction:.2f}分"
        ]

        # 這裡會將資料寫入 Google Sheets
        try:
            gc = service_account.Credentials.from_service_account_info(st.secrets.gspread)
            sh = gc.open("My Streamlit Sheet")
            worksheet = sh.worksheet("sh.worksheet")
            worksheet.append_row(data_to_add)
            
            st.success(f"模擬成功！你的結果已寫入排行榜。")
            st.session_state.round_number += 1 # 回合數加一
        except WorksheetNotFound:
            st.error("工作表名稱有誤，請檢查 Google Sheets 裡的工作表名稱。")
        except Exception as e:
            st.error(f"寫入資料時發生錯誤：{e}")

# --- 排行榜 ---
st.header("即時排行榜")
try:
    gsheet_url = "https://docs.google.com/spreadsheets/d/1kU4W28ZIcTwvRoWybMtzDbs6Vybp1-gLHM1QYllngIs/gviz/tq?tqx=out:csv"
    df = pd.read_csv(gsheet_url)
    
    if not df.empty:
        df_sorted = df.sort_values(by="員工滿意度", ascending=False)
        st.dataframe(df_sorted, hide_index=True)
    else:
        st.info("目前沒有玩家數據。")
except Exception as e:
    st.error(f"讀取資料時發生錯誤：{e}")
