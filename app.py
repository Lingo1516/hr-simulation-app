# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V3.6 - State Decoupling)
#
# V3.6 更新：
# 1. (根本性修正) 徹底解決 KeyError: 'decisions' in Admin Dashboard。
#    - display_admin_dashboard 的「監控面板」現在【只】依賴讀取檔案 (load_decisions_from_file)。
#    - 將 session_state.decisions 的同步操作放在更安全的位置，顯示不再依賴它。
# 2. 再次強化所有狀態讀寫點的防禦性。

import streamlit as st
import pandas as pd
import copy
import pickle # V2.8
import os     # V2.8
import streamlit.components.v1 as components

# --- 0. (V3.1 強化) 檔案同步相關 ---
DECISIONS_FILE = "decisions_state.pkl"

def save_decisions_to_file(decisions_dict):
    if not isinstance(decisions_dict, dict): st.error("儲存決策錯誤：傳入的不是字典！"); decisions_dict = {}
    try:
        with open(DECISIONS_FILE, 'wb') as f: pickle.dump(decisions_dict, f)
    except Exception as e: st.error(f"儲存決策檔案 {DECISIONS_FILE} 時出錯: {e}")

def load_decisions_from_file():
    # (此函數與 V3.1 版本完全相同，保證返回字典)
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
    # (此函數與 V3.1 版本完全相同)
    try:
        if os.path.exists(DECISIONS_FILE): os.remove(DECISIONS_FILE)
    except Exception as e: st.error(f"刪除決策檔案 {DECISIONS_FILE} 時出錯: {e}")

# --- 1. 遊戲參數 (V2 升級版) ---
GLOBAL_PARAMS = {
    # ... (參數內容同 V3.5) ...
    'factory_cost': 5000000,'factory_maintenance': 100000,'factory_capacity': 8,
    'line_p1_cost': 1000000,'line_p1_maintenance': 20000,'line_p1_capacity': 1000,
    'raw_material_cost_R1': 100,'p1_labor_cost': 50,'p1_material_needed_R1': 1,'p1_depreciation_per_line': 10000,
    'line_p2_cost': 1200000,'line_p2_maintenance': 25000,'line_p2_capacity': 800,
    'raw_material_cost_R2': 150,'p2_labor_cost': 70,'p2_material_needed_R2': 1,'p2_depreciation_per_line': 12000,
    'bank_loan_interest_rate_per_season': 0.02,'emergency_loan_interest_rate': 0.05,'tax_rate': 0.20,
    'rd_costs_to_level_up': {2: 500000, 3: 1500000, 4: 3500000, 5: 6500000}
}

