import streamlit as st
import pandas as pd
import gspread

# 設定頁面標題和佈局
st.set_page_config(page_title="人力資源策略模擬", layout="wide")

# --- 頁面標題與說明 ---
st.title("人力資源策略模擬")
st.markdown("---")
st.write("請輸入你的姓名與策略預算，並執行模擬。")

# --- 使用者輸入介面 ---
col1, col2 = st.columns(2)
with col1:
    player_name = st.text_input("玩家姓名", key="player_name")
with col2:
    round_number = st.number_input("回合數", min_value=1, value=1, key="round_number")

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    salary_budget = st.slider("薪資預算 (百萬)", 0, 20, 10, key="salary_budget")
with col4:
    training_budget = st.slider("培訓預算 (百萬)", 0, 10, 5, key="training_budget")

# --- 核心模擬與資料儲存 ---
if st.button("執行模擬"):
    if not player_name:
        st.warning("請輸入你的姓名！")
    else:
        # 簡單的運算邏輯：預算越高，流動率越低，滿意度越高
        turnover_rate = 50 - (salary_budget * 1.5) - (training_budget * 2.0)
        satisfaction = 60 + (salary_budget * 1.0) + (training_budget * 1.5)

        # 準備資料
        data_to_add = [
            player_name,
            round_number,
            salary_budget,
            training_budget,
            f"{turnover_rate:.2f}%",
            f"{satisfaction:.2f}分"
        ]

        # 這裡會將資料寫入 Google Sheets
        try:
            # 取得你的 Google Sheets 憑證
            gc = gspread.service_account_from_dict(st.secrets["gspread"])
            
            # 開啟你的試算表
            sh = gc.open("My Streamlit Sheet")
            worksheet = sh.worksheet("sh.worksheet")
            
            # 將資料寫入新的列
            worksheet.append_row(data_to_add)
            
            st.success(f"模擬成功！你的結果已寫入排行榜。")
        except gspread.exceptions.WorksheetNotFound:
            st.error("工作表名稱有誤，請檢查 'My Streamlit Sheet' 裡的 'sh.worksheet' 是否存在。")
        except Exception as e:
            st.error(f"寫入資料時發生錯誤：{e}")

# --- 排行榜 ---
st.header("即時排行榜")
# 從 Google Sheets 讀取資料
try:
    # 這裡使用你的 Google Sheets ID
    gsheet_url = "https://docs.google.com/spreadsheets/d/1kU4W28ZIcTwvRoWybMtzDbs6Vybp1-gLHM1QYllngIs/gviz/tq?tqx=out:csv"
    df = pd.read_csv(gsheet_url)
    
    if not df.empty:
        # 顯示所有玩家的資料，並以員工滿意度排序
        df_sorted = df.sort_values(by="員工滿意度", ascending=False)
        st.dataframe(df_sorted, hide_index=True)
    else:
        st.info("目前沒有玩家數據。")
except Exception as e:
    st.error(f"讀取資料時發生錯誤：{e}")
