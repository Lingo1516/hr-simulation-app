# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V3.9 - Ultimate Type Stability)
#
# V3.9 更新：
# 1. (根本性修正) 在結算引擎迴圈入口，強制檢查 team_data 和 decision 是否為字典，
#    防止因意外的數據類型錯誤 (如變成數字 0) 導致 KeyError 或 AttributeError。

import streamlit as st
import pandas as pd
import copy
import pickle # V2.8
import os     # V2.8
import streamlit.components.v1 as components

# --- 0. (V3.1 強化) 檔案同步相關 ---
DECISIONS_FILE = "decisions_state.pkl"
# ... (load/save/delete 函數同 V3.8) ...
def save_decisions_to_file(decisions_dict): # ... (同 V3.8) ...
def load_decisions_from_file(): # ... (同 V3.8) ...
def delete_decisions_file(): # ... (同 V3.8) ...

# --- 1. 遊戲參數 (V2 升級版) ---
GLOBAL_PARAMS = {
    # ... (參數內容同 V3.8) ...
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
    # ... (密碼內容同 V3.8) ...
    "admin": "admin123", "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660", "第 7 組": "ice112",
    "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# --- 3. 團隊狀態初始化 (V2.3) ---
def init_team_state(team_key):
    # (此函數與 V3.8 版本完全相同)
    initial_cash = 10000000; initial_factories = 1; initial_lines_p1 = 1; initial_lines_p2 = 1
    initial_inv_r1 = 2000; initial_inv_r2 = 2000; initial_inv_p1 = 500; initial_inv_p2 = 500
    cogs_p1 = (...); cogs_p2 = (...)
    inv_value = (...); fixed_assets = (...); total_assets = (...); initial_equity = total_assets
    return { # ... (返回字典結構同 V3.8) ...
    }

# --- 3.1 (V2.5) 資產負債表平衡函數 ---
def balance_bs(bs_data):
    # (此函數與 V3.8 版本完全相同)
    bs_data['total_assets'] = bs_data.get('cash',0) + bs_data.get('inventory_value',0) + bs_data.get('fixed_assets_value',0) - bs_data.get('accumulated_depreciation',0)
    bs_data['total_liabilities_and_equity'] = bs_data.get('bank_loan',0) + bs_data.get('shareholder_equity',0)
    if abs(bs_data['total_assets'] - bs_data['total_liabilities_and_equity']) > 1:
        diff = bs_data['total_assets'] - bs_data['total_liabilities_and_equity']
        bs_data['shareholder_equity'] += diff
        bs_data['total_liabilities_and_equity'] = bs_data['total_assets']
    return bs_data

# --- 4. 儀表板 (Dashboard V2) (V2.4 格式化) ---
def display_dashboard(team_key, team_data):
    # (此函數與 V3.8 版本完全相同)
    st.header(f"📈 {team_data['team_name']} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data.get('BS', {}); is_data = team_data.get('IS', {}); mr = team_data.get('MR', {}) # V3.9 使用 get 防禦
    tab1, tab2, tab3 = st.tabs(["📊 市場報告 (上季)", "💰 損益表 (上季)", "🏦 資產負債表 (當前)"])
    # ... (tab1, tab2, tab3 內容同 V3.8, 但內部訪問字典也建議用 .get()) ...

# --- 5. 決策表單 (Decision Form V2) (V3.7 修改提交邏輯) ---
def display_decision_form(team_key):
    # (此函數與 V3.8 版本完全相同)
    team_data = st.session_state.teams[team_key]
    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_data['team_name']} ({team_key}) - 第 {st.session_state.game_season} 季決策單")
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs([...])
        # ... (各 Tab 內容同 V3.8) ...
        submitted = st.form_submit_button("提交本季決策")
        if submitted:
            # (檢查邏輯與 V3.8 相同)
            if ...: st.error(...) ; return
            if ...: st.error(...) ; return
            if ...: st.error(...) ; return
            decision_data = { ... } # 收集決策
            all_decisions = load_decisions_from_file() # 讀檔
            all_decisions[team_key] = decision_data    # 更新
            save_decisions_to_file(all_decisions)      # 寫檔
            st.success(...) ; st.rerun()

# --- 6. 結算引擎 (*** V3.9 終極類型穩定 ***) ---
def run_season_calculation():
    """V3.9 結算引擎，強制類型檢查 + 穩定性"""

    teams = st.session_state.teams
    current_decisions_from_file = load_decisions_from_file() # 必定讀檔
    final_decisions = {}

    for team_key in team_list:
        if team_key not in teams: st.session_state.teams[team_key] = init_team_state(team_key)
        team_data = teams.get(team_key) # V3.9 使用 get

        # *** V3.9 強制檢查 team_data ***
        if not isinstance(team_data, dict):
            st.error(f"嚴重錯誤：隊伍 {team_key} 的數據損壞，本季無法結算該隊伍。")
            continue # 跳過這個損壞的隊伍

        if team_key in current_decisions_from_file:
            # *** V3.9 強制檢查 decision ***
            decision_data = current_decisions_from_file[team_key]
            if not isinstance(decision_data, dict):
                st.error(f"嚴重錯誤：隊伍 {team_key} 的決策數據損壞，將使用預設。")
                decision_data = {} # 使用空字典觸發下方預設邏輯
            else:
                final_decisions[team_key] = decision_data
        else: # 預設懲罰 (邏輯同 V3.8)
            st.warning(f"警告：{team_data.get('team_name', team_key)} ({team_key}) 未提交決策，將使用預設。")
            mr_data = team_data.get('MR', {})
            if not isinstance(mr_data, dict): mr_data = {} # V3.8 修正
            final_decisions[team_key] = {
                'price_p1': mr_data.get('price_p1', DEFAULT_PRICE_P1),
                'ad_p1': mr_data.get('ad_p1', DEFAULT_AD_P1),
                'price_p2': mr_data.get('price_p2', DEFAULT_PRICE_P2),
                'ad_p2': mr_data.get('ad_p2', DEFAULT_AD_P2),
                'rd_p1': 0, 'rd_p2': 0, 'produce_p1': 0, 'produce_p2': 0,
                'buy_r1': 0, 'buy_r2': 0, 'build_factory': 0,
                'build_line_p1': 0, 'build_line_p2': 0, 'loan': 0, 'repay': 0
            }

        # *** V3.9 如果 decision_data 在上面檢查後變空字典，也要加入 final_decisions ***
        if team_key not in final_decisions:
             final_decisions[team_key] = { # 同上預設懲罰
                'price_p1': mr_data.get('price_p1', DEFAULT_PRICE_P1), # ... 其他 ...
             }


    # === 階段 1: 結算支出、生產、研發 (*** V3.9 強化 ***) ===
    for team_key, decision in final_decisions.items():
        team_data = teams.get(team_key)
        # *** V3.9 再次檢查 team_data 和 decision ***
        if not isinstance(team_data, dict): continue # 跳過損壞隊伍
        if not isinstance(decision, dict): # 如果 decision 意外損壞 (理論上不會到這)
            st.error(f"結算錯誤：隊伍 {team_key} 的決策數據在處理中損壞。")
            decision = {} # 使用空字典避免崩潰，等同 0 投入

        bs = team_data.get('BS', {}) # V3.9 使用 get
        is_data = {k: 0 for k in init_team_state('temp')['IS']} # V3.9 使用標準模板重置

        # (後續計算同 V3.8, 但大量使用 .get() 提高穩定性)
        is_data['interest_expense'] = bs.get('bank_loan', 0) * GLOBAL_PARAMS['bank_loan_interest_rate_per_season']
        maint_cost = (team_data.get('factories', 0) * GLOBAL_PARAMS['factory_maintenance']) + \
                     (team_data.get('lines_p1', 0) * GLOBAL_PARAMS['line_p1_maintenance']) + \
                     (team_data.get('lines_p2', 0) * GLOBAL_PARAMS['line_p2_maintenance'])
        is_data['op_expense_maintenance'] = maint_cost
        capex_cost = (decision.get('build_factory', 0) * GLOBAL_PARAMS['factory_cost']) + \
                     (decision.get('build_line_p1', 0) * GLOBAL_PARAMS['line_p1_cost']) + \
                     (decision.get('build_line_p2', 0) * GLOBAL_PARAMS['line_p2_cost'])
        buy_R1_cost = decision.get('buy_r1', 0) * GLOBAL_PARAMS['raw_material_cost_R1']
        buy_R2_cost = decision.get('buy_r2', 0) * GLOBAL_PARAMS['raw_material_cost_R2']
        # ... (生產計算同 V3.8, 但內部訪問 team_data 也用 .get()) ...
        actual_prod_p1 = int(min(decision.get('produce_p1',0), ...))
        actual_prod_p2 = int(min(decision.get('produce_p2',0), ...))
        # ...
        is_data['op_expense_ads'] = decision.get('ad_p1', 0) + decision.get('ad_p2', 0)
        is_data['op_expense_rd'] = decision.get('rd_p1', 0) + decision.get('rd_p2', 0)
        depr_cost = (...); is_data['depreciation_expense'] = depr_cost
        total_cash_out = (...)
        bs['cash'] = bs.get('cash', 0) - total_cash_out + decision.get('loan', 0) # V3.9 使用 get
        # ... (資產庫存更新同 V3.8, 但使用 .get() 防禦) ...
        team_data['factories'] = team_data.get('factories', 0) + decision.get('build_factory', 0)
        # ... (研發計算同 V3.8, 含邊界檢查) ...
        team_data['MR']['price_p1'] = decision.get('price_p1', DEFAULT_PRICE_P1) # V3.9 使用 get
        # ... (更新 MR 和 IS) ...
        team_data['IS'] = is_data # 存回 state

    # === 階段 2: 市場結算 (V3.5 修正) ===
    # (此階段邏輯與 V3.5 相同，包含數值檢查)
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
        bs = balance_bs(team_data.get('BS', {})) # V3.9 使用 get
        # === 階段 4: 緊急貸款 (破產檢查) ===
        if bs.get('cash', 0) < 0: # V3.9 使用 get
             # ... (結算邏輯同 V3.5) ...
            bs = balance_bs(bs) # V2.5
        # V3.9 確保存回的是字典
        team_data['BS'] = bs if isinstance(bs, dict) else {}
        team_data['IS'] = is_data if isinstance(is_data, dict) else {}

    # === 階段 5: 推進遊戲 (V3.7) ===
    st.session_state.game_season += 1
    # st.session_state.decisions = {} # V3.7 移除
    delete_decisions_file() # 只刪除檔案
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")


# --- 7. (V2.5 修改) 老師專用函式 (V3.6) ---
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
        # --- B. 學生畫面 (V3.7 只依賴檔案) ---
        team_key = current_user
        if team_key not in st.session_state.teams: st.session_state.teams[team_key] = init_team_state(team_key)
        # V3.9 安全獲取
        current_team_data = st.session_state.teams.get(team_key, init_team_state(team_key))

        # --- B1. 學生側邊欄 ---
        st.sidebar.header(f"🎓 {current_team_data.get('team_name', team_key)} ({team_key})") # V3.9 .get()
        new_team_name = st.sidebar.text_input("修改您的隊伍名稱：", value=current_team_data.get('team_name', team_key)) # V3.9 .get()
        if new_team_name != current_team_data.get('team_name', team_key): # V3.9 .get()
            if not new_team_name.strip(): st.sidebar.error("隊伍名稱不能為空！")
            else: # V3.9 確保 teams[team_key] 存在
                if team_key in st.session_state.teams:
                     st.session_state.teams[team_key]['team_name'] = new_team_name
                     st.sidebar.success("隊伍名稱已更新！"); st.rerun()
                else:
                     st.sidebar.error("發生錯誤，無法更新隊名。")

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
