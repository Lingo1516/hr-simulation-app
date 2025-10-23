# -*- coding: utf-8 -*-
# ^^^ 這一行就是修復亂碼的 "魔法指令" ^^^

# app.py (Nova Manufacturing Sim - V2-Framework-V1.1)
# 執行方式: streamlit run app.py
#
# V1.1 更新：
# 1. 在最頂部加入 "# -*- coding: utf-8 -*-" 來強制修復中文亂碼問題。

import streamlit as st
import pandas as pd
import copy

# --- 1. 遊戲參數 (V2 升級版) ---
# 這些是遊戲的 "規則" (基於 .doc 檔案推測)
GLOBAL_PARAMS = {
    'factory_cost': 5000000,
    'factory_maintenance': 100000,
    'factory_capacity': 8, # 1座工廠 = 8 條生產線 (P1+P2總和)
    
    # P1 相關
    'line_p1_cost': 1000000,
    'line_p1_maintenance': 20000,
    'line_p1_capacity': 1000, # 單位 P1 / 季
    'raw_material_cost_R1': 100,
    'p1_labor_cost': 50, # 每單位 P1 的人工成本
    'p1_material_needed_R1': 1, # 每單位 P1 需 1 單位 R1
    'p1_depreciation_per_line': 10000, # 每條P1線的折舊

    # P2 相關 (我先做合理假設)
    'line_p2_cost': 1200000, 
    'line_p2_maintenance': 25000,
    'line_p2_capacity': 800, # 單位 P2 / 季
    'raw_material_cost_R2': 150,
    'p2_labor_cost': 70, 
    'p2_material_needed_R2': 1,
    'p2_depreciation_per_line': 12000,

    # 財務
    'bank_loan_interest_rate_per_season': 0.02, # 季利率 2%
    'emergency_loan_interest_rate': 0.05, 
    'tax_rate': 0.20, # 稅率 20%
    
    # 研發
    'rd_costs_to_level_up': { 
        2: 500000, 3: 1500000, 4: 3500000, 5: 6500000
    }
}

# --- 2. 團隊狀態初始化 (V2 升級版) ---
def init_team_state():
    """定義一家公司 "出生時" 的狀態 (V2)"""
    
    # 初始資產
    initial_cash = 10000000
    initial_factories = 1
    initial_lines_p1 = 1
    initial_lines_p2 = 1
    initial_inv_r1 = 2000
    initial_inv_r2 = 2000
    initial_inv_p1 = 500
    initial_inv_p2 = 500
    
    # 初始資產價值 (用於資產負債表)
    # (簡易版：使用成本法)
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
    
    # 初始股東權益 = 初始總資產
    initial_equity = total_assets

    return {
        # --- 資產負債表 (Balance Sheet) ---
        'BS': {
            'cash': initial_cash,
            'inventory_value': inv_value,
            'fixed_assets_value': fixed_assets, # 廠房設備 (扣除折舊前)
            'accumulated_depreciation': 0, # 累計折舊
            'total_assets': total_assets,
            
            'bank_loan': 0,
            'shareholder_equity': initial_equity,
            'total_liabilities_and_equity': total_assets
        },
        
        # --- 損益表 (Income Statement) - 上一季的 ---
        'IS': {
            'revenue_p1': 0,
            'revenue_p2': 0,
            'total_revenue': 0,
            'cogs': 0, # 銷貨成本
            'gross_profit': 0,
            'op_expense_ads': 0,
            'op_expense_rd': 0,
            'op_expense_maintenance': 0,
            'depreciation_expense': 0,
            'total_op_expense': 0,
            'operating_profit': 0,
            'interest_expense': 0,
            'profit_before_tax': 0,
            'tax_expense': 0,
            'net_income': 0
        },

        # --- 非財務數據 (Internal Data) ---
        'factories': initial_factories,
        'lines_p1': initial_lines_p1,
        'lines_p2': initial_lines_p2,
        
        'inventory_R1_units': initial_inv_r1,
        'inventory_R2_units': initial_inv_r2,
        'inventory_P1_units': initial_inv_p1,
        'inventory_P2_units': initial_inv_p2,

        'rd_level_P1': 1,
        'rd_level_P2': 1,
        'rd_investment_P1': 0,
        'rd_investment_P2': 0,
        
        # --- 市場報告 (Market Report) - 上一季的 ---
        'MR': {
            'price_p1': 300,
            'ad_p1': 50000,
            'sales_units_p1': 0,
            'market_share_p1': 0.0,
            
            'price_p2': 450,
            'ad_p2': 50000,
            'sales_units_p2': 0,
            'market_share_p2': 0.0,
        }
    }

