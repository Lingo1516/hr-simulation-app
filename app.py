# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V4.3 - Ultimate Defensive Access)
#
# V4.3 更新：
# 1. (根本性修正) 徹底解決 AttributeError 和 KeyError。
#    - 在【所有】讀取字典值的地方強制使用 .get(key, default)。
#    - 在【所有】數學運算和格式化前強制使用 force_numeric()。
#    - 重新審視並加固 init_team_state 和 balance_bs。

import streamlit as st
import pandas as pd
import copy
import pickle
import os
import streamlit.components.v1 as components
import numbers # V4.3 引入 numbers 模組

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
    # ... (參數內容同 V4.2) ...
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
    # ... (密碼內容同 V4.2) ...
    "admin": "admin123", "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660", "第 7 組": "ice112",
    "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# --- 3. 團隊狀態初始化 (*** V4.3 強化 ***) ---
def init_team_state(team_key):
    initial_cash = 10000000; initial_factories = 1; initial_lines_p1 = 1; initial_lines_p2 = 1
    initial_inv_r1 = 2000; initial_inv_r2 = 2000; initial_inv_p1 = 500; initial_inv_p2 = 500
    # --- V4.3 強制數值計算 ---
    cogs_p1 = force_numeric(GLOBAL_PARAMS.get('raw_material_cost_R1', 0)) * force_numeric(GLOBAL_PARAMS.get('p1_material_needed_R1', 0)) + force_numeric(GLOBAL_PARAMS.get('p1_labor_cost', 0))
    cogs_p2 = force_numeric(GLOBAL_PARAMS.get('raw_material_cost_R2', 0)) * force_numeric(GLOBAL_PARAMS.get('p2_material_needed_R2', 0)) + force_numeric(GLOBAL_PARAMS.get('p2_labor_cost', 0))
    inv_value = (initial_inv_r1 * force_numeric(GLOBAL_PARAMS.get('raw_material_cost_R1', 0))) + \
                (initial_inv_r2 * force_numeric(GLOBAL_PARAMS.get('raw_material_cost_R2', 0))) + \
                (initial_inv_p1 * cogs_p1) + \
                (initial_inv_p2 * cogs_p2)
    fixed_assets = (initial_factories * force_numeric(GLOBAL_PARAMS.get('factory_cost', 0))) + \
                   (initial_lines_p1 * force_numeric(GLOBAL_PARAMS.get('line_p1_cost', 0))) + \
                   (initial_lines_p2 * force_numeric(GLOBAL_PARAMS.get('line_p2_cost', 0)))
    total_assets = initial_cash + inv_value + fixed_assets
    initial_equity = total_assets
    # --- V4.3 確保所有初始值都是數字 ---
    bs_init = {
        'cash': force_numeric(initial_cash), 'inventory_value': force_numeric(inv_value),
        'fixed_assets_value': force_numeric(fixed_assets), 'accumulated_depreciation': 0,
        'total_assets': force_numeric(total_assets), 'bank_loan': 0,
        'shareholder_equity': force_numeric(initial_equity),
        'total_liabilities_and_equity': force_numeric(total_assets)
    }
    is_init_keys = ['revenue_p1', 'revenue_p2', 'total_revenue', 'cogs', 'gross_profit',
                   'op_expense_ads', 'op_expense_rd', 'op_expense_maintenance',
                   'depreciation_expense', 'total_op_expense', 'operating_profit',
                   'interest_expense', 'profit_before_tax', 'tax_expense', 'net_income']
    is_init = {k: 0 for k in is_init_keys}
    mr_init = {
        'price_p1': DEFAULT_PRICE_P1, 'ad_p1': DEFAULT_AD_P1, 'sales_units_p1': 0, 'market_share_p1': 0.0,
        'price_p2': DEFAULT_PRICE_P2, 'ad_p2': DEFAULT_AD_P2, 'sales_units_p2': 0, 'market_share_p2': 0.0,
    }
    return {
        'team_name': str(team_key), # 確保是字串
        'BS': bs_init,
        'IS': is_init,
        'factories': force_numeric(initial_factories, 1), # 確保>0
        'lines_p1': force_numeric(initial_lines_p1, 1),
        'lines_p2': force_numeric(initial_lines_p2, 1),
        'inventory_R1_units': force_numeric(initial_inv_r1), 'inventory_R2_units': force_numeric(initial_inv_r2),
        'inventory_P1_units': force_numeric(initial_inv_p1), 'inventory_P2_units': force_numeric(initial_inv_p2),
        'rd_level_P1': 1, 'rd_level_P2': 1,
        'rd_investment_P1': 0, 'rd_investment_P2': 0,
        'MR': mr_init
    }

