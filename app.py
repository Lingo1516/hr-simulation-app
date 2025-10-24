# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V2.0)
#
# V2.0 重大架構更新：
# 1. (使用者要求) 建立「老師」vs「學生」的獨立畫面。
# 2. (使用者要求) 新增「密碼登入系統」，區分老師和 10 個組別。
# 3. (使用者要求) 在「管理員控制台」新增「排行榜」(依公司總價值)。
# 4. (使用者要求) 在「學生決策單」中新增「策略提示」。
# 5. (解惑) "實際銷售量為0" 是因為顯示的是上一季(第0季)的數據。

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

# --- 2. (V2.0 新增) 密碼系統 ---
# (您可以自行修改密碼)
PASSWORDS = {
    "admin": "admin123", # 老師的密碼
    "第 1 組": "team1",
    "第 2 組": "team2",
    "第 3 組": "team3",
    "第 4 組": "team4",
    "第 5 組": "team5",
    "第 6 組": "team6",
    "第 7 組": "team7",
    "第 8 組": "team8",
    "第 9 組": "team9",
    "第 10 組": "team10"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# --- 3. 團隊狀態初始化 (V2 升級版) ---
def init_team_state():
    """定義一家公司 "出生時" 的狀態 (V2)"""
    initial_cash = 10000000
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
    initial_equity = total_assets

    return {
        'BS': {
            'cash': initial_cash, 'inventory_value': inv_value,
            'fixed_assets_value': fixed_assets, 'accumulated_depreciation': 0,
            'total_assets': total_assets, 'bank_loan': 0,
            'shareholder_equity': initial_equity,
            'total_liabilities_and_equity': total_assets
        },
        'IS': {
            'revenue_p1': 0, 'revenue_p2': 0, 'total_revenue': 0,
            'cogs': 0, 'gross_profit': 0, 'op_expense_ads': 0,
            'op_expense_rd': 0, 'op_expense_maintenance': 0,
            'depreciation_expense': 0, 'total_op_expense': 0,
            'operating_profit': 0, 'interest_expense': 0,
            'profit_before_tax': 0, 'tax_expense': 0, 'net_income': 0
        },
        'factories': initial_factories, 'lines_p1': initial_lines_p1, 'lines_p2': initial_lines_p2,
        'inventory_R1_units': initial_inv_r1, 'inventory_R2_units': initial_inv_r2,
        'inventory_P1_units': initial_inv_p1, 'inventory_P2_units': initial_inv_p2,
        'rd_level_P1': 1, 'rd_level_P2': 1,
        'rd_investment_P1': 0, 'rd_investment_P2': 0,
        'MR': {
            'price_p1': 300, 'ad_p1': 50000, 'sales_units_p1': 0, 'market_share_p1': 0.0,
            'price_p2': 450, 'ad_p2': 50000, 'sales_units_p2': 0, 'market_share_p2': 0.0,
        }
    }


# --- 4. 儀表板 (Dashboard V2) ---
def display_dashboard(team_key, team_data):
    st.header(f"📈 {team_key} 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data['BS']
    is_data = team_data['IS']
    mr = team_data['MR']

    tab1, tab2, tab3 = st.tabs(["📊 市場報告 (上季)", "💰 損益表 (上季)", "🏦 資產負債表 (當前)"])
    with tab1:
        st.subheader("P1 市場 (上季)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("銷售價格", f"${mr['price_p1']}")
        col2.metric("廣告投入", f"${mr['ad_p1']:,.0f}")
        col3.metric("實際銷量", f"{mr['sales_units_p1']:,.0f} u")
        col4.metric("市佔率", f"{mr['market_share_p1']:.2%}")
        st.subheader("P2 市場 (上季)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("銷售價格", f"${mr['price_p2']}")
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
            | 存貨價值 | ${bs['inventory_value']:,.0f} | | |
            | **固定資產** | | **股東權益** | |
            | 廠房設備 | ${bs['fixed_assets_value']:,.0f} | 股東權益 | ${bs['shareholder_equity']:,.0f} |
            | 累計折舊 | (${bs['accumulated_depreciation']:,.0f}) | | |
            | **總資產** | **${bs['total_assets']:,.0f}** | **總負債與權益** | **${bs['total_liabilities_and_equity']:,.0f}** |
            """)
        st.subheader("內部資產 (非財報)")
        col1, col2, col3 = st.columns(3)
        col1.metric("🏭 工廠 (座)", team_data['factories'])
        col2.metric("🔩 P1 生產線 (條)", team_data['lines_p1'])
        col3.metric("🔩 P2 生產線 (條)", team_data['lines_p2']) 
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 R1 庫存 (u)", f"{team_data['inventory_R1_units']:,.0f}")
        col2.metric("🏭 P1 庫存 (u)", f"{team_data['inventory_P1_units']:,.0f}")
        col3.metric("📦 R2 庫存 (u)", f"{team_data['inventory_R2_units']:,.0f}")
        col4.metric("🏭 P2 庫存 (u)", f"{team_data['inventory_P2_units']:,.0f}")


# --- 5. 決策表單 (Decision Form V2) (*** V2.0 新增提示 ***) ---
def display_decision_form(team_key):
    team_data = st.session_state.teams[team_key]
    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_key} - 第 {st.session_state.game_season} 季決策單")
        
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs(["P1 產品決策", "P2 產品決策", "生產與資本決策", "財務決策"])

        with tab_p1:
            st.subheader("P1 產品決策")
            decision_price_P1 = st.slider("P1 銷售價格", 100, 1000, value=team_data['MR']['price_p1'], step=10)
            st.caption("提示：價格將影響您的『市場吸引力』。價格越低，吸引力越高，但毛利越低。")
            decision_ad_P1 = st.number_input("P1 廣告費用", min_value=0, step=10000, value=team_data['MR']['ad_p1'])
            st.caption("提示：廣告費將影響您的『市場吸引力』。投入越高，吸引力越高，但會侵蝕您的營業淨利。")
            decision_rd_P1 = st.number_input("P1 研發費用", min_value=0, step=50000, value=0)
            st.caption(f"提示：研發費用會累計。P1 目前 L{team_data['rd_level_P1']}，累計投入 ${team_data['rd_investment_P1']:,.0f}。")
            
        with tab_p2:
            st.subheader("P2 產品決策")
            decision_price_P2 = st.slider("P2 銷售價格", 150, 1500, value=team_data['MR']['price_p2'], step=10)
            st.caption("提示：P2 市場與 P1 獨立。")
            decision_ad_P2 = st.number_input("P2 廣告費用", min_value=0, step=10000, value=team_data['MR']['ad_p2'])
            st.caption("提示：P2 的廣告效果與 P1 獨立計算。")
            decision_rd_P2 = st.number_input("P2 研發費用", min_value=0, step=50000, value=0)
            st.caption(f"提示：P2 目前 L{team_data['rd_level_P2']}，累計投入 ${team_data['rd_investment_P2']:,.0f}。")

        with tab_prod:
            st.subheader("生產計畫")
            col1, col2 = st.columns(2)
            decision_produce_P1 = col1.number_input("P1 計畫產量 (單位)", min_value=0, step=100, value=0)
            decision_produce_P2 = col2.number_input("P2 計畫產量 (單位)", min_value=0, step=100, value=0)
            st.caption(f"提示：P1 最大產能 {team_data['lines_p1'] * GLOBAL_PARAMS['line_p1_capacity']} (需 R1 {team_data['inventory_R1_units']} u)。 "
                       f"P2 最大產能 {team_data['lines_p2'] * GLOBAL_PARAMS['line_p2_capacity']} (需 R2 {team_data['inventory_R2_units']} u)。")

            st.subheader("原料採購")
            col1, col2 = st.columns(2)
            decision_buy_R1 = col1.number_input("採購 R1 數量 (單位)", min_value=0, step=100, value=0)
            decision_buy_R2 = col2.number_input("採購 R2 數量 (單位)", min_value=0, step=100, value=0)
            st.caption("提示：採購的原料會在本季花費現金，但**下一季**才能用於生產 (V2 簡化版：本季即可用)。")
            
            st.subheader("資本投資")
            col1, col2, col3 = st.columns(3)
            decision_build_factory = col1.number_input("建置新工廠 (座)", min_value=0, value=0)
            decision_build_line_p1 = col2.number_input("建置 P1 生產線 (條)", min_value=0, value=0)
            decision_build_line_p2 = col3.number_input("建置 P2 生產線 (條)", min_value=0, value=0)
            total_lines_now = team_data['lines_p1'] + team_data['lines_p2']
            total_capacity_now = team_data['factories'] * GLOBAL_PARAMS['factory_capacity']
            st.caption(f"提示：1 座工廠 (成本 ${GLOBAL_PARAMS['factory_cost']:,}) 可容納 {GLOBAL_PARAMS['factory_capacity']} 條生產線 (P1+P2)。 "
                       f"您目前 {team_data['factories']} 座工廠，已使用 {total_lines_now} / {total_capacity_now} 條。")

        with tab_fin:
            st.subheader("財務決策")
            col1, col2 = st.columns(2)
            decision_loan = col1.number_input("本季銀行借款", min_value=0, step=100000, value=0)
            decision_repay = col2.number_input("本季償還貸款", min_value=0, step=100000, value=0)
            st.caption(f"提示：您目前的銀行借款總額為 ${team_data['BS']['bank_loan']:,.0f}。本季將產生 ${team_data['BS']['bank_loan'] * GLOBAL_PARAMS['bank_loan_interest_rate_per_season']:,.0f} 的利息費用。")
        
        # --- 提交與檢查 ---
        submitted = st.form_submit_button("提交本季決策")
        if submitted:
            # (檢查邏輯與 V1.3 相同)
            total_lines = team_data['lines_p1'] + decision_build_line_p1 + \
                          team_data['lines_p2'] + decision_build_line_p2
            total_factories = team_data['factories'] + decision_build_factory
            if total_lines > total_factories * GLOBAL_PARAMS['factory_capacity']:
                st.error(f"生產線總數 ({total_lines}) 已超過工廠容量 ({total_factories * GLOBAL_PARAMS['factory_capacity']})！")
                return 
            if decision_produce_P1 > (team_data['lines_p1'] * GLOBAL_PARAMS['line_p1_capacity']):
                st.error(f"P1 計畫產量 ({decision_produce_P1}) 超過 P1 總產能 ({team_data['lines_p1'] * GLOBAL_PARAMS['line_p1_capacity']})！")
                return
            if decision_produce_P2 > (team_data['lines_p2'] * GLOBAL_GPARAMS['line_p2_capacity']):
                st.error(f"P2 計畫產量 ({decision_produce_P2}) 超過 P2 總產能 ({team_data['lines_p2'] * GLOBAL_PARAMS['line_p2_capacity']})！")
                return

            st.session_state.decisions[team_key] = {
                'price_p1': decision_price_P1, 'ad_p1': decision_ad_P1, 'rd_p1': decision_rd_P1,
                'price_p2': decision_price_P2, 'ad_p2': decision_ad_P2, 'rd_p2': decision_rd_P2,
                'produce_p1': decision_produce_P1, 'produce_p2': decision_produce_P2,
                'buy_r1': decision_buy_R1, 'buy_r2': decision_buy_R2,
                'build_factory': decision_build_factory, 'build_line_p1': decision_build_line_p1, 'build_line_p2': decision_build_line_p2,
                'loan': decision_loan, 'repay': decision_repay
            }
            st.success(f"{team_key} 第 {st.session_state.game_season} 季決策已提交！等待老師結算...")
            st.rerun()

# --- 6. 結算引擎 (V1.2 版) ---
def run_season_calculation():
    """V2 結算引擎 (V1.2 版)，包含強制結算邏輯"""
    
    teams = st.session_state.teams
    submitted_decisions = st.session_state.decisions
    final_decisions = {}
    
    for team_key, team_data in teams.items():
        if team_key in submitted_decisions:
            final_decisions[team_key] = submitted_decisions[team_key]
        else:
            st.warning(f"警告：{team_key} 未提交決策，將使用上一季的市場決策及 0 投入。")
            final_decisions[team_key] = {
                'price_p1': team_data['MR']['price_p1'], 'ad_p1': team_data['MR']['ad_p1'],
                'price_p2': team_data['MR']['price_p2'], 'ad_p2': team_data['MR']['ad_p2'],
                'rd_p1': 0, 'rd_p2': 0, 'produce_p1': 0, 'produce_p2': 0,
                'buy_r1': 0, 'buy_r2': 0, 'build_factory': 0, 
                'build_line_p1': 0, 'build_line_p2': 0, 'loan': 0, 'repay': 0
            }

    # === 階段 1: 結算支出、生產、研發 ===
    for team_key, decision in final_decisions.items():
        team_data = teams[team_key]
        bs = team_data['BS']
        is_data = {k: 0 for k in team_data['IS']} # 重置 "本季" 損益表

        is_data['interest_expense'] = bs['bank_loan'] * GLOBAL_PARAMS['bank_loan_interest_rate_per_season']
        maint_cost = (team_data['factories'] * GLOBAL_PARAMS['factory_maintenance']) + \
                     (team_data['lines_p1'] * GLOBAL_PARAMS['line_p1_maintenance']) + \
                     (team_data['lines_p2'] * GLOBAL_PARAMS['line_p2_maintenance'])
        is_data['op_expense_maintenance'] = maint_cost
        capex_cost = (decision['build_factory'] * GLOBAL_PARAMS['factory_cost']) + \
                     (decision['build_line_p1'] * GLOBAL_PARAMS['line_p1_cost']) + \
                     (decision['build_line_p2'] * GLOBAL_PARAMS['line_p2_cost'])
        buy_R1_cost = decision['buy_r1'] * GLOBAL_PARAMS['raw_material_cost_R1']
        buy_R2_cost = decision['buy_r2'] * GLOBAL_PARAMS['raw_material_cost_R2']
        
        max_prod_p1_lines = team_data['lines_p1'] * GLOBAL_PARAMS['line_p1_capacity']
        max_prod_p1_r1 = team_data['inventory_R1_units'] / GLOBAL_PARAMS['p1_material_needed_R1']
        actual_prod_p1 = int(min(decision['produce_p1'], max_prod_p1_lines, max_prod_p1_r1))
        p1_labor_cost = actual_prod_p1 * GLOBAL_PARAMS['p1_labor_cost']
        p1_r1_used_units = actual_prod_p1 * GLOBAL_PARAMS['p1_material_needed_R1']
        
        max_prod_p2_lines = team_data['lines_p2'] * GLOBAL_PARAMS['line_p2_capacity']
        max_prod_p2_r2 = team_data['inventory_R2_units'] / GLOBAL_PARAMS['p2_material_needed_R2']
        actual_prod_p2 = int(min(decision['produce_p2'], max_prod_p2_lines, max_prod_p2_r2))
        p2_labor_cost = actual_prod_p2 * GLOBAL_PARAMS['p2_labor_cost']
        p2_r2_used_units = actual_prod_p2 * GLOBAL_PARAMS['p2_material_needed_R2']

        is_data['op_expense_ads'] = decision['ad_p1'] + decision['ad_p2']
        is_data['op_expense_rd'] = decision['rd_p1'] + decision['rd_p2']
        depr_cost = (team_data['lines_p1'] * GLOBAL_PARAMS['p1_depreciation_per_line']) + \
                    (team_data['lines_p2'] * GLOBAL_PARAMS['p2_depreciation_per_line'])
        is_data['depreciation_expense'] = depr_cost
        
        total_cash_out = maint_cost + capex_cost + buy_R1_cost + buy_R2_cost + \
                         p1_labor_cost + p2_labor_cost + \
                         is_data['op_expense_ads'] + is_data['op_expense_rd'] + \
                         decision['repay']
                         
        bs['cash'] -= total_cash_out
        bs['cash'] += decision['loan']
        
        team_data['factories'] += decision['build_factory']
        team_data['lines_p1'] += decision['build_line_p1']
        team_data['lines_p2'] += decision['build_line_p2']
        team_data['inventory_R1_units'] += decision['buy_r1']
        team_data['inventory_R1_units'] -= p1_r1_used_units
        team_data['inventory_P1_units'] += actual_prod_p1
        team_data['inventory_R2_units'] += decision['buy_r2']
        team_data['inventory_R2_units'] -= p2_r2_used_units
        team_data['inventory_P2_units'] += actual_prod_p2

        team_data['rd_investment_P1'] += decision['rd_p1']
        if team_data['rd_level_P1'] < 5:
            next_level_cost = GLOBAL_PARAMS['rd_costs_to_level_up'][team_data['rd_level_P1'] + 1]
            if team_data['rd_investment_P1'] >= next_level_cost: team_data['rd_level_P1'] += 1
        team_data['rd_investment_P2'] += decision['rd_p2']
        if team_data['rd_level_P2'] < 5:
            next_level_cost = GLOBAL_PARAMS['rd_costs_to_level_up'][team_data['rd_level_P2'] + 1]
            if team_data['rd_investment_P2'] >= next_level_cost: team_data['rd_level_P2'] += 1
                
        team_data['MR']['price_p1'] = decision['price_p1']
        team_data['MR']['ad_p1'] = decision['ad_p1']
        team_data['MR']['price_p2'] = decision['price_p2']
        team_data['MR']['ad_p2'] = decision['ad_p2']
        team_data['IS'] = is_data 

    # === 階段 2: 市場結算 (*** V1 簡化版 ***) ===
    st.warning("V1 結算引擎：使用簡化銷售模型 (未來將替換為競爭模型)")
    market_p1_data = {key: (d['ad_p1'] / 10000) / (d['price_p1'] / 300) for key, d in final_decisions.items()}
    total_score_p1 = sum(market_p1_data.values())
    TOTAL_MARKET_DEMAND_P1 = 50000 
    for team_key, score in market_p1_data.items():
        team_data = teams[team_key]; decision = final_decisions[team_key]
        market_share = (score / total_score_p1) if total_score_p1 > 0 else 0.1
        demand_units = int(TOTAL_MARKET_DEMAND_P1 * market_share)
        actual_sales_units = min(demand_units, team_data['inventory_P1_units'])
        revenue = actual_sales_units * decision['price_p1']
        team_data['BS']['cash'] += revenue
        team_data['inventory_P1_units'] -= actual_sales_units
        team_data['IS']['revenue_p1'] = revenue
        team_data['MR']['sales_units_p1'] = actual_sales_units
        team_data['MR']['market_share_p1'] = market_share

    market_p2_data = {key: (d['ad_p2'] / 10000) / (d['price_p2'] / 450) for key, d in final_decisions.items()}
    total_score_p2 = sum(market_p2_data.values())
    TOTAL_MARKET_DEMAND_P2 = 40000 
    for team_key, score in market_p2_data.items():
        team_data = teams[team_key]; decision = final_decisions[team_key]
        market_share = (score / total_score_p2) if total_score_p2 > 0 else 0.1
        demand_units = int(TOTAL_MARKET_DEMAND_P2 * market_share)
        actual_sales_units = min(demand_units, team_data['inventory_P2_units'])
        revenue = actual_sales_units * decision['price_p2']
        team_data['BS']['cash'] += revenue
        team_data['inventory_P2_units'] -= actual_sales_units
        team_data['IS']['revenue_p2'] = revenue
        team_data['MR']['sales_units_p2'] = actual_sales_units
        team_data['MR']['market_share_p2'] = market_share

    # === 階段 3: 財務報表結算 ===
    for team_key, team_data in teams.items():
        bs = team_data['BS']; is_data = team_data['IS']; decision = final_decisions[team_key]
        
        is_data['total_revenue'] = is_data['revenue_p1'] + is_data['revenue_p2']
        cogs_p1_cost = team_data['MR']['sales_units_p1'] * (GLOBAL_PARAMS['raw_material_cost_R1'] + GLOBAL_PARAMS['p1_labor_cost'])
        cogs_p2_cost = team_data['MR']['sales_units_p2'] * (GLOBAL_PARAMS['raw_material_cost_R2'] + GLOBAL_PARAMS['p2_labor_cost'])
        is_data['cogs'] = cogs_p1_cost + cogs_p2_cost
        is_data['gross_profit'] = is_data['total_revenue'] - is_data['cogs']
        is_data['total_op_expense'] = is_data['op_expense_ads'] + is_data['op_expense_rd'] + \
                                      is_data['op_expense_maintenance'] + is_data['depreciation_expense']
        is_data['operating_profit'] = is_data['gross_profit'] - is_data['total_op_expense']
        is_data['profit_before_tax'] = is_data['operating_profit'] - is_data['interest_expense']
        is_data['tax_expense'] = max(0, is_data['profit_before_tax'] * GLOBAL_PARAMS['tax_rate'])
        is_data['net_income'] = is_data['profit_before_tax'] - is_data['tax_expense']
        bs['cash'] -= is_data['tax_expense']

        bs['bank_loan'] += decision['loan']
        bs['bank_loan'] -= decision['repay']
        bs['shareholder_equity'] += is_data['net_income']
        bs['fixed_assets_value'] += (decision['build_factory'] * GLOBAL_PARAMS['factory_cost']) + \
                                    (decision['build_line_p1'] * GLOBAL_PARAMS['line_p1_cost']) + \
                                    (decision['build_line_p2'] * GLOBAL_PARAMS['line_p2_cost'])
        bs['accumulated_depreciation'] += is_data['depreciation_expense']
        
        cogs_p1_unit = GLOBAL_PARAMS['raw_material_cost_R1'] + GLOBAL_PARAMS['p1_labor_cost']
        cogs_p2_unit = GLOBAL_PARAMS['raw_material_cost_R2'] + GLOBAL_PARAMS['p2_labor_cost']
        bs['inventory_value'] = (team_data['inventory_R1_units'] * GLOBAL_PARAMS['raw_material_cost_R1']) + \
                                (team_data['inventory_R2_units'] * GLOBAL_PARAMS['raw_material_cost_R2']) + \
                                (team_data['inventory_P1_units'] * cogs_p1_unit) + \
                                (team_data['inventory_P2_units'] * cogs_p2_unit)

        bs['total_assets'] = bs['cash'] + bs['inventory_value'] + bs['fixed_assets_value'] - bs['accumulated_depreciation']
        bs['total_liabilities_and_equity'] = bs['bank_loan'] + bs['shareholder_equity']
        
        if abs(bs['total_assets'] - bs['total_liabilities_and_equity']) > 10: 
            diff = bs['total_assets'] - bs['total_liabilities_and_equity']
            bs['shareholder_equity'] += diff 
            bs['total_liabilities_and_equity'] = bs['total_assets']

        # === 階段 4: 緊急貸款 (破產檢查) ===
        if bs['cash'] < 0:
            emergency_loan = abs(bs['cash'])
            interest_penalty = emergency_loan * GLOBAL_PARAMS['emergency_loan_interest_rate']
            bs['cash'] = 0
            bs['bank_loan'] += emergency_loan
            bs['cash'] -= interest_penalty
            bs['shareholder_equity'] -= interest_penalty 
            st.error(f"{team_key} 現金不足！已強制申請 ${emergency_loan:,.0f} 的緊急貸款，並支付 ${interest_penalty:,.0f} 罰息。")

        team_data['BS'] = bs
        team_data['IS'] = is_data

    # === 階段 5: 推進遊戲 ===
    st.session_state.game_season += 1
    st.session_state.decisions = {} 
    
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")


# --- 7. (V2.0 新增) 老師專用函式 ---
def calculate_company_value(bs_data):
    """計算公司總價值 (用於排行榜)"""
    value = bs_data['cash'] + \
            bs_data['inventory_value'] + \
            (bs_data['fixed_assets_value'] - bs_data['accumulated_depreciation']) - \
            bs_data['bank_loan']
    return value

def display_admin_dashboard():
    """顯示老師的控制台畫面"""
    st.header(f"👨‍🏫 管理員控制台 (第 {st.session_state.game_season} 季)")
    
    # --- A. 排行榜 ---
    st.subheader("遊戲排行榜 (依公司總價值)")
    leaderboard = []
    for team_key in team_list:
        if team_key in st.session_state.teams:
            team_data = st.session_state.teams[team_key]
            value = calculate_company_value(team_data['BS'])
            leaderboard.append((team_key, value, team_data['BS']['cash'], team_data['IS']['net_income']))
        else:
            # 如果團隊還沒登入過，也顯示
            leaderboard.append((team_key, 0, 0, 0))
            
    leaderboard.sort(key=lambda x: x[1], reverse=True) # 依總價值排序
    
    df = pd.DataFrame(leaderboard, columns=["團隊", "公司總價值", "現金", "上季淨利"])
    df.index = df.index + 1 # 讓排名從 1 開始
    st.dataframe(df, use_container_width=True)

    # --- B. 監控面板 ---
    st.subheader("本季決策提交狀態")
    all_submitted = True 
    submitted_count = 0
    cols = st.columns(5)
    
    for i, team in enumerate(team_list):
        col = cols[i % 5]
        if team not in st.session_state.teams:
            st.session_state.teams[team] = init_team_state() # 確保所有 team 都已初始化

        if team not in st.session_state.decisions:
            col.warning(f"🟡 {team}\n(尚未提交)")
            all_submitted = False
        else:
            col.success(f"✅ {team}\n(已提交)")
            submitted_count += 1
    st.info(f"提交進度: {submitted_count} / {len(team_list)}")

    # --- C. 控制按鈕 ---
    st.subheader("遊戲控制")
    
    # ** 核心按鈕：結算本季 **
    if st.button("➡️ 結算本季"):
        if not all_submitted:
            st.warning("警告：正在強制結算。未提交的隊伍將使用預設決策。")
        
        with st.spinner("正在執行市場結算..."):
            run_season_calculation()
        st.rerun()

    if st.button("♻️ !!! 重置整個遊戲 !!!"):
        st.session_state.game_season = 1
        st.session_state.teams = {}
        st.session_state.decisions = {}
        st.session_state.logged_in_user = None # 登出所有人
        st.success("遊戲已重置回第 1 季")
        st.rerun()
    
    if st.button("登出"):
        st.session_state.logged_in_user = None
        st.rerun()

# --- 8. 主程式 (Main App) (*** V2.0 重大修改 ***) ---
st.set_page_config(layout="wide")

# --- 初始化 session_state ---
if 'game_season' not in st.session_state:
    st.session_state.game_season = 1
    st.session_state.teams = {} # 儲存 10 組公司的 "當前狀態"
    st.session_state.decisions = {} # 儲存 10 組公司的 "本季決策"
    st.session_state.logged_in_user = None # 追蹤登入狀態

# --- 登入邏輯 ---
if st.session_state.logged_in_user is None:
    st.title("🚀 新星製造 V2 - 遊戲登入")
    
    user_type = st.radio("請選擇您的身份：", ["👨‍🏫 老師 (管理員)", "🎓 學生 (玩家)"])
    
    selected_team_for_login = "admin" # 預設
    
    if user_type == "🎓 學生 (玩家)":
        selected_team_for_login = st.selectbox("請選擇您的公司 (隊伍)：", team_list)
    
    password = st.text_input("請輸入密碼：", type="password")
    
    if st.button("登入"):
        if user_type == "👨‍🏫 老師 (管理員)":
            if password == PASSWORDS["admin"]:
                st.session_state.logged_in_user = "admin"
                st.rerun()
            else:
                st.error("老師密碼錯誤！")
        
        elif user_type == "🎓 學生 (玩家)":
            if password == PASSWORDS.get(selected_team_for_login, "WRONG"):
                st.session_state.logged_in_user = selected_team_for_login
                
                # (V2.0) 確保學生登入時，該隊伍已被初始化
                if selected_team_for_login not in st.session_state.teams:
                    st.session_state.teams[selected_team_for_login] = init_team_state()
                    
                st.rerun()
            else:
                st.error(f"{selected_team_for_login} 的密碼錯誤！")

# --- 登入後的畫面 ---
else:
    # 檢查登入者身份
    current_user = st.session_state.logged_in_user
    
    if current_user == "admin":
        # --- A. 老師畫面 ---
        display_admin_dashboard()
        
    elif current_user in team_list:
        # --- B. 學生畫面 ---
        team_key = current_user
        
        # 學生登出按鈕
        if st.sidebar.button("登出"):
            st.session_state.logged_in_user = None
            st.rerun()
        st.sidebar.info(f"您已登入為： {team_key}")
        
        # (確保團隊數據存在)
        if team_key not in st.session_state.teams:
            st.session_state.teams[team_key] = init_team_state()
            
        current_team_data = st.session_state.teams[team_key]
        
        # 顯示儀表板
        display_dashboard(team_key, current_team_data)
        st.markdown("---")
        
        # 顯示決策表單或等待畫面
        if team_key in st.session_state.decisions:
            st.info(f"您已提交第 {st.session_state.game_season} 季的決策，請等待老師結算...")
            
            # (V2.0 暫不開放撤銷，未來可加入)
            # if st.button("撤銷提交 (Undo)"):
            #     del st.session_state.decisions[team_key]
            #     st.rerun()
        else:
            display_decision_form(team_key)
