# app.py (Nova Manufacturing Sim - V1)
# 執行方式: streamlit run app.py

import streamlit as st
import pandas as pd

# --- 1. 遊戲參數 (來自 基本參數.csv) ---
# 這些是遊戲的 "規則"
GLOBAL_PARAMS = {
    'factory_cost': 5000000,
    'factory_maintenance': 100000,
    'factory_capacity': 4, # 條生產線
    
    'line_cost': 1000000,
    'line_maintenance': 20000,
    'line_capacity': 1000, # 單位 P1
    
    'raw_material_cost_R1': 100,
    'p1_labor_cost': 50, # 每單位 P1 的人工成本
    'p1_material_needed_R1': 1, # 每單位 P1 需 1 單位 R1
    
    'bank_loan_interest_rate_per_season': 0.02, # 季利率 2%
    'emergency_loan_interest_rate': 0.05, # 現金不足的罰息
    
    'rd_costs_to_level_up': { # 升到下一級所需的 "累計" 投入
        2: 500000,
        3: 1500000, # 500k + 1M
        4: 3500000, # 1.5M + 2M
        5: 6500000  # 3.5M + 3M
    }
}

# --- 2. 團隊狀態初始化 ---
def init_team_state():
    """定義一家公司 "出生時" 的狀態"""
    return {
        # 財務
        'cash': 10000000, # 初始現金
        'bank_loan': 0,     # 銀行借款
        
        # 資產
        'factories': 1,
        'lines': 2,
        
        # 庫存 (單位)
        'inventory_R1': 5000, # 原料
        'inventory_P1': 1000, # 產品
        
        # 市場
        'rd_level_P1': 1,
        'rd_investment_P1': 0, # 累計研發投入
        
        # 上一季的決策 (用於顯示在儀表板)
        'last_price_P1': 300,
        'last_ad_P1': 50000,
        
        # 上一季的結果 (用於顯示在儀表板)
        'last_sales_units_P1': 0,
        'last_market_share_P1': 0.0,
        'last_revenue_P1': 0,
        'last_profit': 0
    }

# --- 3. 儀表板 (Dashboard) ---
def display_dashboard(team_key, team_data):
    st.header(f"📈 {team_key} 儀表板 (第 {st.session_state.game_season} 季)")
    st.subheader("財務狀況")
    col1, col2 = st.columns(2)
    col1.metric("🏦 現金", f"${team_data['cash']:,.0f}")
    col2.metric("💸 銀行總借款", f"${team_data['bank_loan']:,.0f}")

    st.subheader("資產與庫存")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏭 工廠 (座)", team_data['factories'])
    col2.metric("🔩 生產線 (條)", team_data['lines'])
    col3.metric("📦 原料 R1 (單位)", f"{team_data['inventory_R1']:,.0f}")
    col4.metric("🏭 產品 P1 (單位)", f"{team_data['inventory_P1']:,.0f}")

    st.subheader("市場狀況")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔬 研發等級 (P1)", f"L {team_data['rd_level_P1']}")
    col2.metric("💲 上季價格 (P1)", f"${team_data['last_price_P1']}")
    col3.metric("📢 上季廣告 (P1)", f"${team_data['last_ad_P1']:,.0f}")
    col4.metric("📊 上季市佔率 (P1)", f"{team_data['last_market_share_P1']:.2%}")
    
    st.subheader("上季損益")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 上季營收", f"${team_data['last_revenue_P1']:,.0f}")
    col2.metric("📈 上季銷量 (單位)", f"{team_data['last_sales_units_P1']:,.0f}")
    col3.metric("💹 上季淨利", f"${team_data['last_profit']:,.0f}")

