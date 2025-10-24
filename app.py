# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V3.4 - Calculation Stability)
#
# V3.4 更新：
# 1. (穩定性) 在結算引擎的市場計算部分，加入強制數值檢查 (.get() + isinstance)，
#    防止因 price 或 ad 意外變為 None 而導致 TypeError。

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
    # ... (參數內容同 V3.2) ...
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
    # ... (密碼內容同 V3.2) ...
    "admin": "admin123", "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660", "第 7 組": "ice112",
    "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# --- 3. 團隊狀態初始化 (V2.3) ---
def init_team_state(team_key):
    # (此函數與 V3.2 版本完全相同)
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
    # (此函數與 V3.2 版本完全相同)
    bs_data['total_assets'] = bs_data['cash'] + bs_data['inventory_value'] + bs_data['fixed_assets_value'] - bs_data['accumulated_depreciation']
    bs_data['total_liabilities_and_equity'] = bs_data['bank_loan'] + bs_data['shareholder_equity']
    if abs(bs_data['total_assets'] - bs_data['total_liabilities_and_equity']) > 1:
        diff = bs_data['total_assets'] - bs_data['total_liabilities_and_equity']
        bs_data['shareholder_equity'] += diff
        bs_data['total_liabilities_and_equity'] = bs_data['total_assets']
    return bs_data

# --- 4. 儀表板 (Dashboard V2) (V2.4 格式化) ---
def display_dashboard(team_key, team_data):
    # (此函數與 V3.2 版本完全相同)
    st.header(f"📈 {team_data['team_name']} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data['BS']; is_data = team_data['IS']; mr = team_data['MR']
    tab1, tab2, tab3 = st.tabs(["📊 市場報告 (上季)", "💰 損益表 (上季)", "🏦 資產負債表 (當前)"])
    # ... (tab1, tab2, tab3 內容同 V3.2) ...
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
    # (此函數與 V3.3 版本完全相同)
    team_data = st.session_state.teams[team_key]
    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_data['team_name']} ({team_key}) - 第 {st.session_state.game_season} 季決策單")
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs(["P1 產品決策", "P2 產品決策", "生產與資本決策", "財務決策"])
        # ... (各 Tab 內容同 V3.3) ...
        with tab_p1: decision_price_P1 = st.slider(...) # ...
        with tab_p2: decision_price_P2 = st.slider(...) # ...
        with tab_prod: decision_produce_P1 = col1.number_input(...) # ...
        with tab_fin: decision_loan = col1.number_input(...) # ...

        submitted = st.form_submit_button("提交本季決策")
        if submitted:
            # (檢查邏輯與 V3.3 相同)
            if ...: st.error(...) ; return # 工廠容量檢查
            if ...: st.error(...) ; return # P1 產能檢查
            if ...: st.error(...) ; return # P2 產能檢查

            decision_data = { ... } # 收集本次決策
            all_decisions = load_decisions_from_file() # V3.3
            all_decisions[team_key] = decision_data # V3.3
            save_decisions_to_file(all_decisions) # V3.3
            st.session_state.decisions = all_decisions # V3.3
            st.success(...) ; st.rerun()