# --- 2. (V2.2 安全升級) 密碼系統 ---
PASSWORDS = {
    # ... (密碼內容同 V3.5) ...
    "admin": "admin123", "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660", "第 7 組": "ice112",
    "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# --- 3. 團隊狀態初始化 (V2.3) ---
def init_team_state(team_key):
    # (此函數與 V3.5 版本完全相同)
    initial_cash = 10000000; initial_factories = 1; initial_lines_p1 = 1; initial_lines_p2 = 1
    initial_inv_r1 = 2000; initial_inv_r2 = 2000; initial_inv_p1 = 500; initial_inv_p2 = 500
    cogs_p1 = (...); cogs_p2 = (...)
    inv_value = (...); fixed_assets = (...); total_assets = (...); initial_equity = total_assets
    return {
        'team_name': team_key,
        'BS': {'cash': initial_cash, 'inventory_value': inv_value, 'fixed_assets_value': fixed_assets, 'accumulated_depreciation': 0, 'total_assets': total_assets, 'bank_loan': 0, 'shareholder_equity': initial_equity, 'total_liabilities_and_equity': total_assets},
        'IS': {k: 0 for k in [...]},
        'factories': initial_factories, 'lines_p1': initial_lines_p1, 'lines_p2': initial_lines_p2,
        'inventory_R1_units': initial_inv_r1, 'inventory_R2_units': initial_inv_r2, 'inventory_P1_units': initial_inv_p1, 'inventory_P2_units': initial_inv_p2,
        'rd_level_P1': 1, 'rd_level_P2': 1, 'rd_investment_P1': 0, 'rd_investment_P2': 0,
        'MR': {'price_p1': 300, 'ad_p1': 50000, 'sales_units_p1': 0, 'market_share_p1': 0.0, 'price_p2': 450, 'ad_p2': 50000, 'sales_units_p2': 0, 'market_share_p2': 0.0,}
    }

# --- 3.1 (V2.5) 資產負債表平衡函數 ---
def balance_bs(bs_data):
    # (此函數與 V3.5 版本完全相同)
    bs_data['total_assets'] = bs_data['cash'] + bs_data['inventory_value'] + bs_data['fixed_assets_value'] - bs_data['accumulated_depreciation']
    bs_data['total_liabilities_and_equity'] = bs_data['bank_loan'] + bs_data['shareholder_equity']
    if abs(bs_data['total_assets'] - bs_data['total_liabilities_and_equity']) > 1:
        diff = bs_data['total_assets'] - bs_data['total_liabilities_and_equity']
        bs_data['shareholder_equity'] += diff
        bs_data['total_liabilities_and_equity'] = bs_data['total_assets']
    return bs_data

# --- 4. 儀表板 (Dashboard V2) (V2.4 格式化) ---
def display_dashboard(team_key, team_data):
    # (此函數與 V3.5 版本完全相同)
    st.header(f"📈 {team_data['team_name']} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data['BS']; is_data = team_data['IS']; mr = team_data['MR']
    tab1, tab2, tab3 = st.tabs(["📊 市場報告 (上季)", "💰 損益表 (上季)", "🏦 資產負債表 (當前)"])
    # ... (tab1, tab2, tab3 內容同 V3.5) ...
    with tab1: # 市場報告
        st.subheader("P1 市場 (上季)"); col1, col2, col3, col4 = st.columns(4); # ... metrics ...
        st.subheader("P2 市場 (上季)"); col1, col2, col3, col4 = st.columns(4); # ... metrics ...
    with tab2: # 損益表
        st.subheader("損益表 (Income Statement) - 上一季"); st.metric(...);
        with st.expander("查看詳細損益表"): st.markdown(f"""...""")
    with tab3: # 資產負債表
        st.subheader("資產負債表 (Balance Sheet) - 當前"); st.metric(...);
        with st.expander("查看詳細資產負債表"): st.markdown(f"""...""")
        st.subheader("內部資產 (非財報)"); col1, col2, col3 = st.columns(3); # ... metrics ...
        col1, col2, col3, col4 = st.columns(4); # ... metrics ...

# --- 5. 決策表單 (Decision Form V2) (V3.3 修改提交邏輯) ---
def display_decision_form(team_key):
    # (此函數與 V3.5 版本完全相同)
    team_data = st.session_state.teams[team_key]
    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_data['team_name']} ({team_key}) - 第 {st.session_state.game_season} 季決策單")
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs(["P1 產品決策", "P2 產品決策", "生產與資本決策", "財務決策"])
        # ... (各 Tab 內容同 V3.5) ...
        with tab_p1: decision_price_P1 = st.slider(...) # ...
        with tab_p2: decision_price_P2 = st.slider(...) # ...
        with tab_prod: decision_produce_P1 = col1.number_input(...) # ...
        with tab_fin: decision_loan = col1.number_input(...) # ...

        submitted = st.form_submit_button("提交本季決策")
        if submitted:
            # (檢查邏輯與 V3.5 相同)
            if ...: st.error(...) ; return # 工廠容量檢查
            if ...: st.error(...) ; return # P1 產能檢查
            if ...: st.error(...) ; return # P2 產能檢查

            decision_data = { ... } # 收集本次決策
            all_decisions = load_decisions_from_file() # V3.3
            all_decisions[team_key] = decision_data # V3.3
            save_decisions_to_file(all_decisions) # V3.3
            st.session_state.decisions = all_decisions # V3.3 同步 state
            st.success(...) ; st.rerun()

# --- 6. 結算引擎 (V3.5 修正) ---
def run_season_calculation():
    """V3.5 結算引擎，優先讀取檔案狀態 + 研發穩定性 + 市場計算穩定性"""
    # (此函數與 V3.5 版本完全相同，包含數值檢查)
    teams = st.session_state.teams
    current_decisions_from_file = load_decisions_from_file() # 必定讀檔
    st.session_state.decisions = current_decisions_from_file # 同步 state
    final_decisions = {}
    DEFAULT_PRICE_P1 = 300; DEFAULT_AD_P1 = 50000; DEFAULT_PRICE_P2 = 450; DEFAULT_AD_P2 = 50000

    for team_key in team_list: # V3.0
        if team_key not in teams: st.session_state.teams[team_key] = init_team_state(team_key)
        team_data = teams[team_key]
        if team_key in current_decisions_from_file: final_decisions[team_key] = current_decisions_from_file[team_key]
        else: # 預設懲罰
            st.warning(f"警告：{team_data['team_name']} ({team_key}) 未提交決策，將使用預設。")
            final_decisions[team_key] = { ... } # (預設值同 V3.5)
    # === 階段 1: 結算支出、生產、研發 (V3.2 修正) ===
    for team_key, decision in final_decisions.items(): # ... (結算邏輯同 V3.5, 含研發檢查) ...
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
    # (此階段邏輯與 V3.5 相同)
    for team_key, team_data in teams.items(): # ... (結算邏輯同 V3.5) ...
        bs = balance_bs(bs) # V2.5
        # === 階段 4: 緊急貸款 (破產檢查) ===
        if bs['cash'] < 0: # ... (結算邏輯同 V3.5) ...
            bs = balance_bs(bs) # V2.5
        team_data['BS'] = bs; team_data['IS'] = is_data # 存回 state
    # === 階段 5: 推進遊戲 (V2.8) ===
    st.session_state.game_season += 1
    st.session_state.decisions = {} # 清空 session state
    delete_decisions_file() # 刪除檔案
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")


# --- 7. (V2.5 修改) 老師專用函式 (*** V3.6 徹底解耦 ***) ---
def calculate_company_value(bs_data):
    # (此函數與 V3.5 版本完全相同)
    value = bs_data.get('cash', 0) + bs_data.get('inventory_value', 0) + \
            (bs_data.get('fixed_assets_value', 0) - bs_data.get('accumulated_depreciation', 0)) - \
            bs_data.get('bank_loan', 0)
    return value

def display_admin_dashboard():
    """顯示老師的控制台畫面"""
    st.header(f"👨‍🏫 管理員控制台 (第 {st.session_state.game_season} 季)")

    # --- 學生密碼總覽 ---
    with st.expander("🔑 學生密碼總覽"): # ... (內容同 V3.5) ...
    # --- 修改團隊數據 ---
    with st.expander("🔧 修改團隊數據 (Edit Team Data)"): # ... (內容同 V3.5) ...
    # --- A. 排行榜 (V2.4 格式化) ---
    st.subheader("遊戲排行榜 (依公司總價值)") # ... (內容同 V3.5) ...
    # --- B. 監控面板 (*** V3.6 徹底解耦 ***) ---
    st.subheader("本季決策提交狀態")
    all_submitted = True; submitted_count = 0; cols = st.columns(5)

    # ** V3.6 核心修改：必定從檔案讀取狀態來顯示 **
    current_decisions_from_file = load_decisions_from_file()
    # ** V3.6 不再依賴同步 session_state 來顯示，只用於結算 **
    # st.session_state.decisions = current_decisions_from_file

    for i, team_key in enumerate(team_list):
        col = cols[i % 5]
        if team_key not in st.session_state.teams: st.session_state.teams[team_key] = init_team_state(team_key)
        team_data = st.session_state.teams[team_key]
        display_name = f"{team_data['team_name']} ({team_key})"

        # ** 使用從檔案讀取的狀態 **
        if team_key not in current_decisions_from_file:
            col.warning(f"🟡 {display_name}\n(尚未提交)")
            all_submitted = False
        else:
            col.success(f"✅ {display_name}\n(已提交)")
            submitted_count += 1

    st.info(f"提交進度: {submitted_count} / {len(team_list)}")
    if st.button("🔄 刷新提交狀態 (Refresh Status)"): st.rerun() # V3.0

    # --- C. 控制按鈕 (*** V3.6 確保重置乾淨 ***) ---
    st.subheader("遊戲控制")
    if st.button("➡️ 結算本季"):
        if not all_submitted: st.warning("警告：正在強制結算...")
        with st.spinner("正在執行市場結算..."): run_season_calculation() # 結算內部會讀檔
        st.rerun()
    if st.button("♻️ !!! 重置整個遊戲 !!!"):
        # V3.6 確保所有相關狀態都被清空
        st.session_state.game_season = 1
        st.session_state.teams = {}
        st.session_state.decisions = {} # 清空 session state
        st.session_state.logged_in_user = None
        delete_decisions_file() # 刪除檔案
        st.success("遊戲已重置回第 1 季，所有數據已清除。")
        st.rerun()
    if st.button("登出"): st.session_state.logged_in_user = None; st.rerun()

# --- 8. 主程式 (Main App) (*** V3.6 強化狀態讀取 ***) ---
st.set_page_config(layout="wide")

# --- 初始化 session_state ---
# V3.6 確保 decisions 初始也是從檔案讀
if 'game_season' not in st.session_state:
    st.session_state.game_season = 1
    st.session_state.teams = {}
    st.session_state.decisions = load_decisions_from_file() # 確保初始讀檔
    st.session_state.logged_in_user = None

# --- 登入邏輯 ---
if st.session_state.logged_in_user is None:
    # (此區塊與 V3.5 相同)
    st.title("🚀 新星製造 V2 - 遊戲登入") # ... (登入介面同 V3.5) ...

# --- 登入後的畫面 ---
else:
    current_user = st.session_state.logged_in_user
    if current_user == "admin":
        # --- A. 老師畫面 ---
        display_admin_dashboard()
    elif current_user in team_list:
        # --- B. 學生畫面 (*** V3.6 強化狀態檢查 ***) ---
        team_key = current_user
        if team_key not in st.session_state.teams: st.session_state.teams[team_key] = init_team_state(team_key)
        current_team_data = st.session_state.teams[team_key]

        # --- B1. 學生側邊欄 ---
        st.sidebar.header(f"🎓 {current_team_data['team_name']} ({team_key})")
        new_team_name = st.sidebar.text_input(...)
        if new_team_name != current_team_data['team_name']: # ... (修改隊名邏輯同 V3.5) ...
            st.rerun()
        if st.sidebar.button("登出"): st.session_state.logged_in_user = None; st.rerun()

        # --- B2. 學生主畫面 ---
        display_dashboard(team_key, current_team_data)
        st.markdown("---")

        # ** V3.6 核心修改：必定從檔案讀取狀態來決定顯示 **
        # (確保 session_state 也同步一下，供學生提交邏輯使用)
        st.session_state.decisions = load_decisions_from_file()
        current_decisions_state = st.session_state.decisions # 使用同步後的 state

        if team_key in current_decisions_state:
            st.info(f"您已提交第 {st.session_state.game_season} 季的決策，請等待老師結算...")
        else:
            display_decision_form(team_key)