# --- 4. 決策表單 (Decision Form) ---
def display_decision_form(team_key):
    team_data = st.session_state.teams[team_key]
    
    with st.form(f"decision_form_{team_key}"):
        st.header(f"📝 {team_key} - 第 {st.session_state.game_season} 季決策單")
        
        st.subheader("財務決策")
        col1, col2 = st.columns(2)
        decision_loan = col1.number_input("本季銀行借款", min_value=0, step=100000, value=0)
        decision_repay = col2.number_input("本季償還貸款", min_value=0, step=100000, value=0)
        if decision_repay > team_data['bank_loan']:
            st.warning("償還金額超過總借款！")

        st.subheader("資本決策")
        col1, col2 = st.columns(2)
        decision_build_factory = col1.number_input("建置新工廠 (座)", min_value=0, max_value=5, value=0)
        decision_build_line = col2.number_input("建置新生產線 (條)", min_value=0, max_value=20, value=0)
        total_lines = team_data['lines'] + decision_build_line
        total_factories = team_data['factories'] + decision_build_factory
        if total_lines > total_factories * GLOBAL_PARAMS['factory_capacity']:
            st.error(f"生產線總數 ({total_lines}) 已超過工廠容量 ({total_factories * GLOBAL_PARAMS['factory_capacity']})！")

        st.subheader("生產決策")
        col1, col2 = st.columns(2)
        decision_buy_R1 = col1.number_input("採購原料 (R1) 單位", min_value=0, step=100, value=0)
        decision_produce_P1 = col2.number_input("計畫生產產品 (P1) 單位", min_value=0, step=100, value=0)
        if decision_produce_P1 > team_data['lines'] * GLOBAL_PARAMS['line_capacity']:
            st.warning(f"計畫產量 ({decision_produce_P1}) 超過總產能 ({team_data['lines'] * GLOBAL_PARAMS['line_capacity']})！")
        
        materials_needed = decision_produce_P1 * GLOBAL_PARAMS['p1_material_needed_R1']
        if materials_needed > team_data['inventory_R1']:
             st.warning(f"原料不足！(需求: {materials_needed}, 現有: {team_data['inventory_R1']})")


        st.subheader("行銷決策")
        col1, col2 = st.columns(2)
        decision_price_P1 = col1.slider("設定 P1 銷售價格", 100, 1000, value=300, step=10)
        decision_ad_P1 = col2.number_input("投入 P1 廣告費用", min_value=0, step=50000, value=50000)

        st.subheader("研發決策")
        decision_rd_P1 = st.number_input("投入 P1 研發費用", min_value=0, step=100000, value=0)
        
        submitted = st.form_submit_button("提交本季決策")
        
    if submitted:
        # 僅儲存決策，等待管理員結算
        st.session_state.decisions[team_key] = {
            'loan': decision_loan,
            'repay': decision_repay,
            'build_factory': decision_build_factory,
            'build_line': decision_build_line,
            'buy_R1': decision_buy_R1,
            'produce_P1': decision_produce_P1,
            'price_P1': decision_price_P1,
            'ad_P1': decision_ad_P1,
            'rd_P1': decision_rd_P1
        }
        st.success(f"{team_key} 第 {st.session_state.game_season} 季決策已提交！等待老師結算...")
        st.rerun()

