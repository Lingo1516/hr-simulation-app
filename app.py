# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V3.9 - Ultimate Type Stability)

import streamlit as st
import pandas as pd
import copy
import pickle
import os
import streamlit.components.v1 as components

# --- 0. (V3.1 強化) 檔案同步相關 ---
DECISIONS_FILE = "decisions_state.pkl"

def save_decisions_to_file(decisions_dict):
    with open(DECISIONS_FILE, 'wb') as f:
        pickle.dump(decisions_dict, f)

def load_decisions_from_file():
    if not os.path.exists(DECISIONS_FILE):
        return {}
    with open(DECISIONS_FILE, 'rb') as f:
        return pickle.load(f)

def delete_decisions_file():
    if os.path.exists(DECISIONS_FILE):
        os.remove(DECISIONS_FILE)

# --- 1. 遊戲參數 (V2 升級版) ---
GLOBAL_PARAMS = {
    'factory_cost': 5000000,
    'factory_maintenance': 100000,
    'factory_capacity': 8,
    'line_p1_cost': 1000000,
    'line_p1_maintenance': 20000,
    'line_p1_capacity': 1000,
    'raw_material_cost_R1': 100,
    'p1_labor_cost': 50,
    'p1_material_needed_R1': 1,
    'p1_depreciation_per_line': 10000,
    'line_p2_cost': 1200000,
    'line_p2_maintenance': 25000,
    'line_p2_capacity': 800,
    'raw_material_cost_R2': 150,
    'p2_labor_cost': 70,
    'p2_material_needed_R2': 1,
    'p2_depreciation_per_line': 12000,
    'bank_loan_interest_rate_per_season': 0.02,
    'emergency_loan_interest_rate': 0.05,
    'tax_rate': 0.20,
    'rd_costs_to_level_up': {2: 500000, 3: 1500000, 4: 3500000, 5: 6500000}
}
DEFAULT_PRICE_P1 = 300
DEFAULT_AD_P1 = 50000
DEFAULT_PRICE_P2 = 450
DEFAULT_AD_P2 = 50000

