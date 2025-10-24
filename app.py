# -*- coding: utf-8 -*-
# Nova Manufacturing Sim - V4.3 Defensive (runnable)
import streamlit as st
import pandas as pd
import os, pickle, numbers

# ---------- 0) 檔案同步 ----------
DECISIONS_FILE = "decisions_state.pkl"

def save_decisions_to_file(decisions_dict):
    if not isinstance(decisions_dict, dict):
        decisions_dict = {}
    try:
        with open(DECISIONS_FILE, "wb") as f:
            pickle.dump(decisions_dict, f)
    except Exception as e:
        st.error(f"儲存決策檔案出錯: {e}")

def load_decisions_from_file():
    if not os.path.exists(DECISIONS_FILE):
        return {}
    try:
        with open(DECISIONS_FILE, "rb") as f:
            data = pickle.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def delete_decisions_file():
    try:
        if os.path.exists(DECISIONS_FILE):
            os.remove(DECISIONS_FILE)
    except Exception:
        pass

# ---------- 1) 參數 ----------
GLOBAL_PARAMS = {
    'factory_cost': 5_000_000,'factory_maintenance': 100_000,'factory_capacity': 8,
    'line_p1_cost': 1_000_000,'line_p1_maintenance': 20_000,'line_p1_capacity': 1_000,
    'raw_material_cost_R1': 100,'p1_labor_cost': 50,'p1_material_needed_R1': 1,'p1_depreciation_per_line': 10_000,
    'line_p2_cost': 1_200_000,'line_p2_maintenance': 25_000,'line_p2_capacity': 800,
    'raw_material_cost_R2': 150,'p2_labor_cost': 70,'p2_material_needed_R2': 1,'p2_depreciation_per_line': 12_000,
    'bank_loan_interest_rate_per_season': 0.02,'emergency_loan_interest_rate': 0.05,'tax_rate': 0.20,
    'rd_costs_to_level_up': {2: 500_000, 3: 1_500_000, 4: 3_500_000, 5: 6_500_000},
}
DEFAULT_PRICE_P1 = 300; DEFAULT_AD_P1 = 50_000
DEFAULT_PRICE_P2 = 450; DEFAULT_AD_P2 = 50_000
team_list = [f"第 {i} 組" for i in range(1, 11)]

# ---------- 2) 工具 ----------
def force_numeric(value, default=0):
    if isinstance(value, numbers.Number):
        return value
    if isinstance(value, str):
        try:
            return float(value.replace(",", ""))
        except Exception:
            return default
    return default

def balance_bs(bs):
    if not isinstance(bs, dict):
        bs = {}
    cash   = force_numeric(bs.get('cash', 0))
    inv    = force_numeric(bs.get('inventory_value', 0))
    fixed  = force_numeric(bs.get('fixed_assets_value', 0))
    depr   = force_numeric(bs.get('accumulated_depreciation', 0))
    loan   = force_numeric(bs.get('bank_loan', 0))
    equity = force_numeric(bs.get('shareholder_equity', 0))

    bs['total_assets'] = cash + inv + fixed - depr
    bs['total_liabilities_and_equity'] = loan + equity

    if abs(bs['total_assets'] - bs['total_liabilities_and_equity']) > 1:
        diff = bs['total_assets'] - bs['total_liabilities_and_equity']
        bs['shareholder_equity'] = equity + diff
        bs['total_liabilities_and_equity'] = bs['total_assets']

    keys = ['cash','inventory_value','fixed_assets_value','accumulated_depreciation',
            'total_assets','bank_loan','shareholder_equity','total_liabilities_and_equity']
    for k in keys:
        bs[k] = force_numeric(bs.get(k, 0))
    return bs