# --- 5. 結算引擎 (The "Black Box") ---
def run_season_calculation():
    """
    這是遊戲的核心引擎。它會在管理員按下按鈕後執行。
    它會讀取所有 'st.session_state.decisions' 的數據，
    然後更新所有 'st.session_state.teams' 的數據。
    
    *** V1 簡化版：尚未加入市場競爭模型 ***
    """
    
    decisions = st.session_state.decisions
    teams = st.session_state.teams
    
    # 暫存每隊的淨利，用於儀表板
    team_profits = {}
    
    # === 階段 1: 支出與生產 ===
    # (先結算所有支出和生產，因為這會影響庫存)
    for team_key, decision in decisions.items():
        team_data = teams[team_key]
        
        # 1a. 財務成本 (利息)
        interest_cost = team_data['bank_loan'] * GLOBAL_PARAMS['bank_loan_interest_rate_per_season']
        
        # 1b. 維護成本
        maint_cost = (team_data['factories'] * GLOBAL_PARAMS['factory_maintenance']) + \
                     (team_data['lines'] * GLOBAL_PARAMS['line_maintenance'])
                     
        # 1c. 資本支出
        capital_cost = (decision['build_factory'] * GLOBAL_PARAMS['factory_cost']) + \
                       (decision['build_line'] * GLOBAL_PARAMS['line_cost'])
                       
        # 1d. 原料採購
        buy_R1_cost = decision['buy_R1'] * GLOBAL_PARAMS['raw_material_cost_R1']
        
        # 1e. 生產 (檢查限制)
        max_production_by_lines = team_data['lines'] * GLOBAL_PARAMS['line_capacity']
        max_production_by_R1 = team_data['inventory_R1'] / GLOBAL_PARAMS['p1_material_needed_R1']
        
        actual_production = min(decision['produce_P1'], max_production_by_lines, max_production_by_R1)
        actual_production = int(actual_production) # 確保是整數
        
        production_labor_cost = actual_production * GLOBAL_PARAMS['p1_labor_cost']
        production_R1_cost = actual_production * GLOBAL_PARAMS['p1_material_needed_R1'] # 這是扣庫存
        
        # 1f. 行銷與研發
        marketing_cost = decision['ad_P1'] + decision['rd_P1']
        
        # 1g. 總支出 (不含利息，利息是損益表項目)
        total_cash_out = maint_cost + capital_cost + buy_R1_cost + \
                         production_labor_cost + marketing_cost + decision['repay']
                         
        # 1h. 結算現金
        team_data['cash'] -= total_cash_out
        team_data['cash'] += decision['loan']
        
        # 1i. 結算資產與庫存
        team_data['factories'] += decision['build_factory']
        team_data['lines'] += decision['build_line']
        team_data['inventory_R1'] += decision['buy_R1']
        team_data['inventory_R1'] -= production_R1_cost # 扣 R1 庫存
        team_data['inventory_P1'] += actual_production # 加 P1 庫存
        
        # 1j. 結算財務
        team_data['bank_loan'] += decision['loan']
        team_data['bank_loan'] -= decision['repay']
        
        # 1k. 結算研發
        team_data['rd_investment_P1'] += decision['rd_P1']
        current_level = team_data['rd_level_P1']
        if current_level < 5:
            next_level_cost = GLOBAL_PARAMS['rd_costs_to_level_up'][current_level + 1]
            if team_data['rd_investment_P1'] >= next_level_cost:
                team_data['rd_level_P1'] += 1
                # (簡易版：升級後不清零，持續累計)
        
        # 1l. 儲存上季決策 (用於儀表板)
        team_data['last_price_P1'] = decision['price_P1']
        team_data['last_ad_P1'] = decision['ad_P1']
        
        # 暫存成本 (用於計算淨利)
        team_profits[team_key] = {
            'total_cost_of_goods': 0, # V1 簡化
            'operating_expense': maint_cost + marketing_cost,
            'interest_cost': interest_cost
        }

    # === 階段 2: 市場結算 (*** V2 才會加入的黑盒子 ***) ===
    # V1 簡化版：假設一個超簡單的銷售
    # 這裡未來會替換成您要的複雜競爭模型
    st.warning("V1 結算引擎：使用簡化銷售模型 (未來將替換為競爭模型)")
    
    total_sales_units_all_teams = 0
    temp_sales_data = {}
    
    for team_key, decision in decisions.items():
        team_data = teams[team_key]
        
        # V1 假模型：價格越低、廣告越高，賣越好
        # (這只是個占位符，不要當真)
        sales_score = (decision['ad_P1'] / 10000) / (decision['price_P1'] / 300)
        temp_sales_data[team_key] = sales_score
    
    total_score = sum(temp_sales_data.values())
    TOTAL_MARKET_DEMAND_V1 = 50000 # V1 假設總市場需求 5 萬

    for team_key, score in temp_sales_data.items():
        team_data = teams[team_key]
        decision = decisions[team_key]
        
        market_share = (score / total_score) if total_score > 0 else 0.1
        demand_units = int(TOTAL_MARKET_DEMAND_V1 * market_share)
        
        # 實際銷量 = min(市場需求, 你的庫存)
        actual_sales_units = min(demand_units, team_data['inventory_P1'])
        
        # 結算
        revenue = actual_sales_units * decision['price_P1']
        
        team_data['cash'] += revenue
        team_data['inventory_P1'] -= actual_sales_units
        
        # 更新儀表板數據
        team_data['last_sales_units_P1'] = actual_sales_units
        team_data['last_market_share_P1'] = market_share
        team_data['last_revenue_P1'] = revenue
        
        # 計算淨利 (簡易版)
        profit = revenue - team_profits[team_key]['operating_expense'] - team_profits[team_key]['interest_cost']
        team_data['last_profit'] = profit

    # === 階段 3: 財務結算 (檢查破產) ===
    for team_key, team_data in teams.items():
        if team_data['cash'] < 0:
            # 現金不足，強制緊急貸款
            emergency_loan = abs(team_data['cash'])
            interest_penalty = emergency_loan * GLOBAL_PARAMS['emergency_loan_interest_rate']
            
            team_data['cash'] = 0 # 補足現金
            team_data['bank_loan'] += emergency_loan # 計入總借款
            team_data['cash'] -= interest_penalty # 扣除罰息
            st.error(f"{team_key} 現金不足！已強制申請 ${emergency_loan:,.0f} 的緊急貸款，並支付 ${interest_penalty:,.0f} 罰息。")
            
            # (如果罰息又導致現金為負，在下一季會再次觸發)

    # === 階段 4: 推進遊戲 ===
    st.session_state.game_season += 1
    st.session_state.decisions = {} # 清空本季決策，準備下一季
    
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")


# --- 6. 主程式 (Main App) ---

# --- 初始化 session_state ---
if 'game_season' not in st.session_state:
    st.session_state.game_season = 1
    st.session_state.teams = {} # 儲存 10 組公司的 "當前狀態"
    st.session_state.decisions = {} # 儲存 10 組公司的 "本季決策"
    
team_list = [f"第 {i} 組 (公司 {i})" for i in range(1, 11)]

# --- 管理員面板 (Sidebar) ---
st.sidebar.title("👨‍🏫 管理員面板")
st.sidebar.header(f"當前遊戲進度：第 {st.session_state.game_season} 季")

# 顯示決策提交狀態
st.sidebar.subheader("本季決策提交狀態")
all_submitted = True
for team in team_list:
    if team not in st.session_state.decisions:
        st.sidebar.warning(f"🟡 {team}: 尚未提交")
        all_submitted = False
    else:
        st.sidebar.success(f"✅ {team}: 已提交")

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
st.title("🚀 新星製造 (Nova Manufacturing) 挑戰賽")
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
    # (可以考慮顯示一個 '撤銷提交' 的按鈕，但 V1 先不加)
else:
    display_decision_form(selected_team)
