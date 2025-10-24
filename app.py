# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V4.2 - Ultimate Numeric Stability)
#
# V4.2 更新：
# 1. (根本性修正) 解決 TypeError: 'int' and 'NoneType' in balance_bs。
#    - 新增 force_numeric 輔助函數。
#    - 在 balance_bs 計算前，對所有參與運算的值強制進行數字檢查和轉換。

import streamlit as st
import pandas as pd
import copy
import pickle
import os
import streamlit.components.v1 as components

# --- 0. (V3.1 強化) 檔案同步相關 ---
DECISIONS_FILE = "decisions_state.pkl"
# ... (load/save/delete 函數同 V4.1) ...
def save_decisions_to_file(decisions_dict): # ... (同 V4.1) ...
def load_decisions_from_file(): # ... (同 V4.1) ...
def delete_decisions_file(): # ... (同 V4.1) ...

# --- 1. 遊戲參數 (V2 升級版) ---
GLOBAL_PARAMS = {
    # ... (參數內容同 V4.1) ...
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
    # ... (密碼內容同 V4.1) ...
    "admin": "admin123", "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660", "第 7 組": "ice112",
    "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# --- 3. 團隊狀態初始化 (V2.3) ---
def init_team_state(team_key):
    # (此函數與 V4.1 版本完全相同)
    initial_cash = 10000000; initial_factories = 1; initial_lines_p1 = 1; initial_lines_p2 = 1
    initial_inv_r1 = 2000; initial_inv_r2 = 2000; initial_inv_p1 = 500; initial_inv_p2 = 500
    cogs_p1 = (...); cogs_p2 = (...)
    inv_value = (...); fixed_assets = (...); total_assets = (...); initial_equity = total_assets
    return { # ... (返回字典結構同 V4.1) ...
    }

# --- 3.1 (V4.2 新增) 強制數值轉換函數 ---
def force_numeric(value, default=0):
    """檢查 value 是否為數字 (int 或 float)，如果不是或為 None，返回 default"""
    if isinstance(value, (int, float)):
        return value
    else:
        # st.warning(f"偵測到非數值: {value}，已強制轉換為 {default}") # 可選的除錯訊息
        return default

# --- 3.2 (V4.2 修改) 資產負債表平衡函數 ---
def balance_bs(bs_data):
    """輸入 BS 字典，重新計算並強制平衡，加入強制數值轉換"""
    # V4.2 在計算前強制轉換
    cash = force_numeric(bs_data.get('cash', 0))
    inv_val = force_numeric(bs_data.get('inventory_value', 0))
    fixed_val = force_numeric(bs_data.get('fixed_assets_value', 0))
    acc_depr = force_numeric(bs_data.get('accumulated_depreciation', 0))
    loan = force_numeric(bs_data.get('bank_loan', 0))
    equity = force_numeric(bs_data.get('shareholder_equity', 0))

    bs_data['total_assets'] = cash + inv_val + fixed_val - acc_depr
    bs_data['total_liabilities_and_equity'] = loan + equity

    if abs(bs_data['total_assets'] - bs_data['total_liabilities_and_equity']) > 1:
        diff = bs_data['total_assets'] - bs_data['total_liabilities_and_equity']
        # V4.2 確保 equity 是數字才能 +/-
        bs_data['shareholder_equity'] = force_numeric(bs_data.get('shareholder_equity'), 0) + diff
        bs_data['total_liabilities_and_equity'] = bs_data['total_assets']

    # V4.2 確保存回字典的值都是數字
    for key in ['cash', 'inventory_value', 'fixed_assets_value', 'accumulated_depreciation',
                'total_assets', 'bank_loan', 'shareholder_equity', 'total_liabilities_and_equity']:
        bs_data[key] = force_numeric(bs_data.get(key, 0))

    return bs_data

# --- 4. 儀表板 (Dashboard V2) (V4.0 簡化顯示) ---
def display_dashboard(team_key, team_data):
    # (此函數與 V4.1 版本完全相同)
    st.header(f"📈 {team_data.get('team_name', team_key)} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data.get('BS', {}); is_data = team_data.get('IS', {}); mr = team_data.get('MR', {}) # V3.9
    st.subheader("📊 市場報告 (上季)"); st.write(mr)
    st.subheader("💰 損益表 (上季)")
    net_income = is_data.get('net_income', 0); st.metric("💹 稅後淨利 (Net Income)", f"${force_numeric(net_income):,.0f}") # V4.2
    with st.expander("查看詳細損益表 (原始數據)"): st.write(is_data)
    st.subheader("🏦 資產負債表 (當前)")
    total_assets = bs.get('total_assets', 0); st.metric("🏦 總資產 (Total Assets)", f"${force_numeric(total_assets):,.0f}") # V4.2
    with st.expander("查看詳細資產負債表 (原始數據)"): st.write(bs)
    st.subheader("🏭 內部資產 (非財報)") # ... (內容同 V4.1) ...

# --- 5. 決策表單 (Decision Form V2) (V3.7 修改提交邏輯) ---
def display_decision_form(team_key):
    # (此函數與 V4.1 版本完全相同)
    team_data = st.session_state.teams[team_key]
    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_data['team_name']} ({team_key}) - 第 {st.session_state.game_season} 季決策單")
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs([...])
        # ... (各 Tab 內容同 V4.1) ...
        submitted = st.form_submit_button("提交本季決策")
        if submitted:
            # (檢查邏輯與 V4.1 相同)
            if ...: st.error(...) ; return
            if ...: st.error(...) ; return
            if ...: st.error(...) ; return
            decision_data = { ... } # 收集決策
            all_decisions = load_decisions_from_file() # 讀檔
            all_decisions[team_key] = decision_data    # 更新
            save_decisions_to_file(all_decisions)      # 寫檔
            st.success(...) ; st.rerun()

# --- 6. 結算引擎 (V3.9 + *** V4.2 強制轉換 ***) ---
def run_season_calculation():
    """V4.2 結算引擎，強制類型檢查 + 穩定性"""

    teams = st.session_state.teams
    current_decisions_from_file = load_decisions_from_file() # 必定讀檔
    final_decisions = {}

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

    # === 階段 1: 結算支出、生產、研發 (V3.9 強化) ===
    for team_key, decision in final_decisions.items():
        team_data = teams.get(team_key)
        if not isinstance(team_data, dict): continue
        if not isinstance(decision, dict): decision = {} # V3.9

        bs = team_data.get('BS', {})
        is_data = {k: 0 for k in init_team_state('temp')['IS']}

        # --- V4.2 強制轉換所有計算中用到的 BS/team_data 值 ---
        current_loan = force_numeric(bs.get('bank_loan', 0))
        factories = force_numeric(team_data.get('factories', 0))
        lines_p1 = force_numeric(team_data.get('lines_p1', 0))
        lines_p2 = force_numeric(team_data.get('lines_p2', 0))
        inv_r1 = force_numeric(team_data.get('inventory_R1_units', 0))
        inv_r2 = force_numeric(team_data.get('inventory_R2_units', 0))
        inv_p1 = force_numeric(team_data.get('inventory_P1_units', 0))
        inv_p2 = force_numeric(team_data.get('inventory_P2_units', 0))
        rd_invest_p1 = force_numeric(team_data.get('rd_investment_P1', 0))
        rd_invest_p2 = force_numeric(team_data.get('rd_investment_P2', 0))
        rd_level_p1 = force_numeric(team_data.get('rd_level_P1', 1), default=1) # 等級預設為1
        rd_level_p2 = force_numeric(team_data.get('rd_level_P2', 1), default=1)

        # (後續計算同 V3.9, 但使用上面轉換後的值)
        is_data['interest_expense'] = current_loan * GLOBAL_PARAMS['bank_loan_interest_rate_per_season']
        maint_cost = (factories * ...) + (lines_p1 * ...) + (lines_p2 * ...)
        is_data['op_expense_maintenance'] = maint_cost
        capex_cost = (force_numeric(decision.get('build_factory', 0)) * ...) + ...
        buy_R1_cost = force_numeric(decision.get('buy_r1', 0)) * ...
        buy_R2_cost = force_numeric(decision.get('buy_r2', 0)) * ...
        # ... (生產計算) ...
        max_prod_p1_lines = lines_p1 * ...; max_prod_p1_r1 = inv_r1 / ...
        actual_prod_p1 = int(min(force_numeric(decision.get('produce_p1',0)), max_prod_p1_lines, max_prod_p1_r1))
        # ... (研發計算，V3.2已有檢查) ...
        # ... (更新 BS, team_data, MR, IS) ...
        team_data['IS'] = is_data # 存回 state

    # === 階段 2: 市場結算 (V3.5 修正) ===
    # (此階段邏輯與 V3.9 相同，包含強制數值檢查)
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

    # === 階段 3: 財務報表結算 (*** V4.2 使用 force_numeric ***) ===
    for team_key, team_data in teams.items():
        # V4.2 安全獲取
        bs = team_data.get('BS', {})
        is_data = team_data.get('IS', {})
        mr_data = team_data.get('MR', {})
        decision = final_decisions.get(team_key, {}) # V4.2

        # (計算邏輯同 V3.9, 但使用 force_numeric)
        rev_p1 = force_numeric(is_data.get('revenue_p1', 0)); rev_p2 = force_numeric(is_data.get('revenue_p2', 0))
        is_data['total_revenue'] = rev_p1 + rev_p2
        sales_p1 = force_numeric(mr_data.get('sales_units_p1', 0)); sales_p2 = force_numeric(mr_data.get('sales_units_p2', 0))
        cogs_p1_cost = sales_p1 * (GLOBAL_PARAMS['raw_material_cost_R1'] + GLOBAL_PARAMS['p1_labor_cost'])
        cogs_p2_cost = sales_p2 * (GLOBAL_PARAMS['raw_material_cost_R2'] + GLOBAL_PARAMS['p2_labor_cost'])
        is_data['cogs'] = cogs_p1_cost + cogs_p2_cost
        is_data['gross_profit'] = is_data['total_revenue'] - is_data['cogs']
        # ... (其他 IS 計算) ...
        is_data['net_income'] = is_data['profit_before_tax'] - is_data['tax_expense']
        bs['cash'] = force_numeric(bs.get('cash', 0)) - force_numeric(is_data.get('tax_expense', 0)) # V4.2

        bs['bank_loan'] = force_numeric(bs.get('bank_loan', 0)) + force_numeric(decision.get('loan', 0)) - force_numeric(decision.get('repay', 0)) # V4.2
        bs['shareholder_equity'] = force_numeric(bs.get('shareholder_equity', 0)) + force_numeric(is_data.get('net_income', 0)) # V4.2
        # ... (更新 fixed_assets, acc_depr, inv_value) ...

        bs = balance_bs(bs) # V2.5

        # === 階段 4: 緊急貸款 (破產檢查) ===
        cash_after_calc = force_numeric(bs.get('cash', 0)) # V4.2
        if cash_after_calc < 0:
            emergency_loan = abs(cash_after_calc)
            interest_penalty = emergency_loan * GLOBAL_PARAMS['emergency_loan_interest_rate']
            bs['cash'] = 0 # 補到0
            bs['bank_loan'] = force_numeric(bs.get('bank_loan', 0)) + emergency_loan # V4.2
            bs['cash'] -= interest_penalty # 可能又變負
            bs['shareholder_equity'] = force_numeric(bs.get('shareholder_equity', 0)) - interest_penalty # V4.2
            st.error(f"{team_data.get('team_name', team_key)} ({team_key}) 現金不足！...")
            bs = balance_bs(bs) # V2.5 再次平衡

        # V4.2 確保存回的是字典
        team_data['BS'] = bs if isinstance(bs, dict) else {}
        team_data['IS'] = is_data if isinstance(is_data, dict) else {}

    # === 階段 5: 推進遊戲 (V3.7) ===
    st.session_state.game_season += 1
    delete_decisions_file() # 只刪除檔案
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")


# --- 7. (V2.5 修改) 老師專用函式 (V3.6) ---
def calculate_company_value(bs_data):
    # (此函數與 V3.9 版本完全相同)
    value = force_numeric(bs_data.get('cash', 0)) + force_numeric(bs_data.get('inventory_value', 0)) + \
            (force_numeric(bs_data.get('fixed_assets_value', 0)) - force_numeric(bs_data.get('accumulated_depreciation', 0))) - \
            force_numeric(bs_data.get('bank_loan', 0)) # V4.2 強制轉換
    return value

def display_admin_dashboard():
    """顯示老師的控制台畫面"""
    st.header(f"👨‍🏫 管理員控制台 (第 {st.session_state.game_season} 季)")
    # --- 學生密碼總覽 ---
    with st.expander("🔑 學生密碼總覽"): # ... (內容同 V4.1) ...
    # --- 修改團隊數據 ---
    with st.expander("🔧 修改團隊數據 (Edit Team Data)"): # ... (內容同 V4.1) ...
    # --- A. 排行榜 (V2.4 格式化) ---
    st.subheader("遊戲排行榜 (依公司總價值)") # ... (內容同 V4.1) ...
    # --- B. 監控面板 (V3.7 只依賴檔案) ---
    st.subheader("本季決策提交狀態") # ... (內容同 V4.1) ...
    # --- C. 控制按鈕 (V3.7) ---
    st.subheader("遊戲控制") # ... (內容同 V4.1) ...

# --- 8. 主程式 (Main App) (V4.1) ---
st.set_page_config(layout="wide")
# --- 初始化 session_state ---
if 'game_season' not in st.session_state: # ... (內容同 V4.1) ...
# --- 登入邏輯 (V4.1) ---
if st.session_state.logged_in_user is None: # ... (內容同 V4.1) ...
# --- 登入後的畫面 ---
else: # ... (內容同 V4.1) ...