# --- 6. 結算引擎 (*** V3.4 強化數值穩定性 ***) ---
def run_season_calculation():
    """V3.4 結算引擎，優先讀取檔案狀態 + 研發穩定性 + 市場計算穩定性"""

    teams = st.session_state.teams
    current_decisions_from_file = load_decisions_from_file() # 必定讀檔
    st.session_state.decisions = current_decisions_from_file # 同步 state
    final_decisions = {}

    for team_key in team_list: # V3.0 確保所有隊伍都被處理
        if team_key not in teams: st.session_state.teams[team_key] = init_team_state(team_key)
        team_data = teams[team_key]
        if team_key in current_decisions_from_file:
            final_decisions[team_key] = current_decisions_from_file[team_key]
        else: # 預設懲罰
            st.warning(f"警告：{team_data['team_name']} ({team_key}) 未提交決策，將使用預設。")
            final_decisions[team_key] = { # (預設值同 V3.3)
                'price_p1': team_data['MR']['price_p1'], 'ad_p1': team_data['MR']['ad_p1'],
                'price_p2': team_data['MR']['price_p2'], 'ad_p2': team_data['MR']['ad_p2'],
                'rd_p1': 0, 'rd_p2': 0, 'produce_p1': 0, 'produce_p2': 0,
                'buy_r1': 0, 'buy_r2': 0, 'build_factory': 0,
                'build_line_p1': 0, 'build_line_p2': 0, 'loan': 0, 'repay': 0
            }

    # === 階段 1: 結算支出、生產、研發 (V3.2 修正) ===
    for team_key, decision in final_decisions.items(): # ... (結算邏輯同 V3.2, 含研發檢查) ...
        team_data['IS'] = is_data # 存回 state

    # === 階段 2: 市場結算 (*** V3.4 強化數值檢查 ***) ===
    st.warning("V1 結算引擎：使用簡化銷售模型 (未來將替換為競爭模型)")

    # --- P1 市場 ---
    market_p1_data = {}
    total_score_p1 = 0
    DEFAULT_PRICE_P1 = 300 # V3.4 預設價格
    for key, d in final_decisions.items():
        # --- V3.4 強制數值檢查 ---
        ad_p1 = d.get('ad_p1', 0)
        price_p1 = d.get('price_p1', DEFAULT_PRICE_P1)
        if not isinstance(ad_p1, (int, float)):
            st.warning(f"偵測到 {key} P1 廣告費異常({ad_p1})，已設為 0。")
            ad_p1 = 0
        if not isinstance(price_p1, (int, float)) or price_p1 <= 0:
            st.warning(f"偵測到 {key} P1 價格異常({price_p1})，已設為 ${DEFAULT_PRICE_P1}。")
            price_p1 = DEFAULT_PRICE_P1
        # --- 檢查結束 ---

        score = (ad_p1 / 10000) / (price_p1 / DEFAULT_PRICE_P1) # 使用預設價格作為基準
        market_p1_data[key] = score
        total_score_p1 += score

    TOTAL_MARKET_DEMAND_P1 = 50000
    for team_key, score in market_p1_data.items():
        team_data = teams[team_key]; decision = final_decisions[team_key]
        market_share = (score / total_score_p1) if total_score_p1 > 0 else (1/len(teams))
        demand_units = int(TOTAL_MARKET_DEMAND_P1 * market_share)
        actual_sales_units = min(demand_units, team_data['inventory_P1_units'])
        # --- V3.4 使用檢查過的 price_p1 ---
        price_p1 = decision.get('price_p1', DEFAULT_PRICE_P1) # 再次獲取 (或使用已檢查的也行)
        if not isinstance(price_p1, (int, float)) or price_p1 <= 0: price_p1 = DEFAULT_PRICE_P1
        revenue = actual_sales_units * price_p1
        # --- 修改結束 ---
        team_data['BS']['cash'] += revenue
        team_data['inventory_P1_units'] -= actual_sales_units
        team_data['IS']['revenue_p1'] = revenue
        team_data['MR']['sales_units_p1'] = actual_sales_units; team_data['MR']['market_share_p1'] = market_share

    # --- P2 市場 ---
    market_p2_data = {}
    total_score_p2 = 0
    DEFAULT_PRICE_P2 = 450 # V3.4 預設價格
    for key, d in final_decisions.items():
        # --- V3.4 強制數值檢查 ---
        ad_p2 = d.get('ad_p2', 0)
        price_p2 = d.get('price_p2', DEFAULT_PRICE_P2)
        if not isinstance(ad_p2, (int, float)):
            st.warning(f"偵測到 {key} P2 廣告費異常({ad_p2})，已設為 0。")
            ad_p2 = 0
        if not isinstance(price_p2, (int, float)) or price_p2 <= 0:
            st.warning(f"偵測到 {key} P2 價格異常({price_p2})，已設為 ${DEFAULT_PRICE_P2}。")
            price_p2 = DEFAULT_PRICE_P2
        # --- 檢查結束 ---

        score = (ad_p2 / 10000) / (price_p2 / DEFAULT_PRICE_P2) # 使用預設價格作為基準
        market_p2_data[key] = score
        total_score_p2 += score

    TOTAL_MARKET_DEMAND_P2 = 40000
    for team_key, score in market_p2_data.items():
        team_data = teams[team_key]; decision = final_decisions[team_key]
        market_share = (score / total_score_p2) if total_score_p2 > 0 else (1/len(teams))
        demand_units = int(TOTAL_MARKET_DEMAND_P2 * market_share)
        actual_sales_units = min(demand_units, team_data['inventory_P2_units'])
        # --- V3.4 使用檢查過的 price_p2 ---
        price_p2 = decision.get('price_p2', DEFAULT_PRICE_P2) # 再次獲取
        if not isinstance(price_p2, (int, float)) or price_p2 <= 0: price_p2 = DEFAULT_PRICE_P2
        revenue = actual_sales_units * price_p2
        # --- 修改結束 ---
        team_data['BS']['cash'] += revenue
        team_data['inventory_P2_units'] -= actual_sales_units
        team_data['IS']['revenue_p2'] = revenue
        team_data['MR']['sales_units_p2'] = actual_sales_units; team_data['MR']['market_share_p2'] = market_share

    # === 階段 3: 財務報表結算 ===
    # (此階段邏輯與 V3.2 相同)
    for team_key, team_data in teams.items(): # ... (結算邏輯同 V3.2) ...
        bs = balance_bs(bs) # V2.5
        # === 階段 4: 緊急貸款 (破產檢查) ===
        if bs['cash'] < 0: # ... (結算邏輯同 V3.2) ...
            bs = balance_bs(bs) # V2.5
        team_data['BS'] = bs; team_data['IS'] = is_data # 存回 state

    # === 階段 5: 推進遊戲 (V2.8) ===
    st.session_state.game_season += 1
    st.session_state.decisions = {} # 清空 session state
    delete_decisions_file() # 刪除檔案
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")