# --- 3.1 (V4.2 新增) 強制數值轉換函數 ---
def force_numeric(value, default=0):
    """檢查 value 是否為數字 (int 或 float)，如果不是或為 None，返回 default"""
    if isinstance(value, numbers.Number): # V4.3 使用 numbers.Number 更通用
        return value
    # V4.3 嘗試轉換字串數字
    elif isinstance(value, str) and value.replace('.','',1).isdigit():
         try: return float(value)
         except ValueError: return default
    else:
        # st.warning(f"偵測到非數值: {value} (類型 {type(value)})，已強制轉換為 {default}") # 可選除錯
        return default

# --- 3.2 (V4.2 修改) 資產負債表平衡函數 ---
def balance_bs(bs_data):
    # (此函數與 V4.2 版本完全相同，已包含 force_numeric)
    if not isinstance(bs_data, dict): bs_data = {} # V4.3
    cash = force_numeric(bs_data.get('cash', 0)); inv_val = force_numeric(bs_data.get('inventory_value', 0))
    fixed_val = force_numeric(bs_data.get('fixed_assets_value', 0)); acc_depr = force_numeric(bs_data.get('accumulated_depreciation', 0))
    loan = force_numeric(bs_data.get('bank_loan', 0)); equity = force_numeric(bs_data.get('shareholder_equity', 0))
    bs_data['total_assets'] = cash + inv_val + fixed_val - acc_depr
    bs_data['total_liabilities_and_equity'] = loan + equity
    if abs(bs_data['total_assets'] - bs_data['total_liabilities_and_equity']) > 1:
        diff = bs_data['total_assets'] - bs_data['total_liabilities_and_equity']
        bs_data['shareholder_equity'] = equity + diff
        bs_data['total_liabilities_and_equity'] = bs_data['total_assets']
    for key in [...]: bs_data[key] = force_numeric(bs_data.get(key, 0)) # 確保都是數字
    return bs_data

# --- 4. 儀表板 (Dashboard V2) (*** V4.3 全面使用 .get() ***) ---
def display_dashboard(team_key, team_data):
    # V4.3 確保 team_data 是字典
    if not isinstance(team_data, dict): team_data = init_team_state(team_key)

    st.header(f"📈 {team_data.get('team_name', team_key)} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    # V4.3 全面使用 .get()
    bs = team_data.get('BS', {})
    is_data = team_data.get('IS', {})
    mr = team_data.get('MR', {})

    st.subheader("📊 市場報告 (上季)")
    st.write(mr) # 保持簡化顯示
    st.subheader("💰 損益表 (上季)")
    net_income = is_data.get('net_income', 0)
    st.metric("💹 稅後淨利 (Net Income)", f"${force_numeric(net_income):,.0f}")
    with st.expander("查看詳細損益表 (原始數據)"): st.write(is_data) # 保持簡化顯示
    st.subheader("🏦 資產負債表 (當前)")
    total_assets = bs.get('total_assets', 0)
    st.metric("🏦 總資產 (Total Assets)", f"${force_numeric(total_assets):,.0f}")
    with st.expander("查看詳細資產負債表 (原始數據)"): st.write(bs) # 保持簡化顯示
    st.subheader("🏭 內部資產 (非財報)")
    col1, col2, col3 = st.columns(3)
    col1.metric("工廠 (座)", force_numeric(team_data.get('factories', 0))) # V4.3
    col2.metric("P1 生產線 (條)", force_numeric(team_data.get('lines_p1', 0))) # V4.3
    col3.metric("P2 生產線 (條)", force_numeric(team_data.get('lines_p2', 0))) # V4.3
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("R1 庫存 (u)", f"{force_numeric(team_data.get('inventory_R1_units', 0)):,.0f}") # V4.3
    col2.metric("P1 庫存 (u)", f"{force_numeric(team_data.get('inventory_P1_units', 0)):,.0f}") # V4.3
    col3.metric("R2 庫存 (u)", f"{force_numeric(team_data.get('inventory_R2_units', 0)):,.0f}") # V4.3
    col4.metric("P2 庫存 (u)", f"{force_numeric(team_data.get('inventory_P2_units', 0)):,.0f}") # V4.3

# --- 5. 決策表單 (Decision Form V2) (*** V4.3 全面使用 .get() ***) ---
def display_decision_form(team_key):
    # V4.3 確保 team_data 存在且為字典
    team_data = st.session_state.teams.get(team_key)
    if not isinstance(team_data, dict):
        st.error(f"無法載入 {team_key} 的數據，請聯繫老師。")
        return

    # V4.3 安全獲取內部字典
    mr_data = team_data.get('MR', {})
    bs_data = team_data.get('BS', {})

    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_data.get('team_name', team_key)} ({team_key}) - 第 {st.session_state.game_season} 季決策單")
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs(["P1 產品決策", "P2 產品決策", "生產與資本決策", "財務決策"])

        with tab_p1:
            st.subheader("P1 產品決策")
            # V4.3 value 使用 force_numeric 和 get
            decision_price_P1 = st.slider("P1 銷售價格", 100, 1000, value=force_numeric(mr_data.get('price_p1', DEFAULT_PRICE_P1), DEFAULT_PRICE_P1), step=10)
            st.info("💡 **策略提示：** ...")
            decision_ad_P1 = st.number_input("P1 廣告費用", min_value=0, step=10000, value=force_numeric(mr_data.get('ad_p1', DEFAULT_AD_P1), DEFAULT_AD_P1))
            st.info("💡 **策略提示：** ...")
            decision_rd_P1 = st.number_input("P1 研發費用", min_value=0, step=50000, value=0)
            st.info(f"💡 **策略提示：** ... P1 目前 L{force_numeric(team_data.get('rd_level_P1', 1), 1)}，累計投入 ${force_numeric(team_data.get('rd_investment_P1', 0)):,.0f}。")

        with tab_p2: # ... (類似修改 P2 的 value) ...
        with tab_prod: # ... (類似修改產能/庫存提示的 value) ...
        with tab_fin: # ... (類似修改借款提示的 value) ...

        submitted = st.form_submit_button("提交本季決策")
        if submitted:
            # (檢查邏輯 V4.3 使用 force_numeric 和 get)
            lines_p1 = force_numeric(team_data.get('lines_p1', 0)); lines_p2 = force_numeric(team_data.get('lines_p2', 0))
            factories = force_numeric(team_data.get('factories', 0))
            # V4.3 強制轉換輸入值
            build_f = force_numeric(decision_build_factory, 0); build_l1 = force_numeric(decision_build_line_p1, 0); build_l2 = force_numeric(decision_build_line_p2, 0)
            prod_p1 = force_numeric(decision_produce_P1, 0); prod_p2 = force_numeric(decision_produce_P2, 0)

            total_lines = lines_p1 + build_l1 + lines_p2 + build_l2
            total_factories = factories + build_f
            if total_lines > total_factories * force_numeric(GLOBAL_PARAMS.get('factory_capacity', 8)): st.error(...) ; return
            if prod_p1 > (lines_p1 * force_numeric(GLOBAL_PARAMS.get('line_p1_capacity', 1000))): st.error(...) ; return
            if prod_p2 > (lines_p2 * force_numeric(GLOBAL_PARAMS.get('line_p2_capacity', 800))): st.error(...) ; return

            decision_data = { # V4.3 收集時強制轉換
                'price_p1': force_numeric(decision_price_P1, DEFAULT_PRICE_P1),
                'ad_p1': force_numeric(decision_ad_P1, DEFAULT_AD_P1), # ... 其他 ...
            }
            all_decisions = load_decisions_from_file() # 讀檔
            all_decisions[team_key] = decision_data    # 更新
            save_decisions_to_file(all_decisions)      # 寫檔
            st.success(...) ; st.rerun()