# ---------- 3) 狀態 ----------
def init_team_state(team_key):
    initial_cash = 10_000_000
    initial_factories = 1
    initial_lines_p1 = 1
    initial_lines_p2 = 1
    initial_inv_r1 = 2_000
    initial_inv_r2 = 2_000
    initial_inv_p1 = 500
    initial_inv_p2 = 500

    cogs_p1_unit = (force_numeric(GLOBAL_PARAMS.get('raw_material_cost_R1')) *
                    force_numeric(GLOBAL_PARAMS.get('p1_material_needed_R1')) +
                    force_numeric(GLOBAL_PARAMS.get('p1_labor_cost')))
    cogs_p2_unit = (force_numeric(GLOBAL_PARAMS.get('raw_material_cost_R2')) *
                    force_numeric(GLOBAL_PARAMS.get('p2_material_needed_R2')) +
                    force_numeric(GLOBAL_PARAMS.get('p2_labor_cost')))

    inv_value = initial_inv_r1*force_numeric(GLOBAL_PARAMS.get('raw_material_cost_R1')) + \
                initial_inv_r2*force_numeric(GLOBAL_PARAMS.get('raw_material_cost_R2')) + \
                initial_inv_p1*cogs_p1_unit + initial_inv_p2*cogs_p2_unit

    fixed_assets = (initial_factories*force_numeric(GLOBAL_PARAMS.get('factory_cost')) +
                    initial_lines_p1*force_numeric(GLOBAL_PARAMS.get('line_p1_cost')) +
                    initial_lines_p2*force_numeric(GLOBAL_PARAMS.get('line_p2_cost')))

    bs = balance_bs({
        'cash': initial_cash,
        'inventory_value': inv_value,
        'fixed_assets_value': fixed_assets,
        'accumulated_depreciation': 0,
        'bank_loan': 0,
        'shareholder_equity': initial_cash + inv_value + fixed_assets,
    })

    is_keys = ['revenue_p1','revenue_p2','total_revenue','cogs','gross_profit',
               'op_expense_maintenance','interest_expense','ad_expense','rd_expense',
               'profit_before_tax','tax_expense','net_income']
    is_data = {k:0 for k in is_keys}
    mr = {'price_p1': DEFAULT_PRICE_P1, 'ad_p1': DEFAULT_AD_P1,
          'price_p2': DEFAULT_PRICE_P2, 'ad_p2': DEFAULT_AD_P2,
          'sales_units_p1': 0, 'sales_units_p2': 0,
          'market_share_p1': 0.0, 'market_share_p2': 0.0}

    return {
        'team_name': str(team_key),
        'factories': initial_factories, 'lines_p1': initial_lines_p1, 'lines_p2': initial_lines_p2,
        'inventory_R1_units': initial_inv_r1, 'inventory_R2_units': initial_inv_r2,
        'inventory_P1_units': initial_inv_p1, 'inventory_P2_units': initial_inv_p2,
        'rd_level_P1': 1, 'rd_level_P2': 1, 'rd_investment_P1': 0, 'rd_investment_P2': 0,
        'BS': bs, 'IS': is_data, 'MR': mr,
    }