# --- 7. (V2.5 修改) 老師專用函式 (V3.1 移除除錯) ---
def calculate_company_value(bs_data):
    # (此函數與 V3.2 版本完全相同)
    value = bs_data['cash'] + bs_data['inventory_value'] + (bs_data['fixed_assets_value'] - bs_data['accumulated_depreciation']) - bs_data['bank_loan']
    return value

def display_admin_dashboard():
    """顯示老師的控制台畫面"""
    st.header(f"👨‍🏫 管理員控制台 (第 {st.session_state.game_season} 季)")
    
    # --- 學生密碼總覽 ---
    with st.expander("🔑 學生密碼總覽"): # ... (內容同 V3.2) ...
    # --- 修改團隊數據 ---
    with st.expander("🔧 修改團隊數據 (Edit Team Data)"): # ... (內容同 V3.2) ...
    # --- A. 排行榜 (V2.4 格式化) ---
    st.subheader("遊戲排行榜 (依公司總價值)") # ... (內容同 V3.2) ...
    # --- B. 監控面板 (V3.0 依賴檔案讀取) ---
    st.subheader("本季決策提交狀態") # ... (內容同 V3.2) ...
    # --- C. 控制按鈕 (V2.8 修改重置邏輯) ---
    st.subheader("遊戲控制") # ... (內容同 V3.2) ...

# --- 8. 主程式 (Main App) (V3.3 強化初始化和學生畫面) ---
st.set_page_config(layout="wide")

# --- 初始化 session_state ---
if 'game_season' not in st.session_state:
    st.session_state.game_season = 1
    st.session_state.teams = {}
    st.session_state.decisions = load_decisions_from_file() # V3.0
    st.session_state.logged_in_user = None

# --- 登入邏輯 ---
if st.session_state.logged_in_user is None:
    # (此區塊與 V3.2 相同)
    st.title("🚀 新星製造 V2 - 遊戲登入") # ... (登入介面同 V3.2) ...

# --- 登入後的畫面 ---
else:
    current_user = st.session_state.logged_in_user
    if current_user == "admin":
        # --- A. 老師畫面 ---
        display_admin_dashboard()
    elif current_user in team_list:
        # --- B. 學生畫面 (V3.3 強化狀態檢查) ---
        team_key = current_user
        if team_key not in st.session_state.teams: st.session_state.teams[team_key] = init_team_state(team_key)
        current_team_data = st.session_state.teams[team_key]

        # --- B1. 學生側邊欄 ---
        st.sidebar.header(f"🎓 {current_team_data['team_name']} ({team_key})")
        new_team_name = st.sidebar.text_input(...)
        if new_team_name != current_team_data['team_name']: # ... (修改隊名邏輯同 V3.2) ...
            st.rerun()
        if st.sidebar.button("登出"): st.session_state.logged_in_user = None; st.rerun()

        # --- B2. 學生主畫面 ---
        display_dashboard(team_key, current_team_data)
        st.markdown("---")

        # ** V3.3 核心修改：必定從檔案讀取狀態來決定顯示 **
        current_decisions_from_file = load_decisions_from_file()
        st.session_state.decisions = current_decisions_from_file # V3.3 同步

        if team_key in current_decisions_from_file:
            st.info(f"您已提交第 {st.session_state.game_season} 季的決策，請等待老師結算...")
        else:
            display_decision_form(team_key)