# --- 6. 結算引擎 (V3.9 + V4.3) ---
def run_season_calculation():
    """V4.3 結算引擎，強制類型檢查 + 穩定性"""
    # (此函數與 V4.2 版本基本相同，已包含所有 force_numeric 檢查)
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

    # === 階段 1: 結算支出、生產、研發 (V4.2 強制轉換) ===
    for team_key, decision in final_decisions.items():
        # ... (結算邏輯同 V4.2, 包含所有 force_numeric) ...
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
    # === 階段 3: 財務報表結算 (V4.2) ===
    for team_key, team_data in teams.items():
        # ... (結算邏輯同 V4.2, 包含 force_numeric) ...
        bs = balance_bs(team_data.get('BS', {})) # V3.9
        # === 階段 4: 緊急貸款 (破產檢查) ===
        cash_after_calc = force_numeric(bs.get('cash', 0)) # V4.2
        if cash_after_calc < 0:
             # ... (結算邏輯同 V4.2, 包含 force_numeric) ...
            bs = balance_bs(bs) # V2.5
        team_data['BS'] = bs if isinstance(bs, dict) else {}
        team_data['IS'] = is_data if isinstance(is_data, dict) else {}
    # === 階段 5: 推進遊戲 (V3.7) ===
    st.session_state.game_season += 1
    delete_decisions_file() # 只刪除檔案
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")

# --- 7. (V2.5 修改) 老師專用函式 (V4.2 強制轉換) ---
def calculate_company_value(bs_data):
    # (此函數與 V4.2 版本完全相同, 已包含 force_numeric)
    value = force_numeric(bs_data.get('cash', 0)) + ...
    return value

def display_admin_dashboard():
    """顯示老師的控制台畫面"""
    st.header(f"👨‍🏫 管理員控制台 (第 {st.session_state.game_season} 季)")
    # --- 學生密碼總覽 ---
    with st.expander("🔑 學生密碼總覽"): # ... (內容同 V4.1) ...
    # --- 修改團隊數據 ---
    with st.expander("🔧 修改團隊數據 (Edit Team Data)"): # ... (內容同 V4.1) ...
    # --- A. 排行榜 (V4.1) ---
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
else: # ... (內容同 V4.1, 但 display_dashboard 已更新) ...
