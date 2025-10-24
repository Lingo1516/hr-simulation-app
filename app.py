# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V4.0 - Reference Integration)
#
# V4.0 更新：
# 1. (參考用戶程式) 登入方式改為帳號密碼輸入。
# 2. (參考用戶程式) 儀表板顯示改用 st.write() 簡化，提高穩定性。
# 3. 保留 V3.x 詳細決策表單、穩定結算引擎、檔案狀態管理。
# 4. 老師控制台密碼總覽改用 st.write()。

import streamlit as st
import pandas as pd
import copy
import pickle
import os
import streamlit.components.v1 as components

# --- 0. (V3.1 強化) 檔案同步相關 ---
DECISIONS_FILE = "decisions_state.pkl"

def save_decisions_to_file(decisions_dict):
    if not isinstance(decisions_dict, dict): st.error("儲存決策錯誤：傳入的不是字典！"); decisions_dict = {}
    try:
        with open(DECISIONS_FILE, 'wb') as f: pickle.dump(decisions_dict, f)
    except Exception as e: st.error(f"儲存決策檔案 {DECISIONS_FILE} 時出錯: {e}")

def load_decisions_from_file():
    decisions = {}
    if os.path.exists(DECISIONS_FILE):
        try:
            with open(DECISIONS_FILE, 'rb') as f:
                loaded_data = pickle.load(f)
                if isinstance(loaded_data, dict): decisions = loaded_data
                else: st.warning(f"決策檔案 {DECISIONS_FILE} 內容格式不符 (非字典)，將重置。"); delete_decisions_file()
        except FileNotFoundError: st.warning(f"嘗試讀取決策檔案 {DECISIONS_FILE} 時找不到檔案。")
        except EOFError: st.warning(f"決策檔案 {DECISIONS_FILE} 為空或損壞，將重置。"); delete_decisions_file()
        except pickle.UnpicklingError: st.warning(f"決策檔案 {DECISIONS_FILE} 格式錯誤，將重置。"); delete_decisions_file()
        except Exception as e: st.error(f"讀取決策檔案 {DECISIONS_FILE} 時發生未知錯誤: {e}"); delete_decisions_file()
    return decisions

def delete_decisions_file():
    try:
        if os.path.exists(DECISIONS_FILE): os.remove(DECISIONS_FILE)
    except Exception as e: st.error(f"刪除決策檔案 {DECISIONS_FILE} 時出錯: {e}")

# --- 1. 遊戲參數 (V2 升級版) ---
GLOBAL_PARAMS = {
    # ... (參數內容同 V3.9) ...
    'factory_cost': 5000000,'factory_maintenance': 100000,'factory_capacity': 8,
    'line_p1_cost': 1000000,'line_p1_maintenance': 20000,'line_p1_capacity': 1000,
    'raw_material_cost_R1': 100,'p1_labor_cost': 50,'p1_material_needed_R1': 1,'p1_depreciation_per_line': 10000,
    'line_p2_cost': 1200000,'line_p2_maintenance': 25000,'line_p2_capacity': 800,
    'raw_material_cost_R2': 150,'p2_labor_cost': 70,'p2_material_needed_R2': 1,'p2_depreciation_per_line': 12000,
    'bank_loan_interest_rate_per_season': 0.02,'emergency_loan_interest_rate': 0.05,'tax_rate': 0.20,
    'rd_costs_to_level_up': {2: 500000, 3: 1500000, 4: 3500000, 5: 6500000}
}
DEFAULT_PRICE_P1 = 300; DEFAULT_AD_P1 = 50000; DEFAULT_PRICE_P2 = 450; DEFAULT_AD_P2 = 50000

