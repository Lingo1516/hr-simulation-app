# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V2.5)
#
# V2.5 更新：
# 1. (使用者要求) 在「管理員控制台」新增「修改團隊數據」功能，
#    老師可手動修改任一隊伍的「現金」和「銀行借款」。
# 2. 修改相關函數，確保資產負債表在修改後能自動平衡。

import streamlit as st
import pandas as pd
import copy

# --- 1. 遊戲參數 (V2 升級版) ---
GLOBAL_PARAMS = {
    'factory_cost': 5000000,
    'factory_maintenance': 100000,
    'factory_capacity': 8, # 1座工廠 = 8 條生產線 (P1+P2總和)
    'line_p1_cost': 1000000,
    'line_p1_maintenance': 20000,
    'line_p1_capacity': 1000, # 單位 P1 / 季
    'raw_material_cost_R1': 100,
    'p1_labor_cost': 50, # 每單位 P1 的人工成本
    'p1_material_needed_R1': 1, # 每單位 P1 需 1 單位 R1
    'p1_depreciation_per_line': 10000, # 每條P1線的折舊
    'line_p2_cost': 1200000,
    'line_p2_maintenance': 25000,
    'line_p2_capacity': 800, # 單位 P2 / 季
    'raw_material_cost_R2': 150,
    'p2_labor_cost': 70,
    'p2_material_needed_R2': 1,
    'p2_depreciation_per_line': 12000,
    'bank_loan_interest_rate_per_season': 0.02, # 季利率 2%
    'emergency_loan_interest_rate': 0.05,
    'tax_rate': 0.20, # 稅率 20%
    'rd_costs_to_level_up': {
        2: 500000, 3: 1500000, 4: 3500000, 5: 6500000
    }
}