# ---------- 4) UI ----------
def display_dashboard(team_key, team_data):
    if not isinstance(team_data, dict):
        team_data = init_team_state(team_key)
    st.header(f"📈 {team_data.get('team_name', team_key)} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data.get('BS', {}); is_data = team_data.get('IS', {}); mr = team_data.get('MR', {})
    st.subheader("📊 市場報告 (上季)"); st.write(pd.DataFrame([mr]))
    st.subheader("💰 損益表 (上季)"); st.metric("稅後淨利", f"${force_numeric(is_data.get('net_income',0)):,.0f}")
    with st.expander("損益表明細"): st.write(is_data)
    st.subheader("🏦 資產負債表 (當前)"); st.metric("總資產", f"${force_numeric(bs.get('total_assets',0)):,.0f}")
    with st.expander("資產負債表明細"): st.write(bs)
    c1,c2,c3 = st.columns(3)
    c1.metric("工廠", force_numeric(team_data.get('factories',0)))
    c2.metric("P1 線", force_numeric(team_data.get('lines_p1',0)))
    c3.metric("P2 線", force_numeric(team_data.get('lines_p2',0)))
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("R1 庫存", f"{force_numeric(team_data.get('inventory_R1_units',0)):,.0f}")
    c2.metric("P1 庫存", f"{force_numeric(team_data.get('inventory_P1_units',0)):,.0f}")
    c3.metric("R2 庫存", f"{force_numeric(team_data.get('inventory_R2_units',0)):,.0f}")
    c4.metric("P2 庫存", f"{force_numeric(team_data.get('inventory_P2_units',0)):,.0f}")

def display_decision_form(team_key):
    t = st.session_state.teams.get(team_key, init_team_state(team_key))
    with st.form(f"decision_form_{team_key}", clear_on_submit=False):
        st.header(f"📝 {t.get('team_name', team_key)} - 第 {st.session_state.game_season} 季決策單")
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs(["P1 產品", "P2 產品", "生產/資本", "財務"])

        with tab_p1:
            price_p1 = st.number_input("P1 價格", min_value=1, value=int(force_numeric(t.get('MR',{}).get('price_p1', DEFAULT_PRICE_P1))))
            ad_p1    = st.number_input("P1 廣告", min_value=0, step=10_000, value=int(force_numeric(t.get('MR',{}).get('ad_p1', DEFAULT_AD_P1))))
            prod_p1  = st.number_input("P1 生產量", min_value=0, value=0)

        with tab_p2:
            price_p2 = st.number_input("P2 價格", min_value=1, value=int(force_numeric(t.get('MR',{}).get('price_p2', DEFAULT_PRICE_P2))))
            ad_p2    = st.number_input("P2 廣告", min_value=0, step=10_000, value=int(force_numeric(t.get('MR',{}).get('ad_p2', DEFAULT_AD_P2))))
            prod_p2  = st.number_input("P2 生產量", min_value=0, value=0)

        with tab_prod:
            buy_r1 = st.number_input("購買 R1 原料(單位)", min_value=0, value=0)
            buy_r2 = st.number_input("購買 R2 原料(單位)", min_value=0, value=0)
            build_factory = st.number_input("新建工廠(座)", min_value=0, value=0)
            add_lines_p1  = st.number_input("新增 P1 產線(條)", min_value=0, value=0)
            add_lines_p2  = st.number_input("新增 P2 產線(條)", min_value=0, value=0)

        with tab_fin:
            loan  = st.number_input("舉借銀行貸款", min_value=0, step=100_000, value=0)
            repay = st.number_input("償還銀行貸款", min_value=0, step=100_000, value=0)

        submitted = st.form_submit_button("提交本季決策")
        if submitted:
            decisions = load_decisions_from_file()
            decisions[team_key] = {
                'price_p1': int(force_numeric(price_p1, DEFAULT_PRICE_P1)),
                'ad_p1': int(force_numeric(ad_p1, 0)),
                'produce_p1': int(force_numeric(prod_p1, 0)),
                'price_p2': int(force_numeric(price_p2, DEFAULT_PRICE_P2)),
                'ad_p2': int(force_numeric(ad_p2, 0)),
                'produce_p2': int(force_numeric(prod_p2, 0)),
                'buy_r1': int(force_numeric(buy_r1, 0)),
                'buy_r2': int(force_numeric(buy_r2, 0)),
                'build_factory': int(force_numeric(build_factory, 0)),
                'add_lines_p1': int(force_numeric(add_lines_p1, 0)),
                'add_lines_p2': int(force_numeric(add_lines_p2, 0)),
                'loan': int(force_numeric(loan, 0)),
                'repay': int(force_numeric(repay, 0)),
            }
            save_decisions_to_file(decisions)
            st.success("✅ 已提交！")

# ---------- 5) 結算 ----------
def run_season_calculation():
    teams = st.session_state.teams
    decisions = load_decisions_from_file()

    for team_key in team_list:
        if team_key not in teams:
            teams[team_key] = init_team_state(team_key)

        t = teams[team_key]
        d = decisions.get(team_key, {})
        bs = t.get('BS', {})
        is_data = {k:0 for k in t.get('IS',{}).keys()} if isinstance(t.get('IS',{}), dict) else {}

        # 資本支出
        build_f = int(force_numeric(d.get('build_factory',0)))
        add_l1  = int(force_numeric(d.get('add_lines_p1',0)))
        add_l2  = int(force_numeric(d.get('add_lines_p2',0)))
        capex = build_f*GLOBAL_PARAMS['factory_cost'] + \
                add_l1*GLOBAL_PARAMS['line_p1_cost'] + \
                add_l2*GLOBAL_PARAMS['line_p2_cost']
        t['factories'] += build_f
        t['lines_p1'] += add_l1
        t['lines_p2'] += add_l2
        bs['fixed_assets_value'] = force_numeric(bs.get('fixed_assets_value',0)) + capex
        bs['cash'] = force_numeric(bs.get('cash',0)) - capex

        # 貸款
        loan = int(force_numeric(d.get('loan',0))); repay = int(force_numeric(d.get('repay',0)))
        bs['bank_loan'] = force_numeric(bs.get('bank_loan',0)) + loan - repay
        bs['cash'] += loan - repay
        is_data['interest_expense'] = force_numeric(bs['bank_loan'])*GLOBAL_PARAMS['bank_loan_interest_rate_per_season']

        # 維護費
        maint = (t['factories']*GLOBAL_PARAMS['factory_maintenance'] +
                 t['lines_p1']*GLOBAL_PARAMS['line_p1_maintenance'] +
                 t['lines_p2']*GLOBAL_PARAMS['line_p2_maintenance'])
        is_data['op_expense_maintenance'] = maint
        bs['cash'] -= maint

        # 原料
        buy_r1 = int(force_numeric(d.get('buy_r1',0))); buy_r2 = int(force_numeric(d.get('buy_r2',0)))
        cost_r1 = buy_r1*GLOBAL_PARAMS['raw_material_cost_R1']
        cost_r2 = buy_r2*GLOBAL_PARAMS['raw_material_cost_R2']
        bs['cash'] -= (cost_r1 + cost_r2)
        t['inventory_R1_units'] += buy_r1
        t['inventory_R2_units'] += buy_r2

        # 生產（受產能/原料限制）
        want_p1 = int(force_numeric(d.get('produce_p1',0)))
        want_p2 = int(force_numeric(d.get('produce_p2',0)))
        max_p1 = min(t['lines_p1']*GLOBAL_PARAMS['line_p1_capacity'],
                     t['inventory_R1_units']//GLOBAL_PARAMS['p1_material_needed_R1'])
        max_p2 = min(t['lines_p2']*GLOBAL_PARAMS['line_p2_capacity'],
                     t['inventory_R2_units']//GLOBAL_PARAMS['p2_material_needed_R2'])
        prod_p1 = min(want_p1, max_p1)
        prod_p2 = min(want_p2, max_p2)
        t['inventory_R1_units'] -= prod_p1*GLOBAL_PARAMS['p1_material_needed_R1']
        t['inventory_R2_units'] -= prod_p2*GLOBAL_PARAMS['p2_material_needed_R2']
        t['inventory_P1_units'] += prod_p1
        t['inventory_P2_units'] += prod_p2

        # 銷售（示意：賣掉 50% 庫存）
        price_p1 = max(1, int(force_numeric(d.get('price_p1', DEFAULT_PRICE_P1))))
        price_p2 = max(1, int(force_numeric(d.get('price_p2', DEFAULT_PRICE_P2))))
        sell_p1 = t['inventory_P1_units']//2
        sell_p2 = t['inventory_P2_units']//2
        t['inventory_P1_units'] -= sell_p1
        t['inventory_P2_units'] -= sell_p2
        rev_p1 = sell_p1*price_p1; rev_p2 = sell_p2*price_p2
        is_data['revenue_p1'] = rev_p1; is_data['revenue_p2'] = rev_p2
        is_data['total_revenue'] = rev_p1 + rev_p2
        bs['cash'] += is_data['total_revenue']

        # COGS（簡化）
        cogs_p1 = sell_p1*(GLOBAL_PARAMS['raw_material_cost_R1'] + GLOBAL_PARAMS['p1_labor_cost'])
        cogs_p2 = sell_p2*(GLOBAL_PARAMS['raw_material_cost_R2'] + GLOBAL_PARAMS['p2_labor_cost'])
        is_data['cogs'] = cogs_p1 + cogs_p2
        is_data['gross_profit'] = is_data['total_revenue'] - is_data['cogs']

        # 廣告
        ad = int(force_numeric(d.get('ad_p1',0))) + int(force_numeric(d.get('ad_p2',0)))
        is_data['ad_expense'] = ad
        bs['cash'] -= ad

        # 稅前/稅後
        pbt = is_data['gross_profit'] - is_data['op_expense_maintenance'] - is_data['interest_expense'] - is_data['ad_expense']
        is_data['profit_before_tax'] = pbt
        tax = max(0, pbt*GLOBAL_PARAMS['tax_rate'])
        is_data['tax_expense'] = tax
        is_data['net_income'] = pbt - tax
        bs['cash'] -= tax
        bs['shareholder_equity'] = force_numeric(bs.get('shareholder_equity',0)) + is_data['net_income']

        # 更新
        t['MR']['sales_units_p1'] = sell_p1
        t['MR']['sales_units_p2'] = sell_p2
        t['IS'] = is_data
        t['BS'] = balance_bs(bs)

        # 緊急貸款（現金為負）
        if t['BS']['cash'] < 0:
            need = -t['BS']['cash']
            pen = need*GLOBAL_PARAMS['emergency_loan_interest_rate']
            t['BS']['cash'] = 0
            t['BS']['bank_loan'] += need
            t['BS']['cash'] -= pen
            t['BS']['shareholder_equity'] -= pen
            t['BS'] = balance_bs(t['BS'])

    st.session_state.game_season += 1
    delete_decisions_file()
    st.success(f"✅ 第 {st.session_state.game_season-1} 季結算完畢 → 進入第 {st.session_state.game_season} 季")

# ---------- 6) Admin ----------
def calculate_company_value(bs):
    bs = bs or {}
    return (force_numeric(bs.get('cash',0)) +
            force_numeric(bs.get('inventory_value',0)) +
            (force_numeric(bs.get('fixed_assets_value',0)) - force_numeric(bs.get('accumulated_depreciation',0))) -
            force_numeric(bs.get('bank_loan',0)))

def display_admin_dashboard():
    st.header(f"👨‍🏫 管理員控制台 (第 {st.session_state.game_season} 季)")
    rows = [{"team": k, "company_value": calculate_company_value(t.get('BS',{}))}
            for k,t in st.session_state.teams.items()]
    df = pd.DataFrame(rows).sort_values("company_value", ascending=False)
    st.table(df)
    if st.button("🚀 進行結算 (Run Season)"):
        run_season_calculation()

# ---------- 7) 主程式 ----------
st.set_page_config(layout="wide")
if 'game_season' not in st.session_state:
    st.session_state.game_season = 1
if 'teams' not in st.session_state:
    st.session_state.teams = {k: init_team_state(k) for k in team_list}
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = "admin"  # 先免登入

st.title("Nova Manufacturing Sim — V4.3 Defensive (Runnable)")
tab1, tab2 = st.tabs(["學生端", "老師端"])
with tab1:
    team_key = st.selectbox("選擇隊伍", team_list, index=0)
    display_dashboard(team_key, st.session_state.teams.get(team_key))
    st.divider()
    display_decision_form(team_key)
with tab2:
    display_admin_dashboard()