# --- 3. 儀表板 (Dashboard V2) ---
def display_dashboard(team_key, team_data):
    st.header(f"📈 {team_key} 儀表板 (第 {st.session_state.game_season} 季)")
    
    # 複製 .doc 檔案的格式
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

# --- 4. 決策表單 (Decision Form V2) ---
def display_decision_form(team_key):
    team_data = st.session_state.teams[team_key]
    
    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_key} - 第 {st.session_state.game_season} 季決策單")
        
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs(["P1 產品決策", "P2 產品決策", "生產與資本決策", "財務決策"])

        with tab_p1:
            st.subheader("P1 產品決策")
            decision_price_P1 = st.slider("P1 銷售價格", 100, 1000, value=team_data['MR']['price_p1'], step=10)
            decision_ad_P1 = st.number_input("P1 廣告費用", min_value=0, step=10000, value=team_data['MR']['ad_p1'])
            decision_rd_P1 = st.number_input("P1 研發費用", min_value=0, step=50000, value=0)
            
        with tab_p2:
            st.subheader("P2 產品決策")
            decision_price_P2 = st.slider("P2 銷售價格", 150, 1500, value=team_data['MR']['price_p2'], step=10)
            decision_ad_P2 = st.number_input("P2 廣告費用", min_value=0, step=10000, value=team_data['MR']['ad_p2'])
            decision_rd_P2 = st.number_input("P2 研發費用", min_value=0, step=50000, value=0)

        with tab_prod:
            st.subheader("生產計畫")
            col1, col2 = st.columns(2)
            decision_produce_P1 = col1.number_input("P1 計畫產量 (單位)", min_value=0, step=100, value=0)
            decision_produce_P2 = col2.number_input("P2 計畫產量 (單位)", min_value=0, step=100, value=0)

            st.subheader("原料採購")
            col1, col2 = st.columns(2)
            decision_buy_R1 = col1.number_input("採購 R1 數量 (單位)", min_value=0, step=100, value=0)
            decision_buy_R2 = col2.number_input("採購 R2 數量 (單位)", min_value=0, step=100, value=0)
            
            st.subheader("資本投資")
            col1, col2, col3 = st.columns(3)
            decision_build_factory = col1.number_input("建置新工廠 (座)", min_value=0, value=0)
            decision_build_line_p1 = col2.number_input("建置 P1 生產線 (條)", min_value=0, value=0)
            decision_build_line_p2 = col3.number_input("建置 P2 生產線 (條)", min_value=0, value=0)

        with tab_fin:
            st.subheader("財務決策")
            col1, col2 = st.columns(2)
            decision_loan = col1.number_input("本季銀行借款", min_value=0, step=100000, value=0)
            decision_repay = col2.number_input("本季償還貸款", min_value=0, step=100000, value=0)

        # --- 提交與檢查 ---
        submitted = st.form_submit_button("提交本季決策")
        
        if submitted:
            # (V2 增加更複雜的檢查)
            
            # 檢查工廠容量
            total_lines = team_data['lines_p1'] + decision_build_line_p1 + \
                          team_data['lines_p2'] + decision_build_line_p2
            total_factories = team_data['factories'] + decision_build_factory
            if total_lines > total_factories * GLOBAL_PARAMS['factory_capacity']:
                st.error(f"生產線總數 ({total_lines}) 已超過工廠容量 ({total_factories * GLOBAL_PARAMS['factory_capacity']})！")
                return # 停止提交

            # 檢查 P1 產能
            if decision_produce_P1 > (team_data['lines_p1'] * GLOBAL_PARAMS['line_p1_capacity']):
                st.error(f"P1 計畫產量 ({decision_produce_P1}) 超過 P1 總產能 ({team_data['lines_p1'] * GLOBAL_PARAMS['line_p1_capacity']})！")
                return
            
            # 檢查 P2 產能
            if decision_produce_P2 > (team_data['lines_p2'] * GLOBAL_PARAMS['line_p2_capacity']):
                st.error(f"P2 計畫產量 ({decision_produce_P2}) 超過 P2 總產能 ({team_data['lines_p2'] * GLOBAL_PARAMS['line_p2_capacity']})！")
                return

            # 儲存決策
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