# --- 2. (V2.2 安全升級) 密碼系統 ---
PASSWORDS = {
    "admin": "admin123", # 老師的密碼 (您還是可以自己改)
    "第 1 組": "sky902",
    "第 2 組": "rock331",
    "第 3 組": "lion774",
    "第 4 組": "moon159",
    "第 5 組": "tree482",
    "第 6 組": "fire660",
    "第 7 組": "ice112",
    "第 8 組": "sun735",
    "第 9 組": "king048",
    "第 10 組": "aqua526"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# --- 3. 團隊狀態初始化 (V2.3) ---
def init_team_state(team_key): # 傳入 team_key
    """定義一家公司 "出生時" 的狀態 (V2.3)"""
    initial_cash = 10000000 # 預設初始現金
    initial_factories = 1
    initial_lines_p1 = 1
    initial_lines_p2 = 1
    initial_inv_r1 = 2000
    initial_inv_r2 = 2000
    initial_inv_p1 = 500
    initial_inv_p2 = 500

    cogs_p1 = GLOBAL_PARAMS['raw_material_cost_R1'] * GLOBAL_PARAMS['p1_material_needed_R1'] + GLOBAL_PARAMS['p1_labor_cost']
    cogs_p2 = GLOBAL_PARAMS['raw_material_cost_R2'] * GLOBAL_PARAMS['p2_material_needed_R2'] + GLOBAL_PARAMS['p2_labor_cost']
    inv_value = (initial_inv_r1 * GLOBAL_PARAMS['raw_material_cost_R1']) + \
                (initial_inv_r2 * GLOBAL_PARAMS['raw_material_cost_R2']) + \
                (initial_inv_p1 * cogs_p1) + \
                (initial_inv_p2 * cogs_p2)
    fixed_assets = (initial_factories * GLOBAL_PARAMS['factory_cost']) + \
                   (initial_lines_p1 * GLOBAL_PARAMS['line_p1_cost']) + \
                   (initial_lines_p2 * GLOBAL_PARAMS['line_p2_cost'])
    total_assets = initial_cash + inv_value + fixed_assets
    initial_equity = total_assets # 初始假設無負債

    return {
        'team_name': team_key,
        'BS': {
            'cash': initial_cash, 'inventory_value': inv_value,
            'fixed_assets_value': fixed_assets, 'accumulated_depreciation': 0,
            'total_assets': total_assets, 'bank_loan': 0, # 初始無負債
            'shareholder_equity': initial_equity,
            'total_liabilities_and_equity': total_assets
        },
        'IS': { # 上一季損益表為 0
             k: 0 for k in ['revenue_p1', 'revenue_p2', 'total_revenue', 'cogs', 'gross_profit',
                           'op_expense_ads', 'op_expense_rd', 'op_expense_maintenance',
                           'depreciation_expense', 'total_op_expense', 'operating_profit',
                           'interest_expense', 'profit_before_tax', 'tax_expense', 'net_income']
        },
        'factories': initial_factories, 'lines_p1': initial_lines_p1, 'lines_p2': initial_lines_p2,
        'inventory_R1_units': initial_inv_r1, 'inventory_R2_units': initial_inv_r2,
        'inventory_P1_units': initial_inv_p1, 'inventory_P2_units': initial_inv_p2,
        'rd_level_P1': 1, 'rd_level_P2': 1,
        'rd_investment_P1': 0, 'rd_investment_P2': 0,
        'MR': { # 上一季市場報告預設值
            'price_p1': 300, 'ad_p1': 50000, 'sales_units_p1': 0, 'market_share_p1': 0.0,
            'price_p2': 450, 'ad_p2': 50000, 'sales_units_p2': 0, 'market_share_p2': 0.0,
        }
    }

# --- 3.1 (V2.5 新增) 資產負債表平衡函數 ---
def balance_bs(bs_data):
    """輸入 BS 字典，重新計算總資產和總負債權益，並強制平衡"""
    # 重新計算總資產
    bs_data['total_assets'] = bs_data['cash'] + bs_data['inventory_value'] + \
                              bs_data['fixed_assets_value'] - bs_data['accumulated_depreciation']
    # 重新計算總負債與權益 (假設只有銀行借款)
    bs_data['total_liabilities_and_equity'] = bs_data['bank_loan'] + bs_data['shareholder_equity']

    # 強制平衡 (差額調整至股東權益)
    if abs(bs_data['total_assets'] - bs_data['total_liabilities_and_equity']) > 1: # 允許 1 元誤差
        diff = bs_data['total_assets'] - bs_data['total_liabilities_and_equity']
        bs_data['shareholder_equity'] += diff
        bs_data['total_liabilities_and_equity'] = bs_data['total_assets'] # 確保完全相等
    return bs_data


# --- 4. 儀表板 (Dashboard V2) (V2.4 格式化) ---
def display_dashboard(team_key, team_data):
    # (此函數與 V2.4 版本完全相同，故省略...)
    st.header(f"📈 {team_data['team_name']} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data['BS']
    is_data = team_data['IS']
    mr = team_data['MR']

    tab1, tab2, tab3 = st.tabs(["📊 市場報告 (上季)", "💰 損益表 (上季)", "🏦 資產負債表 (當前)"])
    # ... (tab1, tab2, tab3 的內容同 V2.4) ...
    with tab1:
        st.subheader("P1 市場 (上季)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("銷售價格", f"${mr['price_p1']:,.0f}")
        col2.metric("廣告投入", f"${mr['ad_p1']:,.0f}")
        col3.metric("實際銷量", f"{mr['sales_units_p1']:,.0f} u")
        col4.metric("市佔率", f"{mr['market_share_p1']:.2%}")
        st.subheader("P2 市場 (上季)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("銷售價格", f"${mr['price_p2']:,.0f}")
        col2.metric("廣告投入", f"${mr['ad_p2']:,.0f}")
        col3.metric("實際銷量", f"{mr['sales_units_p2']:,.0f} u")
        col4.metric("市佔率", f"{mr['market_share_p2']:.2%}")
    with tab2:
        st.subheader("損益表 (Income Statement) - 上一季")
        st.metric("💹 稅後淨利 (Net Income)", f"${is_data['net_income']:,.0f}")
        with st.expander("查看詳細損益表"):
            st.markdown(f"""
            | 項目 | 金額 |
            | :--- | ---: |
            | P1 營業收入 | ${is_data['revenue_p1']:,.0f} |
            | P2 營業收入 | ${is_data['revenue_p2']:,.0f} |
            | **總營業收入** | **${is_data['total_revenue']:,.0f}** |
            | 銷貨成本 (COGS) | (${is_data['cogs']:,.0f}) |
            | **營業毛利** | **${is_data['gross_profit']:,.0f}** |
            | --- | --- |
            | 廣告費用 | (${is_data['op_expense_ads']:,.0f}) |
            | 研發費用 | (${is_data['op_expense_rd']:,.0f}) |
            | 維護費用 | (${is_data['op_expense_maintenance']:,.0f}) |
            | 折舊費用 | (${is_data['depreciation_expense']:,.0f}) |
            | **總營業費用** | **(${is_data['total_op_expense']:,.0f})** |
            | **營業淨利** | **${is_data['operating_profit']:,.0f}** |
            | --- | --- |
            | 利息費用 | (${is_data['interest_expense']:,.0f}) |
            | **稅前淨利** | **${is_data['profit_before_tax']:,.0f}** |
            | 所得稅 (20%) | (${is_data['tax_expense']:,.0f}) |
            | **稅後淨利** | **${is_data['net_income']:,.0f}** |
            """)
    with tab3:
        st.subheader("資產負債表 (Balance Sheet) - 當前")
        st.metric("🏦 總資產 (Total Assets)", f"${bs['total_assets']:,.0f}")
        with st.expander("查看詳細資產負債表"):
            st.markdown(f"""
            | 資產 (Assets) | 金額 | 負債與權益 (Liabilities & Equity) | 金額 |
            | :--- | ---: | :--- | ---: |
            | **流動資產** | | **負債** | |
            | 現金 | ${bs['cash']:,.0f} | 銀行借款 | ${bs['bank_loan']:,.0f} |
            | 存貨價值 | ${bs['inventory_value']:,.0f} | |