# --- 2. (V2.2 安全升級) 密碼系統 ---
PASSWORDS = {
    # ... (密碼內容同 V3.9) ...
    "admin": "admin123", "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660", "第 7 組": "ice112",
    "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# --- 3. 團隊狀態初始化 (V2.3) ---
def init_team_state(team_key):
    # (此函數與 V3.9 版本完全相同)
    initial_cash = 10000000; initial_factories = 1; initial_lines_p1 = 1; initial_lines_p2 = 1
    initial_inv_r1 = 2000; initial_inv_r2 = 2000; initial_inv_p1 = 500; initial_inv_p2 = 500
    cogs_p1 = (...); cogs_p2 = (...)
    inv_value = (...); fixed_assets = (...); total_assets = (...); initial_equity = total_assets
    return { # ... (返回字典結構同 V3.9) ...
    }

# --- 3.1 (V2.5) 資產負債表平衡函數 ---
def balance_bs(bs_data):
    # (此函數與 V3.9 版本完全相同)
    bs_data['total_assets'] = bs_data.get('cash',0) + bs_data.get('inventory_value',0) + bs_data.get('fixed_assets_value',0) - bs_data.get('accumulated_depreciation',0)
    bs_data['total_liabilities_and_equity'] = bs_data.get('bank_loan',0) + bs_data.get('shareholder_equity',0)
    if abs(bs_data['total_assets'] - bs_data['total_liabilities_and_equity']) > 1:
        diff = bs_data['total_assets'] - bs_data['total_liabilities_and_equity']
        bs_data['shareholder_equity'] += diff
        bs_data['total_liabilities_and_equity'] = bs_data['total_assets']
    return bs_data

# --- 4. 儀表板 (Dashboard V2) (*** V4.0 簡化顯示 ***) ---
def display_dashboard(team_key, team_data):
    st.header(f"📈 {team_data.get('team_name', team_key)} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data.get('BS', {})
    is_data = team_data.get('IS', {})
    mr = team_data.get('MR', {})

    # V4.0 使用 st.write 簡化顯示
    st.subheader("📊 市場報告 (上季)")
    st.write(mr)

    st.subheader("💰 損益表 (上季)")
    # V4.0 為了稍微美觀，格式化一下淨利
    net_income = is_data.get('net_income', 0)
    st.metric("💹 稅後淨利 (Net Income)", f"${net_income:,.0f}")
    with st.expander("查看詳細損益表 (原始數據)"):
        st.write(is_data)

    st.subheader("🏦 資產負債表 (當前)")
    # V4.0 格式化總資產
    total_assets = bs.get('total_assets', 0)
    st.metric("🏦 總資產 (Total Assets)", f"${total_assets:,.0f}")
    with st.expander("查看詳細資產負債表 (原始數據)"):
        st.write(bs)

    st.subheader("🏭 內部資產 (非財報)")
    col1, col2, col3 = st.columns(3)
    col1.metric("工廠 (座)", team_data.get('factories', 0))
    col2.metric("P1 生產線 (條)", team_data.get('lines_p1', 0))
    col3.metric("P2 生產線 (條)", team_data.get('lines_p2', 0))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("R1 庫存 (u)", f"{team_data.get('inventory_R1_units', 0):,.0f}")
    col2.metric("P1 庫存 (u)", f"{team_data.get('inventory_P1_units', 0):,.0f}")
    col3.metric("R2 庫存 (u)", f"{team_data.get('inventory_R2_units', 0):,.0f}")
    col4.metric("P2 庫存 (u)", f"{team_data.get('inventory_P2_units', 0):,.0f}")

# --- 5. 決策表單 (Decision Form V2) (V3.7 修改提交邏輯) ---
def display_decision_form(team_key):
    # (此函數與 V3.9 版本完全相同，保留詳細表單)
    team_data = st.session_state.teams[team_key]
    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_data['team_name']} ({team_key}) - 第 {st.session_state.game_season} 季決策單")
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs(["P1 產品決策", "P2 產品決策", "生產與資本決策", "財務決策"])
        # ... (各 Tab 內容同 V3.9) ...
        submitted = st.form_submit_button("提交本季決策")
        if submitted:
            # (檢查邏輯與 V3.9 相同)
            if ...: st.error(...) ; return
            if ...: st.error(...) ; return
            if ...: st.error(...) ; return
            decision_data = { ... } # 收集決策
            all_decisions = load_decisions_from_file() # 讀檔
            all_decisions[team_key] = decision_data    # 更新
            save_decisions_to_file(all_decisions)      # 寫檔
            st.success(...) ; st.rerun()

# --- 6. 結算引擎 (V3.9) ---
def run_season_calculation():
    """V3.9 結算引擎，強制類型檢查 + 穩定性"""
    # (此函數與 V3.9 版本完全相同)
    teams = st.session_state.teams
    current_decisions_from_file = load_decisions_from_file() # 必定讀檔
    final_decisions = {}
    DEFAULT_PRICE_P1 = 300; DEFAULT_AD_P1 = 50000; DEFAULT_PRICE_P2 = 450; DEFAULT_AD_P2 = 50000

    for team_key in team_list: # V3.0
        if team_key not in teams: st.session_state.teams[team_key] = init_team_state(team_key)
        team_data = teams.get(team_key) # V3.9
        if not isinstance(team_data, dict): st.error(...) ; continue # V3.9
        if team_key in current_decisions_from_file:
            decision_data = current_decisions_from_file[team_key]
            if not isinstance(decision_data, dict): st.error(...); decision_data = {} # V3.9
            else: final_decisions[team_key] = decision_data
        else: # 預設懲罰 (V3.8 修正)
             st.warning(...)
             mr_data = team_data.get('MR', {}); # ... (V3.8 檢查 mr_data) ...
             final_decisions[team_key] = { ... } # (V3.8 預設值)
        if team_key not in final_decisions: final_decisions[team_key] = { ... } # V3.9 再次確保

    # === 階段 1: 結算支出、生產、研發 ===
    for team_key, decision in final_decisions.items(): # ... (結算邏輯同 V3.9, 含 .get() 防禦) ...
        team_data['IS'] = is_data # 存回 state
    # === 階段 2: 市場結算 (V3.5 修正) ===
    st.warning("V1 結算引擎：使用簡化銷售模型...")
    # --- P1 市場 ---
    market_p1_data = {}; total_score_p1 = 0
    for key, d in final_decisions.items(): # ... (含 V3.5 強制數值檢查) ...
        market_p1_data[key] = score; total_score_p1 += score
    TOTAL_MARKET_DEMAND_P1 = 50000
    for team_key, score in market_p1_data.items(): # ... (含 V3.5 強制數值檢查) ...
        team_data['MR']['market_share_p1'] = market_share
    # --- P2 市場 ---
    market_p2_data = {}; total_score_p2 = 0
    for key, d in final_decisions.items(): # ... (含 V3.5 強制數值檢查) ...
        market_p2_data[key] = score; total_score_p2 += score
    TOTAL_MARKET_DEMAND_P2 = 40000
    for team_key, score in market_p2_data.items(): # ... (含 V3.5 強制數值檢查) ...
        team_data['MR']['market_share_p2'] = market_share
    # === 階段 3: 財務報表結算 ===
    for team_key, team_data in teams.items(): # ... (結算邏輯同 V3.9) ...
        bs = balance_bs(team_data.get('BS', {})) # V3.9
        # === 階段 4: 緊急貸款 (破產檢查) ===
        if bs.get('cash', 0) < 0: # V3.9
             # ... (結算邏輯同 V3.9) ...
            bs = balance_bs(bs) # V2.5
        team_data['BS'] = bs if isinstance(bs, dict) else {}; team_data['IS'] = is_data if isinstance(is_data, dict) else {} # V3.9
    # === 階段 5: 推進遊戲 (V3.7) ===
    st.session_state.game_season += 1
    # st.session_state.decisions = {} # V3.7 移除
    delete_decisions_file() # 只刪除檔案
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")


# --- 7. (V2.5 修改) 老師專用函式 (*** V4.0 簡化密碼顯示 ***) ---
def calculate_company_value(bs_data):
    # (此函數與 V3.9 版本完全相同)
    value = bs_data.get('cash', 0) + bs_data.get('inventory_value', 0) + \
            (bs_data.get('fixed_assets_value', 0) - bs_data.get('accumulated_depreciation', 0)) - \
            bs_data.get('bank_loan', 0)
    return value

def display_admin_dashboard():
    """顯示老師的控制台畫面"""
    st.header(f"👨‍🏫 管理員控制台 (第 {st.session_state.game_season} 季)")

    # --- 學生密碼總覽 (*** V4.0 簡化顯示 ***) ---
    with st.expander("🔑 學生密碼總覽"):
        st.warning("請勿將此畫面展示給學生。")
        # 直接打印字典
        st.write(PASSWORDS)
        st.caption("如需修改密碼，請直接修改 app.py 檔案頂部的 PASSWORDS 字典。")

    # --- 修改團隊數據 ---
    with st.expander("🔧 修改團隊數據 (Edit Team Data)"): # ... (內容同 V3.9) ...
    # --- A. 排行榜 (V2.4 格式化) ---
    st.subheader("遊戲排行榜 (依公司總價值)") # ... (內容同 V3.9) ...
    # --- B. 監控面板 (V3.7 只依賴檔案) ---
    st.subheader("本季決策提交狀態") # ... (內容同 V3.9) ...
    # --- C. 控制按鈕 (V3.7) ---
    st.subheader("遊戲控制") # ... (內容同 V3.9) ...

# --- 8. 主程式 (Main App) (*** V4.0 修改登入邏輯 ***) ---
st.set_page_config(layout="wide")

# --- 初始化 session_state ---
if 'game_season' not in st.session_state:
    st.session_state.game_season = 1
    st.session_state.teams = {}
    # V3.7 不再需要 decisions 初始化
    st.session_state.logged_in_user = None

# --- 登入邏輯 (*** V4.0 修改 ***) ---
if st.session_state.logged_in_user is None:
    st.title("🚀 新星製造 V2 - 遊戲登入")

    # V4.0 使用 text_input 作為帳號
    username = st.text_input("請輸入您的隊伍名稱 (例如 第 1 組) 或 管理員帳號 (admin)")
    password = st.text_input("請輸入密碼：", type="password")

    if st.button("登入"):
        # 檢查是否為老師
        if username == "admin" and password == PASSWORDS.get("admin"):
            st.session_state.logged_in_user = "admin"
            st.rerun()
        # 檢查是否為學生隊伍
        elif username in PASSWORDS and password == PASSWORDS.get(username):
            st.session_state.logged_in_user = username
            # 確保隊伍已初始化
            if username not in st.session_state.teams:
                st.session_state.teams[username] = init_team_state(username)
            st.rerun()
        # 密碼或帳號錯誤
        else:
            st.error("帳號或密碼錯誤！請檢查輸入是否正確（例如 '第 1 組' 中間有空格）。")

# --- 登入後的畫面 ---
else:
    current_user = st.session_state.logged_in_user
    if current_user == "admin":
        # --- A. 老師畫面 ---
        display_admin_dashboard()
    elif current_user in team_list:
        # --- B. 學生畫面 (V3.7 只依賴檔案) ---
        team_key = current_user
        if team_key not in st.session_state.teams: st.session_state.teams[team_key] = init_team_state(team_key)
        current_team_data = st.session_state.teams.get(team_key, init_team_state(team_key))

        # --- B1. 學生側邊欄 ---
        st.sidebar.header(f"🎓 {current_team_data.get('team_name', team_key)} ({team_key})") # V3.9
        new_team_name = st.sidebar.text_input(...)
        if new_team_name != current_team_data.get('team_name', team_key): # ... (修改隊名邏輯同 V3.9) ...
            st.rerun()
        if st.sidebar.button("登出"): st.session_state.logged_in_user = None; st.rerun()

        # --- B2. 學生主畫面 ---
        display_dashboard(team_key, current_team_data)
        st.markdown("---")

        # ** V3.7 核心修改：只從檔案讀取狀態來決定顯示 **
        current_decisions_from_file = load_decisions_from_file()

        if team_key in current_decisions_from_file:
            st.info(f"您已提交第 {st.session_state.game_season} 季的決策，請等待老師結算...")
        else:
            display_decision_form(team_key)
