# -*- coding: utf-8 -*-
# Nova Manufacturing Sim — V4.3 Classroom (Passwords + Tasks/Risks + Tracking)
import streamlit as st
import pandas as pd
import os, pickle, numbers, time
from datetime import datetime

# ---------- 0) 檔案 ----------
DECISIONS_FILE = "decisions_state.pkl"    # 存放各季各組「提交內容 + 提交狀態」
STATE_FILE     = "game_state.pkl"         # 可擴充保存其他全域狀態（目前僅示意）

# ---------- 1) 密碼 ----------
PASSWORDS = {
    "admin": "admin123",
    "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660",
    "第 7 組": "ice112", "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526",
}
TEAM_LIST = [f"第 {i} 組" for i in range(1, 11)]

# ---------- 2) 每季任務與風險（可自行編輯） ----------
SEASON_BRIEFS = {
    1: {
        "task": "建立基本產能與定價策略：決定是否擴充產線、設定 P1/P2 價格與廣告。",
        "risk": "過度擴張導致現金吃緊；定價過低拉高銷量但毛利不足。"
    },
    2: {
        "task": "優化供應鏈與存貨：補足 R1/R2 原料、避免缺料導致停線。",
        "risk": "過多庫存佔用現金；過少庫存使產能閒置。"
    },
    3: {
        "task": "導入研發與品牌：配置 RD 與廣告，以提升長期競爭力。",
        "risk": "短期獲利下滑；若市場需求不如預期，回收期拉長。"
    },
    # 後續季可照此擴充
}

# ---------- 3) 參數 ----------
GLOBAL_PARAMS = {
    'factory_cost': 5_000_000,'factory_maintenance': 100_000,'factory_capacity': 8,
    'line_p1_cost': 1_000_000,'line_p1_maintenance': 20_000,'line_p1_capacity': 1_000,
    'raw_material_cost_R1': 100,'p1_labor_cost': 50,'p1_material_needed_R1': 1,'p1_depreciation_per_line': 10_000,
    'line_p2_cost': 1_200_000,'line_p2_maintenance': 25_000,'line_p2_capacity': 800,
    'raw_material_cost_R2': 150,'p2_labor_cost': 70,'p2_material_needed_R2': 1,'p2_depreciation_per_line': 12_000,
    'bank_loan_interest_rate_per_season': 0.02,'emergency_loan_interest_rate': 0.05,'tax_rate': 0.20,
}
DEF_PRICE_P1 = 300; DEF_AD_P1 = 50_000
DEF_PRICE_P2 = 450; DEF_AD_P2 = 50_000

# ---------- 4) 工具 ----------
def force_numeric(v, default=0):
    if isinstance(v, numbers.Number): return v
    if isinstance(v, str):
        try: return float(v.replace(",", ""))
        except Exception: return default
    return default

def balance_bs(bs):
    if not isinstance(bs, dict): bs = {}
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
    for k in ['cash','inventory_value','fixed_assets_value','accumulated_depreciation',
              'total_assets','bank_loan','shareholder_equity','total_liabilities_and_equity']:
        bs[k] = force_numeric(bs.get(k, 0))
    return bs

def save_decisions(data):
    with open(DECISIONS_FILE, "wb") as f:
        pickle.dump(data, f)

def load_decisions():
    if not os.path.exists(DECISIONS_FILE): return {}
    try:
        with open(DECISIONS_FILE, "rb") as f:
            d = pickle.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}

# ---------- 5) 初始狀態 ----------
def init_team_state(team_key):
    initial_cash = 10_000_000
    fixed_assets = 5_000_000 + 1_000_000 + 1_200_000  # 工廠1 + P1線1 + P2線1
    bs = balance_bs({
        'cash': initial_cash, 'inventory_value': 0,
        'fixed_assets_value': fixed_assets, 'accumulated_depreciation': 0,
        'bank_loan': 0, 'shareholder_equity': initial_cash + fixed_assets,
    })
    is_keys = ['revenue_p1','revenue_p2','total_revenue','cogs','gross_profit',
               'op_expense_maintenance','interest_expense','ad_expense','rd_expense',
               'profit_before_tax','tax_expense','net_income']
    return {
        'team_name': str(team_key), 'factories': 1, 'lines_p1': 1, 'lines_p2': 1,
        'inventory_R1_units': 2000, 'inventory_R2_units': 2000,
        'inventory_P1_units': 500, 'inventory_P2_units': 500,
        'rd_level_P1': 1, 'rd_level_P2': 1, 'rd_investment_P1': 0, 'rd_investment_P2': 0,
        'BS': bs, 'IS': {k:0 for k in is_keys}, 'MR': {
            'price_p1': DEF_PRICE_P1, 'ad_p1': DEF_AD_P1,
            'price_p2': DEF_PRICE_P2, 'ad_p2': DEF_AD_P2,
            'sales_units_p1': 0, 'sales_units_p2': 0,
            'market_share_p1': 0.0, 'market_share_p2': 0.0
        }
    }

