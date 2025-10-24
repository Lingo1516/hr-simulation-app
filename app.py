# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V3.8 - MR Robustness)
#
# V3.8 更新：
# 1. (穩定性) 修復 AttributeError: 'dict' object has no attribute 'get'。
#    - 在結算引擎為未提交隊伍設定預設值時，在使用 team_data['MR'].get() 前，
#      強制檢查 team_data['MR'] 是否存在且為字典，否則直接使用全局預設值。

import streamlit as st
import pandas as pd
import copy
import pickle # V2.8
import os     # V2.8
import streamlit.components.v1 as components

# --- 0. (V3.1 強化) 檔案同步相關 ---
DECISIONS_FILE = "decisions_state.pkl"
# ... (load/save/delete 函數同 V3.7) ...
def save_decisions_to_file(decisions_dict): # ... (同 V3.7) ...
def load_decisions_from_file(): # ... (同 V3.7) ...
def delete_decisions_file(): # ... (同 V3.7) ...

# --- 1. 遊戲參數 (V2 升級版) ---
GLOBAL_PARAMS = {
    # ... (參數內容同 V3.7) ...
    'factory_cost': 5000000,'factory_maintenance': 100000,'factory_capacity': 8,
    'line_p1_cost': 1000000,'line_p1_maintenance': 20000,'line_p1_capacity': 1000,
    'raw_material_cost_R1': 100,'p1_labor_cost': 50,'p1_material_needed_R1': 1,'p1_depreciation_per_line': 10000,
    'line_p2_cost': 1200000,'line_p2_maintenance': 25000,'line_p2_capacity': 800,
    'raw_material_cost_R2': 150,'p2_labor_cost': 70,'p2_material_needed_R2': 1,'p2_depreciation_per_line': 12000,
    'bank_loan_interest_rate_per_season': 0.02,'emergency_loan_interest_rate': 0.05,'tax_rate': 0.20,
    'rd_costs_to_level_up': {2: 500000, 3: 1500000, 4: 3500000, 5: 6500000}
}
# V3.8 新增預設值常量
DEFAULT_PRICE_P1 = 300
DEFAULT_AD_P1 = 50000
DEFAULT_PRICE_P2 = 450
DEFAULT_AD_P2 = 50000

# --- 2. (V2.2 安全升級) 密碼系統 ---
PASSWORDS = {
    # ... (密碼內容同 V3.7) ...
    "admin": "admin123", "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660", "第 7 組": "ice112",
    "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# --- 3. 團隊狀態初始化 (V2.3) ---
def init_team_state(team_key):
    # (此函數與 V3.7 版本完全相同)
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
        'MR': {'price_p1': DEFAULT_PRICE_P1, 'ad_p1': DEFAULT_AD_P1, 'sales_units_p1': 0, 'market_share_p1': 0.0, # V3.8 使用常量
               'price_p2': DEFAULT_PRICE_P2, 'ad_p2': DEFAULT_AD_P2, 'sales_units_p2': 0, 'market_share_p2': 0.0,}
    }

# --- 3.1 (V2.5) 資產負債表平衡函數 ---
def balance_bs(bs_data):
    # (此函數與 V3.7 版本完全相同)
    bs_data['total_assets'] = bs_data.get('cash',0) + bs_data.get('inventory_value',0) + bs_data.get('fixed_assets_value',0) - bs_data.get('accumulated_depreciation',0)
    bs_data['total_liabilities_and_equity'] = bs_data.get('bank_loan',0) + bs_data.get('shareholder_equity',0)
    if abs(bs_data['total_assets'] - bs_data['total_liabilities_and_equity']) > 1:
        diff = bs_data['total_assets'] - bs_data['total_liabilities_and_equity']
        bs_data['shareholder_equity'] += diff
        bs_data['total_liabilities_and_equity'] = bs_data['total_assets']
    return bs_data

# --- 4. 儀表板 (Dashboard V2) (V2.4 格式化) ---
def display_dashboard(team_key, team_data):
    # (此函數與 V3.7 版本完全相同)
    st.header(f"📈 {team_data['team_name']} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data['BS']; is_data = team_data['IS']; mr = team_data['MR']
    tab1, tab2, tab3 = st.tabs(["📊 市場報告 (上季)", "💰 損益表 (上季)", "🏦 資產負債表 (當前)"])
    # ... (tab1, tab2, tab3 內容同 V3.7) ...

# --- 5. 決策表單 (Decision Form V2) (V3.7 修改提交邏輯) ---
def display_decision_form(team_key):
    # (此函數與 V3.7 版本完全相同)
    team_data = st.session_state.teams[team_key]
    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_data['team_name']} ({team_key}) - 第 {st.session_state.game_season} 季決策單")
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs([...])
        # ... (各 Tab 內容同 V3.7) ...
        submitted = st.form_submit_button("提交本季決策")
        if submitted:
            # (檢查邏輯與 V3.7 相同)
            if ...: st.error(...) ; return
            if ...: st.error(...) ; return
            if ...: st.error(...) ; return
            decision_data = { ... } # 收集決策
            all_decisions = load_decisions_from_file() # 讀檔
            all_decisions[team_key] = decision_data    # 更新
            save_decisions_to_file(all_decisions)      # 寫檔
            st.success(...) ; st.rerun()