# --- 5. 結算引擎 (The "Black Box" V1-Simple) ---
def run_season_calculation():
    """
    V2 結算引擎 (V1 簡化版)
    
    *** V1 簡化版：尚未加入市場競爭模型 ***
    *** V1 簡化版：財報尚未完全連動 ***
    """
    
    decisions = st.session_state.decisions
    teams = st.session_state.teams
    
    # 暫存市場數據，V2 真實版會用到
    market_p1_data = []
    market_p2_data = []

    # === 階段 1: 結算支出、生產、研發 (10 組各自獨立) ===
    for team_key, decision in decisions.items():
        team_data = teams[team_key]
        bs = team_data['BS']
        is_data = team_data['IS'] # 這是 "上一季" 的IS，我們要清空並重建
        
        # 重置 "本季" 損益表
        is_data = {k: 0 for k in is_data}

        # 1a. 財務成本 (利息)
        is_data['interest_expense'] = bs['bank_loan'] * GLOBAL_PARAMS['bank_loan_interest_rate_per_season']
        
        # 1b. 維護成本
        maint_cost = (team_data['factories'] * GLOBAL_PARAMS['factory_maintenance']) + \
                     (team_data['lines_p1'] * GLOBAL_PARAMS['line_p1_maintenance']) + \
                     (team_data['lines_p2'] * GLOBAL_PARAMS['line_p2_maintenance'])
        is_data['op_expense_maintenance'] = maint_cost
                     
        # 1c. 資本支出 (CapEx) - 影響現金和資產負債表
        capex_cost = (decision['build_factory'] * GLOBAL_PARAMS['factory_cost']) + \
                     (decision['build_line_p1'] * GLOBAL_PARAMS['line_p1_cost']) + \
                     (decision['build_line_p2'] * GLOBAL_PARAMS['line_p2_cost'])
                       
        # 1d. 原料採購
        buy_R1_cost = decision['buy_r1'] * GLOBAL_PARAMS['raw_material_cost_R1']
        buy_R2_cost = decision['buy_r2'] * GLOBAL_PARAMS['raw_material_cost_R2']
        
        # 1e. 生產 (檢查限制)
        # P1
        max_prod_p1_lines = team_data['lines_p1'] * GLOBAL_PARAMS['line_p1_capacity']
        max_prod_p1_r1 = team_data['inventory_R1_units'] / GLOBAL_PARAMS['p1_material_needed_R1']
        actual_prod_p1 = int(min(decision['produce_p1'], max_prod_p1_lines, max_prod_p1_r1))
        
        p1_labor_cost = actual_prod_p1 * GLOBAL_PARAMS['p1_labor_cost']
        p1_r1_used_units = actual_prod_p1 * GLOBAL_PARAMS['p1_material_needed_R1']
        
        # P2
        max_prod_p2_lines = team_data['lines_p2'] * GLOBAL_PARAMS['line_p2_capacity']
        max_prod_p2_r2 = team_data['inventory_R2_units'] / GLOBAL_PARAMS['p2_material_needed_R2']
        actual_prod_p2 = int(min(decision['produce_p2'], max_prod_p2_lines, max_prod_p2_r2))
        
        p2_labor_cost = actual_prod_p2 * GLOBAL_PARAMS['p2_labor_cost']
        p2_r2_used_units = actual_prod_p2 * GLOBAL_PARAMS['p2_material_needed_R2']

        # 1f. 行銷與研發
        is_data['op_expense_ads'] = decision['ad_p1'] + decision['ad_p2']
        is_data['op_expense_rd'] = decision['rd_p1'] + decision['rd_p2']
        
        # 1g. 折舊
        depr_cost = (team_data['lines_p1'] * GLOBAL_PARAMS['p1_depreciation_per_line']) + \
                    (team_data['lines_p2'] * GLOBAL_PARAMS['p2_depreciation_per_line'])
        is_data['depreciation_expense'] = depr_cost
        
        # 1h. 總現金支出 (不含利息，利息只是 IS 項目，不是本季支付)
        total_cash_out = maint_cost + capex_cost + buy_R1_cost + buy_R2_cost + \
                         p1_labor_cost + p2_labor_cost + \
                         is_data['op_expense_ads'] + is_data['op_expense_rd'] + \
                         decision['repay']
                         
        # 1i. 結算現金 (尚未加入營收)
        bs['cash'] -= total_cash_out
        bs['cash'] += decision['loan']
        
        # 1j. 結算資產與庫存 (非財報)
        team_data['factories'] += decision['build_factory']
        team_data['lines_p1'] += decision['build_line_p1']
        team_data['lines_p2'] += decision['build_line_p2']
        
        team_data['inventory_R1_units'] += decision['buy_r1']
        team_data['inventory_R1_units'] -= p1_r1_used_units
        team_data['inventory_P1_units'] += actual_prod_p1
        
        team_data['inventory_R2_units'] += decision['buy_r2']
        team_data['inventory_R2_units'] -= p2_r2_used_units
        team_data['inventory_P2_units'] += actual_prod_p2

        # 1k. 結算研發
        team_data['rd_investment_P1'] += decision['rd_p1']
        if team_data['rd_level_P1'] < 5:
            next_level_cost = GLOBAL_PARAMS['rd_costs_to_level_up'][team_data['rd_level_P1'] + 1]
            if team_data['rd_investment_P1'] >= next_level_cost:
                team_data['rd_level_P1'] += 1

        team_data['rd_investment_P2'] += decision['rd_p2']
        if team_data['rd_level_P2'] < 5:
            next_level_cost = GLOBAL_PARAMS['rd_costs_to_level_up'][team_data['rd_level_P2'] + 1]
            if team_data['rd_investment_P2'] >= next_level_cost:
                team_data['rd_level_P2'] += 1
                
        # 1l. 儲存本季決策 (用於儀表板)
        team_data['MR']['price_p1'] = decision['price_p1']
        team_data['MR']['ad_p1'] = decision['ad_p1']
        team_data['MR']['price_p2'] = decision['price_p2']
        team_data['MR']['ad_p2'] = decision['ad_p2']
        
        # 1m. 儲存IS數據
        team_data['IS'] = is_data # 存回 state

    # === 階段 2: 市場結算 (*** V2 真實版將替換此處 ***) ===
    st.warning("V1 結算引擎：使用簡化銷售模型 (未來將替換為競爭模型)")
    
    # V1 假模型：和 V1 程式一樣，10 組人搶 50k (P1) + 40k (P2) 的市場
    
    # --- P1 市場 ---
    market_p1_data = {key: (d['ad_p1'] / 10000) / (d['price_p1'] / 300) for key, d in decisions.items()}
    total_score_p1 = sum(market_p1_data.values())
    TOTAL_MARKET_DEMAND_P1 = 50000 

    for team_key, score in market_p1_data.items():
        team_data = teams[team_key]
        decision = decisions[team_key]
        
        market_share = (score / total_score_p1) if total_score_p1 > 0 else 0.1
        demand_units = int(TOTAL_MARKET_DEMAND_P1 * market_share)
        
        actual_sales_units = min(demand_units, team_data['inventory_P1_units'])
        
        revenue = actual_sales_units * decision['price_p1']
        
        team_data['BS']['cash'] += revenue
        team_data['inventory_P1_units'] -= actual_sales_units
        
        team_data['IS']['revenue_p1'] = revenue
        team_data['MR']['sales_units_p1'] = actual_sales_units
        team_data['MR']['market_share_p1'] = market_share

    # --- P2 市場 ---
    market_p2_data = {key: (d['ad_p2'] / 10000) / (d['price_p2'] / 450) for key, d in decisions.items()}
    total_score_p2 = sum(market_p2_data.values())
    TOTAL_MARKET_DEMAND_P2 = 40000 

    for team_key, score in market_p2_data.items():
        team_data = teams[team_key]
        decision = decisions[team_key]
        
        market_share = (score / total_score_p2) if total_score_p2 > 0 else 0.1
        demand_units = int(TOTAL_MARKET_DEMAND_P2 * market_share)
        
        actual_sales_units = min(demand_units, team_data['inventory_P2_units'])
        
        revenue = actual_sales_units * decision['price_p2']
        
        team_data['BS']['cash'] += revenue
        team_data['inventory_P2_units'] -= actual_sales_units
        
        team_data['IS']['revenue_p2'] = revenue
        team_data['MR']['sales_units_p2'] = actual_sales_units
        team_data['MR']['market_share_p2'] = market_share

    # === 階段 3: 財務報表結算 (V1 簡化版) ===
    for team_key, team_data in teams.items():
        bs = team_data['BS']
        is_data = team_data['IS']
        decision = decisions[team_key]
        
        # 損益表 (Income Statement)
        is_data['total_revenue'] = is_data['revenue_p1'] + is_data['revenue_p2']
        
        # (V1 簡化 COGS)
        cogs_p1_cost = team_data['MR']['sales_units_p1'] * (GLOBAL_PARAMS['raw_material_cost_R1'] + GLOBAL_PARAMS['p1_labor_cost'])
        cogs_p2_cost = team_data['MR']['sales_units_p2'] * (GLOBAL_PARAMS['raw_material_cost_R2'] + GLOBAL_PARAMS['p2_labor_cost'])
        is_data['cogs'] = cogs_p1_cost + cogs_p2_cost
        
        is_data['gross_profit'] = is_data['total_revenue'] - is_data['cogs']
        
        is_data['total_op_expense'] = is_data['op_expense_ads'] + is_data['op_expense_rd'] + \
                                      is_data['op_expense_maintenance'] + is_data['depreciation_expense']
        
        is_data['operating_profit'] = is_data['gross_profit'] - is_data['total_op_expense']
        is_data['profit_before_tax'] = is_data['operating_profit'] - is_data['interest_expense']
        
        is_data['tax_expense'] = max(0, is_data['profit_before_tax'] * GLOBAL_PARAMS['tax_rate']) # 虧損不繳稅
        is_data['net_income'] = is_data['profit_before_tax'] - is_data['tax_expense']
        
        # 結算現金 (稅金) - (V1 假設稅金本季支付)
        bs['cash'] -= is_data['tax_expense']

        # 資產負債表 (Balance Sheet)
        bs['bank_loan'] += decision['loan']
        bs['bank_loan'] -= decision['repay']
        
        # 結算權益
        bs['shareholder_equity'] += is_data['net_income'] # 淨利滾入權益
        
        # 結算資產 (V1 簡化版)
        bs['fixed_assets_value'] += (decision['build_factory'] * GLOBAL_PARAMS['factory_cost']) + \
                                    (decision['build_line_p1'] * GLOBAL_PARAMS['line_p1_cost']) + \
                                    (decision['build_line_p2'] * GLOBAL_PARAMS['line_p2_cost'])
        bs['accumulated_depreciation'] += is_data['depreciation_expense']
        
        # (V1 簡化版，真實的庫存價值計算更複雜)
        cogs_p1_unit = GLOBAL_PARAMS['raw_material_cost_R1'] + GLOBAL_PARAMS['p1_labor_cost']
        cogs_p2_unit = GLOBAL_PARAMS['raw_material_cost_R2'] + GLOBAL_PARAMS['p2_labor_cost']
        bs['inventory_value'] = (team_data['inventory_R1_units'] * GLOBAL_PARAMS['raw_material_cost_R1']) + \
                                (team_data['inventory_R2_units'] * GLOBAL_PARAMS['raw_material_cost_R2']) + \
                                (team_data['inventory_P1_units'] * cogs_p1_unit) + \
                                (team_data['inventory_P2_units'] * cogs_p2_unit)

        # 檢查平衡
        bs['total_assets'] = bs['cash'] + bs['inventory_value'] + bs['fixed_assets_value'] - bs['accumulated_depreciation']
        bs['total_liabilities_and_equity'] = bs['bank_loan'] + bs['shareholder_equity']
        
        # (V1 簡化版：如果 BS 不平衡，強制平衡，真實版 V2 必須修到平衡)
        if abs(bs['total_assets'] - bs['total_liabilities_and_equity']) > 10: # 允許 10 元內的浮點數誤差
            diff = bs['total_assets'] - bs['total_liabilities_and_equity']
            bs['shareholder_equity'] += diff # 用權益來強制平衡 (V1 簡易做法)
            bs['total_liabilities_and_equity'] = bs['total_assets']

        # === 階段 4: 緊急貸款 (破產檢查) ===
        if bs['cash'] < 0:
            emergency_loan = abs(bs['cash'])
            interest_penalty = emergency_loan * GLOBAL_PARAMS['emergency_loan_interest_rate']
            
            bs['cash'] = 0
            bs['bank_loan'] += emergency_loan
            bs['cash'] -= interest_penalty
            bs['shareholder_equity'] -= interest_penalty # 罰息作為費用，沖銷權益
            st.error(f"{team_key} 現金不足！已強制申請 ${emergency_loan:,.0f} 的緊急貸款，並支付 ${interest_penalty:,.0f} 罰息。")

        # 存回 state
        team_data['BS'] = bs
        team_data['IS'] = is_data

    # === 階段 5: 推進遊戲 ===
    st.session_state.game_season += 1
    st.session_state.decisions = {} # 清空本季決策
    
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")