# --- 2. (V2.2 安全升級) 密碼系統 ---
PASSWORDS = {
    "admin": "admin123", "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660", "第 7 組": "ice112",
    "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# --- 3. 團隊狀態初始化 (V2.3) ---
def init_team_state(team_key):
    initial_cash = 10000000
    initial_factories = 1
    initial_lines_p1 = 1
    initial_lines_p2 = 1
    initial_inv_r1 = 2000
    initial_inv_r2 = 2000
    initial_inv_p1 = 500
    initial_inv_p2 = 500
    team_name = team_key
    # 其他財務計算邏輯可略作調整
    mr = {
        'team_name': team_name, 'price_p1': DEFAULT_PRICE_P1, 'ad_p1': DEFAULT_AD_P1,
        'price_p2': DEFAULT_PRICE_P2, 'ad_p2': DEFAULT_AD_P2,
        'market_share_p1': 0, 'market_share_p2': 0
    }
    bs = {
        'cash': initial_cash, 'inventory_value': 0, 'fixed_assets_value': 0,
        'accumulated_depreciation': 0, 'bank_loan': 0, 'shareholder_equity': initial_cash,
        'total_assets': initial_cash, 'total_liabilities_and_equity': initial_cash
    }
    is_data = {
        'interest_expense': 0, 'op_expense_maintenance': 0,
        'op_expense_ads': 0, 'op_expense_rd': 0, 'depreciation_expense': 0
    }
    return {
        'team_name': team_name,
        'factories': initial_factories,
        'lines_p1': initial_lines_p1,
        'lines_p2': initial_lines_p2,
        'inv_r1': initial_inv_r1,
        'inv_r2': initial_inv_r2,
        'inv_p1': initial_inv_p1,
        'inv_p2': initial_inv_p2,
        'MR': mr,
        'BS': bs,
        'IS': is_data
    }

# --- 3.1 (V2.5) 資產負債表平衡函數 ---
def balance_bs(bs_data):
    bs_data['total_assets'] = bs_data.get('cash',0) + bs_data.get('inventory_value',0) + bs_data.get('fixed_assets_value',0) - bs_data.get('accumulated_depreciation',0)
    bs_data['total_liabilities_and_equity'] = bs_data.get('bank_loan',0) + bs_data.get('shareholder_equity',0)
    if abs(bs_data['total_assets'] - bs_data['total_liabilities_and_equity']) > 1:
        diff = bs_data['total_assets'] - bs_data['total_liabilities_and_equity']
        bs_data['shareholder_equity'] += diff
        bs_data['total_liabilities_and_equity'] = bs_data['total_assets']
    return bs_data

# --- 4. 儀表板 (Dashboard V2) (V2.4 格式化) ---
def display_dashboard(team_key, team_data):
    st.header(f"📈 {team_data['team_name']} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data.get('BS', {})
    is_data = team_data.get('IS', {})
    mr = team_data.get('MR', {})
    tab1, tab2, tab3 = st.tabs(["📊 市場報告 (上季)", "💰 損益表 (上季)", "🏦 資產負債表 (當前)"])
    with tab1:
        st.write(mr)
    with tab2:
        st.write(is_data)
    with tab3:
        st.write(bs)

# --- 5. 決策表單 (Decision Form V2) (V3.7 修改提交邏輯) ---
def display_decision_form(team_key):
    team_data = st.session_state.teams[team_key]
    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_data['team_name']} ({team_key}) - 第 {st.session_state.game_season} 季決策單")
        price_p1 = st.number_input("P1 價格", min_value=100, value=team_data['MR'].get('price_p1', DEFAULT_PRICE_P1))
        ad_p1 = st.number_input("P1 廣告", min_value=0, value=team_data['MR'].get('ad_p1', DEFAULT_AD_P1))
        price_p2 = st.number_input("P2 價格", min_value=150, value=team_data['MR'].get('price_p2', DEFAULT_PRICE_P2))
        ad_p2 = st.number_input("P2 廣告", min_value=0, value=team_data['MR'].get('ad_p2', DEFAULT_AD_P2))
        # ... 其他各項決策欄位 ...
        submitted = st.form_submit_button("提交本季決策")
        if submitted:
            # 基本檢查
            if price_p1 < 0 or price_p2 < 0:
                st.error("價格不能為負數")
                return
            # ... 其他檢查 ...
            decision_data = {
                'price_p1': price_p1,
                'ad_p1': ad_p1,
                'price_p2': price_p2,
                'ad_p2': ad_p2,
            }
            all_decisions = load_decisions_from_file()
            all_decisions[team_key] = decision_data
            save_decisions_to_file(all_decisions)
            st.success("決策已提交，等待老師結算")
            st.rerun()

# --- 6. 結算引擎 (V3.9 終極類型穩定) ---
def run_season_calculation():
    teams = st.session_state.teams
    current_decisions_from_file = load_decisions_from_file()
    final_decisions = {}

    for team_key in team_list:
        if team_key not in teams:
            st.session_state.teams[team_key] = init_team_state(team_key)
        team_data = teams.get(team_key)
        if not isinstance(team_data, dict):
            st.error(f"隊伍 {team_key} 的數據損壞。")
            continue
        if team_key in current_decisions_from_file:
            decision_data = current_decisions_from_file[team_key]
            if not isinstance(decision_data, dict):
                st.error(f"隊伍 {team_key} 的決策數據損壞。")
                decision_data = {}
            else:
                final_decisions[team_key] = decision_data
        else:
            st.warning(f"{team_data.get('team_name', team_key)} ({team_key}) 未提交決策，將使用預設。")
            mr_data = team_data.get('MR', {})
            if not isinstance(mr_data, dict):
                mr_data = {}
            final_decisions[team_key] = {
                'price_p1': mr_data.get('price_p1', DEFAULT_PRICE_P1),
                'ad_p1': mr_data.get('ad_p1', DEFAULT_AD_P1),
                'price_p2': mr_data.get('price_p2', DEFAULT_PRICE_P2),
                'ad_p2': mr_data.get('ad_p2', DEFAULT_AD_P2),
            }
        if team_key not in final_decisions:
            final_decisions[team_key] = {
                'price_p1': mr_data.get('price_p1', DEFAULT_PRICE_P1),
                'ad_p1': mr_data.get('ad_p1', DEFAULT_AD_P1),
                'price_p2': mr_data.get('price_p2', DEFAULT_PRICE_P2),
                'ad_p2': mr_data.get('ad_p2', DEFAULT_AD_P2),
            }
    # ... 結算邏輯與所有細節（計算產量、資產更新、利息、稅金等） --
    st.session_state.game_season += 1
    delete_decisions_file()
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")

# --- 7. (V2.5 修改) 老師專用函式 (V3.6) ---
def calculate_company_value(bs_data):
    value = bs_data.get('cash', 0) + bs_data.get('inventory_value', 0) + \
            (bs_data.get('fixed_assets_value', 0) - bs_data.get('accumulated_depreciation', 0)) - \
            bs_data.get('bank_loan', 0)
    return value

def display_admin_dashboard():
    st.header(f"👨‍🏫 管理員控制台 (第 {st.session_state.game_season} 季)")
    with st.expander("🔑 學生密碼總覽"):
        st.write(PASSWORDS)
    st.subheader("遊戲排行榜 (依公司總價值)")
    # ... 顯示公司排行榜與決策提交狀態 ...
    st.subheader("遊戲控制")

# --- 8. 主程式 (Main App) (V3.7) ---
st.set_page_config(layout="wide")

if 'game_season' not in st.session_state:
    st.session_state.game_season = 1
    st.session_state.teams = {}
    st.session_state.logged_in_user = None

if st.session_state.logged_in_user is None:
    st.title("🚀 新星製造 V2 - 遊戲登入")
    username = st.text_input("請輸入團隊或管理員帳號")
    password = st.text_input("請輸入密碼", type="password")
    if st.button("登入"):
        if username in PASSWORDS and password == PASSWORDS[username]:
            st.session_state.logged_in_user = username
            st.rerun()
        else:
            st.error("帳號或密碼錯誤，請重試。")
else:
    current_user = st.session_state.logged_in_user
    if current_user == "admin":
        display_admin_dashboard()
    elif current_user in team_list:
        team_key = current_user
        if team_key not in st.session_state.teams:
            st.session_state.teams[team_key] = init_team_state(team_key)
        current_team_data = st.session_state.teams.get(team_key, init_team_state(team_key))
        st.sidebar.header(f"🎓 {current_team_data.get('team_name', team_key)} ({team_key})")
        new_team_name = st.sidebar.text_input("修改您的隊伍名稱：", value=current_team_data.get('team_name', team_key))
        if new_team_name != current_team_data.get('team_name', team_key):
            if not new_team_name.strip():
                st.sidebar.error("隊伍名稱不能為空！")
            else:
                if team_key in st.session_state.teams:
                    st.session_state.teams[team_key]['team_name'] = new_team_name
                    st.sidebar.success("隊伍名稱已更新！")
                    st.rerun()
                else:
                    st.sidebar.error("發生錯誤，無法更新隊名。")
        if st.sidebar.button("登出"):
            st.session_state.logged_in_user = None
            st.rerun()
        display_dashboard(team_key, current_team_data)
        st.markdown("---")
        current_decisions_from_file = load_decisions_from_file()
        if team_key in current_decisions_from_file:
            st.info(f"您已提交第 {st.session_state.game_season} 季的決策，請等待老師結算...")
        else:
            display_decision_form(team_key)