# ---------- 6) Session ----------
st.set_page_config(layout="wide")
if 'game_season' not in st.session_state: st.session_state.game_season = 1
if 'teams' not in st.session_state: st.session_state.teams = {k: init_team_state(k) for k in TEAM_LIST}
if 'role' not in st.session_state: st.session_state.role = None          # 'teacher' or 'student'
if 'team_key' not in st.session_state: st.session_state.team_key = None  # for student
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# ---------- 7) 登入 ----------
def login_view():
    st.title("Nova Manufacturing Sim — 登入")
    role = st.radio("選擇身分", ["老師", "學生"], horizontal=True)
    if role == "老師":
        pw = st.text_input("老師密碼", type="password")
        if st.button("登入（老師端）"):
            if pw == PASSWORDS.get("admin"):
                st.session_state.role = 'teacher'; st.session_state.logged_in = True
                st.success("老師登入成功")
                st.experimental_rerun()
            else:
                st.error("老師密碼錯誤")
    else:
        team = st.selectbox("選擇組別", TEAM_LIST)
        pw = st.text_input("學生密碼（老師提供）", type="password")
        if st.button("登入（學生端）"):
            if pw == PASSWORDS.get(team):
                st.session_state.role = 'student'
                st.session_state.team_key = team
                st.session_state.logged_in = True
                st.success(f"{team} 登入成功")
                st.experimental_rerun()
            else:
                st.error("學生密碼錯誤，請向老師確認")

# ---------- 8) 學生端 ----------
def student_view():
    team_key = st.session_state.team_key
    t = st.session_state.teams.get(team_key, init_team_state(team_key))
    season = st.session_state.game_season
    brief = SEASON_BRIEFS.get(season, {"task":"請依市況自行擬定策略。", "risk":"價格/產能/現金的取捨。"})
    st.title(f"🎓 學生端 — {team_key}（第 {season} 季）")
    with st.expander("📌 本季任務與風險（務必閱讀）", expanded=True):
        st.markdown(f"**任務：** {brief['task']}")
        st.markdown(f"**風險：** {brief['risk']}")

    with st.form(f"decision_form_{team_key}", clear_on_submit=False):
        st.subheader("📝 本季決策")
        c1,c2 = st.columns(2)
        with c1:
            price_p1 = st.number_input("P1 價格", min_value=1, value=int(t['MR'].get('price_p1', DEF_PRICE_P1)))
            ad_p1    = st.number_input("P1 廣告", min_value=0, step=10_000, value=int(t['MR'].get('ad_p1', DEF_AD_P1)))
            prod_p1  = st.number_input("P1 生產量", min_value=0, value=0)
            buy_r1   = st.number_input("購買 R1 原料(單位)", min_value=0, value=0)
        with c2:
            price_p2 = st.number_input("P2 價格", min_value=1, value=int(t['MR'].get('price_p2', DEF_PRICE_P2)))
            ad_p2    = st.number_input("P2 廣告", min_value=0, step=10_000, value=int(t['MR'].get('ad_p2', DEF_AD_P2)))
            prod_p2  = st.number_input("P2 生產量", min_value=0, value=0)
            buy_r2   = st.number_input("購買 R2 原料(單位)", min_value=0, value=0)

        c3,c4 = st.columns(2)
        with c3:
            build_factory = st.number_input("新建工廠(座)", min_value=0, value=0)
            add_lines_p1  = st.number_input("新增 P1 產線(條)", min_value=0, value=0)
        with c4:
            add_lines_p2  = st.number_input("新增 P2 產線(條)", min_value=0, value=0)
            loan  = st.number_input("舉借銀行貸款", min_value=0, step=100_000, value=0)
            repay = st.number_input("償還銀行貸款", min_value=0, step=100_000, value=0)

        submitted = st.form_submit_button("✅ 提交本季決策")
        if submitted:
            decisions = load_decisions()
            if season not in decisions: decisions[season] = {}
            decisions[season][team_key] = {
                'submitted': True,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'data': {
                    'price_p1': int(price_p1), 'ad_p1': int(ad_p1), 'produce_p1': int(prod_p1), 'buy_r1': int(buy_r1),
                    'price_p2': int(price_p2), 'ad_p2': int(ad_p2), 'produce_p2': int(prod_p2), 'buy_r2': int(buy_r2),
                    'build_factory': int(build_factory), 'add_lines_p1': int(add_lines_p1), 'add_lines_p2': int(add_lines_p2),
                    'loan': int(loan), 'repay': int(repay),
                }
            }
            save_decisions(decisions)
            st.success("已提交！老師端會即時看到你的組別已完成。")

    with st.expander("📊 目前資源（僅供參考）"):
        bs = t.get('BS', {})
        st.write(pd.DataFrame([{
            "現金": bs.get('cash',0), "貸款": bs.get('bank_loan',0),
            "工廠": t.get('factories',0), "P1 線": t.get('lines_p1',0), "P2 線": t.get('lines_p2',0),
            "R1 庫存": t.get('inventory_R1_units',0), "R2 庫存": t.get('inventory_R2_units',0),
            "P1 庫存": t.get('inventory_P1_units',0), "P2 庫存": t.get('inventory_P2_units',0),
        }]))