# --- 6. 主程式 (Main App) ---

# --- 初始化 session_state ---
if 'game_season' not in st.session_state:
    st.session_state.game_season = 1
    st.session_state.teams = {} 
    st.session_state.decisions = {} 
    
team_list = [f"第 {i} 組 (公司 {i})" for i in range(1, 11)]

# --- 管理員面板 (Sidebar) ---
st.sidebar.title("👨‍🏫 管理員面板")
st.sidebar.header(f"當前遊戲進度：第 {st.session_state.game_season} 季")

st.sidebar.subheader("本季決策提交狀態")
all_submitted = True
submitted_count = 0
for team in team_list:
    if team not in st.session_state.decisions:
        st.sidebar.warning(f"🟡 {team}: 尚未提交")
        all_submitted = False
    else:
        st.sidebar.success(f"✅ {team}: 已提交")
        submitted_count += 1
st.sidebar.info(f"提交進度: {submitted_count} / {len(team_list)}")

# ** 核心按鈕：結算本季 **
if st.sidebar.button("➡️ 結算本季", disabled=not all_submitted):
    with st.spinner("正在執行市場結算..."):
        run_season_calculation()
    st.rerun()

if not all_submitted:
    st.sidebar.info("需所有團隊都提交決策後，才能結算本季。")

st.sidebar.markdown("---")
if st.sidebar.button("♻️ !!! 重置整個遊戲 !!!"):
    st.session_state.game_season = 1
    st.session_state.teams = {}
    st.session_state.decisions = {}
    st.success("遊戲已重置回第 1 季")
    st.rerun()

# --- 學生主畫面 (Main Screen) ---
st.title("🚀 新星製造 (Nova Manufacturing) V2 挑戰賽")
selected_team = st.selectbox("請選擇您的公司 (隊伍)：", team_list)

# --- 載入或初始化該團隊的數據 ---
if selected_team not in st.session_state.teams:
    st.session_state.teams[selected_team] = init_team_state()

# 獲取該團隊的當前數據
current_team_data = st.session_state.teams[selected_team]

# --- 顯示儀表板 ---
display_dashboard(selected_team, current_team_data)

st.markdown("---")

# --- 顯示決策表單或等待畫面 ---
if selected_team in st.session_state.decisions:
    st.info(f"您已提交第 {st.session_state.game_season} 季的決策，請等待老師結算...")
else:
    display_decision_form(selected_team)
