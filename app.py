import streamlit as st
import pandas as pd
from gspread import service_account
from gspread.exceptions import WorksheetNotFound

# Setting page title and layout
st.set_page_config(page_title="人力資源策略模擬", layout="wide")

# Initialize session state for the game
if 'player_name' not in st.session_state:
    st.session_state.player_name = ''
if 'round_number' not in st.session_state:
    st.session_state.round_number = 1

# --- Page Title and Description ---
st.title("人力資源策略模擬")
st.markdown("---")
st.write("請輸入你的姓名與策略預算，並執行模擬。")

# --- User Input Interface ---
player_name = st.text_input("玩家姓名", value=st.session_state.player_name, key="player_name_input")
st.session_state.player_name = player_name

st.write(f"當前回合數: {st.session_state.round_number}")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    salary_budget = st.slider("薪資預算 (百萬)", 0, 20, 10, key="salary_budget")
with col2:
    training_budget = st.slider("培訓預算 (百萬)", 0, 10, 5, key="training_budget")

# --- Core Simulation and Data Storage ---
if st.button("執行模擬"):
    if not st.session_state.player_name:
        st.warning("請輸入你的姓名！")
    else:
        # Simple calculation logic: higher budget leads to lower turnover and higher satisfaction
        turnover_rate = 50 - (salary_budget * 1.5) - (training_budget * 2.0)
        satisfaction = 60 + (salary_budget * 1.0) + (training_budget * 1.5)

        # Preparing data to be added to Google Sheets
        data_to_add = [
            st.session_state.player_name,
            st.session_state.round_number,
            salary_budget,
            training_budget,
            f"{turnover_rate:.2f}%",
            f"{satisfaction:.2f}分"
        ]

        # Writing data to Google Sheets
        try:
            # Get your Google Sheets credentials
            # Using the correct syntax to get credentials from st.secrets
            gc = service_account.from_keyfile_dict(st.secrets["gspread"])
            
            # Opening your spreadsheet
            sh = gc.open("My Streamlit Sheet")
            worksheet = sh.worksheet("sh.worksheet")
            
            # Appending the new row to the worksheet
            worksheet.append_row(data_to_add)
            
            st.success("模擬成功！你的結果已寫入排行榜。")
            st.session_state.round_number += 1
        except WorksheetNotFound:
            st.error("工作表名稱有誤，請檢查 'My Streamlit Sheet' 裡的工作表名稱。")
        except Exception as e:
            st.error(f"寫入資料時發生錯誤：{e}")

# --- Real-time Leaderboard ---
st.header("即時排行榜")
# Reading data from Google Sheets
try:
    # Using your Google Sheets ID
    gsheet_url = "https://docs.google.com/spreadsheets/d/1kU4W28ZIcTwvRoWybMtzDbs6Vybp1-gLHM1QYllngIs/gviz/tq?tqx=out:csv"
    df = pd.read_csv(gsheet_url)
    
    if not df.empty:
        # Displaying all players' data, sorted by employee satisfaction
        df_sorted = df.sort_values(by="員工滿意度", ascending=False)
        st.dataframe(df_sorted, hide_index=True)
    else:
        st.info("目前沒有玩家數據。")
except Exception as e:
    st.error(f"讀取資料時發生錯誤：{e}")