# --- 6. 結算引擎 (*** V3.8 修正預設值邏輯 ***) ---
def run_season_calculation():
    """V3.8 結算引擎，修正預設值邏輯 + 穩定性"""

    teams = st.session_state.teams
    current_decisions_from_file = load_decisions_from_file() # 必定讀檔
    final_decisions = {}

    for team_key in team_list:
        if team_key not in teams: st.session_state.teams[team_key] = init_team_state(team_key)
        team_data = teams[team_key]
        if team_key in current_decisions_from_file:
            final_decisions[team_key] = current_decisions_from_file[team_key]
        else: # 預設懲罰
            st.warning(f"警告：{team_data['team_name']} ({team_key}) 未提交決策，將使用預設。")
            # --- V3.8 修正：在使用 get 前先檢查 MR 是否為 dict ---
            mr_data = team_data.get('MR', {}) # 先安全地獲取 MR，如果不存在則給空字典
            if not isinstance(mr_data, dict): # 如果 MR 不是字典 (狀態損壞)
                st.error(f"偵測到 {team_key} 的 MR 數據結構錯誤，將使用全局預設市場決策。")
                mr_data = {} # 重置為空字典，強制使用下面的全局預設

            final_decisions[team_key] = {
                'price_p1': mr_data.get('price_p1', DEFAULT_PRICE_P1), # 從 mr_data 安全地 get
                'ad_p1': mr_data.get('ad_p1', DEFAULT_AD_P1),
                'price_p2': mr_data.get('price_p2', DEFAULT_PRICE_P2),
                'ad_p2': mr_data.get('ad_p2', DEFAULT_AD_P2),
                'rd_p1': 0, 'rd_p2': 0, 'produce_p1': 0, 'produce_p2': 0,
                'buy_r1': 0, 'buy_r2': 0, 'build_factory': 0,
                'build_line_p1': 0, 'build_line_p2': 0, 'loan': 0, 'repay': 0
            }
            # --- V3.8 修正結束 ---

    # === 階段 1: 結算支出、生產、研發 (V3.2 修正) ===
    # (此階段邏輯與 V3.7 相同)
    for team_key, decision in final_decisions.items(): # ... (結算邏輯同 V3.7, 含研發檢查) ...
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
    # (此階段邏輯與 V3.7 相同)
    for team_key, team_data in teams.items(): # ... (結算邏輯同 V3.7) ...
        bs = balance_bs(bs) # V2.5
        # === 階段 4: 緊急貸款 (破產檢查) ===
        if bs['cash'] < 0: # ... (結算邏輯同 V3.7) ...
            bs = balance_bs(bs) # V2.5
        team_data['BS'] = bs; team_data['IS'] = is_data # 存回 state
    # === 階段 5: 推進遊戲 (V3.7) ===
    st.session_state.game_season += 1
    # st.session_state.decisions = {} # V3.7 移除
    delete_decisions_file() # 只刪除檔案
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")


# --- 7. (V2.5 修改) 老師專用函式 (V3.6) ---
def calculate_company_value(bs_data):
    # (此函數與 V3.7 版本完全相同)
    value = bs_data.get('cash', 0) + bs_data.get('inventory_value', 0) + \
            (bs_data.get('fixed_assets_value', 0) - bs_data.get('accumulated_depreciation', 0)) - \
            bs_data.get('bank_loan', 0)
    return value

def display_admin_dashboard():
    """顯示老師的控制台畫面"""
    st.header(f"👨‍🏫 管理員控制台 (第 {st.session_state.game_season} 季)")
    # --- 學生密碼總覽 ---
    with st.expander("🔑 學生密碼總覽"): # ... (內容同 V3.7) ...
    # --- 修改團隊數據 ---
    with st.expander("🔧 修改團隊數據 (Edit Team Data)"): # ... (內容同 V3.7) ...
    # --- A. 排行榜 (V2.4 格式化) ---
    st.subheader("遊戲排行榜 (依公司總價值)") # ... (內容同 V3.7) ...
    # --- B. 監控面板 (V3.7 只依賴檔案) ---
    st.subheader("本季決策提交狀態") # ... (內容同 V3.7) ...
    # --- C. 控制按鈕 (V3.7) ---
    st.subheader("遊戲控制") # ... (內容同 V3.7) ...

# --- 8. 主程式 (Main App) (V3.7) ---
st.set_page_config(layout="wide")

# --- 初始化 session_state ---
if 'game_season' not in st.session_state:
    st.session_state.game_season = 1
    st.session_state.teams = {}
    # V3.7 不再需要 decisions 初始化
    st.session_state.logged_in_user = None

# --- 登入邏जिक ---
if st.session_state.logged_in_user is None:
    # (此區塊與 V3.7 相同)
    st.title("🚀 新星製造 V2 - 遊戲登入") # ... (登入介面同 V3.7) ...

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
        current_team_data = st.session_state.teams[team_key]

        # --- B1. 學生側邊欄 ---
        st.sidebar.header(f"🎓 {current_team_data['team_name']} ({team_key})")
        new_team_name = st.sidebar.text_input(...)
        if new_team_name != current_team_data['team_name']: # ... (修改隊名邏輯同 V3.7) ...
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