# ---------- 9) 老師端（需密碼登入） ----------
def teacher_view():
    season = st.session_state.game_season
    st.title(f"👨‍🏫 老師端（第 {season} 季）")
    # 提交狀態面板
    st.subheader("📮 提交狀態（即時）")
    decisions = load_decisions()
    season_dec = decisions.get(season, {})
    rows = []
    for team in TEAM_LIST:
        info = season_dec.get(team, {})
        rows.append({
            "組別": team,
            "是否提交": "✅" if info.get('submitted') else "—",
            "提交時間": info.get('timestamp', ""),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    # 檢視某組提交內容
    who = st.selectbox("檢視哪一組的決策內容", TEAM_LIST)
    info = season_dec.get(who)
    if info and info.get('submitted'):
        st.write(pd.DataFrame([info['data']]))
    else:
        st.info("尚未提交。")

    st.divider()
    st.subheader("🚀 進行結算（可先讓部分組提交，沒交者用 0/預設）")
    if st.button("結算本季，進入下一季"):
        # 簡化結算：只示範「提交即入帳，未提交視為 0」
        for team in TEAM_LIST:
            t = st.session_state.teams[team]
            d = (decisions.get(season, {}).get(team, {}) or {}).get('data', {})
            # —— 以下為極簡財務影響（保守）：只處理貸款/廣告/原料/產能 CAPEX ——
            bs = t['BS']
            # capex
            capex = d.get('build_factory',0)*GLOBAL_PARAMS['factory_cost'] + \
                    d.get('add_lines_p1',0)*GLOBAL_PARAMS['line_p1_cost'] + \
                    d.get('add_lines_p2',0)*GLOBAL_PARAMS['line_p2_cost']
            t['factories'] += d.get('build_factory',0)
            t['lines_p1'] += d.get('add_lines_p1',0)
            t['lines_p2'] += d.get('add_lines_p2',0)
            bs['fixed_assets_value'] = force_numeric(bs.get('fixed_assets_value',0)) + capex
            bs['cash'] = force_numeric(bs.get('cash',0)) - capex
            # 原料
            cost_r1 = d.get('buy_r1',0)*GLOBAL_PARAMS['raw_material_cost_R1']
            cost_r2 = d.get('buy_r2',0)*GLOBAL_PARAMS['raw_material_cost_R2']
            bs['cash'] -= (cost_r1 + cost_r2)
            t['inventory_R1_units'] += d.get('buy_r1',0)
            t['inventory_R2_units'] += d.get('buy_r2',0)
            # 廣告
            ad = d.get('ad_p1',0) + d.get('ad_p2',0)
            bs['cash'] -= ad
            # 貸款
            loan = d.get('loan',0); repay = d.get('repay',0)
            bs['bank_loan'] = force_numeric(bs.get('bank_loan',0)) + loan - repay
            bs['cash'] += loan - repay
            # 單純平衡
            t['BS'] = balance_bs(bs)

        st.session_state.game_season += 1
        st.success(f"第 {season} 季結算完成，已進入第 {st.session_state.game_season} 季。")
        st.stop()

# ---------- 10) 入口 ----------
def header_bar():
    left, mid, right = st.columns([1,2,1])
    with left:
        st.caption(f"學期進度：第 {st.session_state.game_season} 季")
    with right:
        if st.button("登出"):
            for k in ['role','team_key','logged_in']:
                st.session_state[k] = None if k!='logged_in' else False
            st.experimental_rerun()

if not st.session_state.logged_in:
    login_view()
else:
    header_bar()
    if st.session_state.role == 'student':
        student_view()
    elif st.session_state.role == 'teacher':
        teacher_view()
    else:
        st.error("未知身分，請重新登入。")
