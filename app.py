# -*- coding: utf-8 -*-
# Nova Manufacturing Sim - V5.0 Classroom Stable (no placeholders)
# 功能：
# - 學生用「下拉選組別 + 輸入該組密碼」登入；老師用老師密碼登入
# - 學生端固定顯示每季「任務與風險」
# - 學生提交決策後，老師端即時看到誰交了、內容與時間
# - 老師可按「結算」：做簡化財務更新（CAPEX/原料/廣告/貸款），進入下一季
# - 使用 st.rerun（含舊版相容墊片）；決策以 pickle 檔案保存（decisions_state.pkl）

import streamlit as st
import pandas as pd
import pickle, os, numbers
from datetime import datetime

# ---------- Streamlit rerun 兼容墊片 ----------
if not hasattr(st, "rerun"):
    def _compat_rerun():
        st.experimental_rerun()
    st.rerun = _compat_rerun

# ---------- 常數與設定 ----------
DECISIONS_FILE = "decisions_state.pkl"
TEAM_LIST = [f"第 {i} 組" for i in range(1, 11)]

PASSWORDS = {
    "admin": "admin123",  # 老師密碼
    "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660",
    "第 7 組": "ice112", "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526",
}

# 每季任務與風險（可自行擴充）
SEASON_BRIEFS = {
    1: {"task": "建立基本產能與定價策略；評估是否擴充產線。", "risk": "過度擴張導致現金吃緊；定價過低毛利不足。"},
    2: {"task": "補足原料、控制庫存週轉；避免缺料停線。", "risk": "庫存過多佔用現金、過少造成產能閒置。"},
    3: {"task": "導入研發與品牌投入，建立差異化。", "risk": "短期獲利下滑；市場不如預期回收期延長。"},
}

# 遊戲參數（簡化）
GLOBAL_PARAMS = {
    'factory_cost': 5_000_000, 'factory_maintenance': 100_000, 'factory_capacity': 8,
    'line_p1_cost': 1_000_000, 'line_p1_maintenance': 20_000, 'line_p1_capacity': 1_000,
    'line_p2_cost': 1_200_000, 'line_p2_maintenance': 25_000, 'line_p2_capacity': 800,
    'raw_material_cost_R1': 100, 'raw_material_cost_R2': 150,
    'p1_material_needed_R1': 1, 'p2_material_needed_R2': 1,
    'p1_labor_cost': 50, 'p2_labor_cost': 70,
    'bank_loan_interest_rate_per_season': 0.02,
    'emergency_loan_interest_rate': 0.05,
}

# ---------- 小工具 ----------
def force_numeric(v, default=0):
    if isinstance(v, numbers.Number): return v
    if isinstance(v, str):
        try: return float(v.replace(",", ""))
        except Exception: return default
    return default

def balance_bs(bs):
    """把資產與「負債+權益」對齊；所有欄位保證為數字"""
    if not isinstance(bs, dict): bs = {}
    cash   = force_numeric(bs.get('cash', 0))
    inv    = force_numeric(bs.get('inventory_value', 0))
    fixed  = force_numeric(bs.get('fixed_assets_value', 0))
    depr   = force_numeric(bs.get('accumulated_depreciation', 0))
    loan   = force_numeric(bs.get('bank_loan', 0))
    equity = force_numeric(bs.get('shareholder_equity', 0))
    total_assets = cash + inv + fixed - depr
    total_le = loan + equity
    if abs(total_assets - total_le) > 1:
        equity += (total_assets - total_le)
    out = {
        'cash': cash, 'inventory_value': inv, 'fixed_assets_value': fixed, 'accumulated_depreciation': depr,
        'bank_loan': loan, 'shareholder_equity': equity,
        'total_assets': total_assets, 'total_liabilities_and_equity': loan + equity
    }
    return out

def save_decisions(d: dict):
    try:
        with open(DECISIONS_FILE, "wb") as f:
            pickle.dump(d, f)
    except Exception as e:
        st.error(f"儲存決策檔失敗：{e}")

def load_decisions() -> dict:
    if not os.path.exists(DECISIONS_FILE): return {}
    try:
        with open(DECISIONS_FILE, "rb") as f:
            data = pickle.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def clear_decisions():
    if os.path.exists(DECISIONS_FILE):
        try: os.remove(DECISIONS_FILE)
        except: pass

# ---------- 狀態初始化 ----------
st.set_page_config(layout="wide")

if "game_season" not in st.session_state: st.session_state.game_season = 1
if "logged_in"  not in st.session_state: st.session_state.logged_in = False
if "role"       not in st.session_state: st.session_state.role = None          # "teacher" / "student"
if "team_key"   not in st.session_state: st.session_state.team_key = None
if "teams"      not in st.session_state: st.session_state.teams = {}

def init_team_if_needed(team_key: str):
    if team_key in st.session_state.teams: return
    fixed_assets = GLOBAL_PARAMS['factory_cost'] + GLOBAL_PARAMS['line_p1_cost'] + GLOBAL_PARAMS['line_p2_cost']
    bs = balance_bs({
        'cash': 10_000_000,
        'inventory_value': 0,
        'fixed_assets_value': fixed_assets,
        'accumulated_depreciation': 0,
        'bank_loan': 0,
        'shareholder_equity': 10_000_000 + fixed_assets,
    })
    st.session_state.teams[team_key] = {
        'team_name': team_key,
        'factories': 1, 'lines_p1': 1, 'lines_p2': 1,
        'inventory_R1_units': 2000, 'inventory_R2_units': 2000,
        'inventory_P1_units': 500, 'inventory_P2_units': 500,
        'BS': bs,  # 這版只做簡化的財報
    }

# ---------- 登入 ----------
def login_view():
    st.title("🏭 Nova Manufacturing Sim — 登入")
    role = st.radio("選擇身分", ["學生", "老師"], horizontal=True)

    if role == "老師":
        pw = st.text_input("老師密碼", type="password")
        if st.button("登入（老師端）"):
            if pw == PASSWORDS.get("admin"):
                st.session_state.logged_in = True
                st.session_state.role = "teacher"
                st.success("老師登入成功")
                st.rerun()
            else:
                st.error("老師密碼錯誤")

    else:  # 學生
        team = st.selectbox("選擇你的組別", TEAM_LIST, index=0)
        pw = st.text_input("該組密碼（老師提供）", type="password")
        if st.button("登入（學生端）"):
            if pw == PASSWORDS.get(team):
                st.session_state.logged_in = True
                st.session_state.role = "student"
                st.session_state.team_key = team
                init_team_if_needed(team)
                st.success(f"{team} 登入成功")
                st.rerun()
            else:
                st.error("密碼錯誤，請向老師確認。")

# ---------- 學生端 ----------
def student_view(team_key: str):
    init_team_if_needed(team_key)
    t = st.session_state.teams[team_key]
    season = st.session_state.game_season

    st.header(f"🎓 學生端 — {t.get('team_name', team_key)}（第 {season} 季）")

    # 任務與風險
    brief = SEASON_BRIEFS.get(season, {"task": "請依市況自行擬定策略。", "risk": "價格/產能/現金的取捨。"})
    with st.expander("📌 本季任務與風險（務必閱讀）", expanded=True):
        st.markdown(f"**任務：** {brief['task']}")
        st.markdown(f"**風險：** {brief['risk']}")

    # 已提交提示
    all_dec = load_decisions()
    season_dec = all_dec.get(season, {})
    info = season_dec.get(team_key)
    if info and info.get("submitted"):
        st.success(f"您已提交第 {season} 季決策（{info.get('timestamp','')}），請等待老師結算。")
        with st.expander("查看已提交內容"):
            st.write(info.get("data", {}))

    # 決策表單
    with st.form(f"decision_form_{team_key}", clear_on_submit=False):
        st.subheader("📝 本季決策")
        c1, c2 = st.columns(2)
        with c1:
            price = st.number_input("產品價格", min_value=100, max_value=1000, value=300, step=10)
            ad    = st.number_input("廣告費用", min_value=0, max_value=2_000_000, value=50_000, step=10_000)
            buy_r1 = st.number_input("購買 R1 原料（單位）", min_value=0, max_value=500_000, value=0, step=100)
            build_factory = st.number_input("新建工廠（座）", min_value=0, max_value=5, value=0)
        with c2:
            produce = st.number_input("本季生產量（單位）", min_value=0, max_value=500_000, value=0, step=100)
            buy_r2 = st.number_input("購買 R2 原料（單位）", min_value=0, max_value=500_000, value=0, step=100)
            add_l1 = st.number_input("新增 P1 產線（條）", min_value=0, max_value=20, value=0)
            add_l2 = st.number_input("新增 P2 產線（條）", min_value=0, max_value=20, value=0)
        c3, c4 = st.columns(2)
        with c3:
            loan  = st.number_input("舉借銀行貸款", min_value=0, max_value=100_000_000, value=0, step=100_000)
        with c4:
            repay = st.number_input("償還銀行貸款", min_value=0, max_value=100_000_000, value=0, step=100_000)

        submitted = st.form_submit_button("✅ 提交")
        if submitted:
            all_dec = load_decisions()
            if season not in all_dec: all_dec[season] = {}
            all_dec[season][team_key] = {
                "submitted": True,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "price": int(price), "ad": int(ad),
                    "produce": int(produce),
                    "buy_r1": int(buy_r1), "buy_r2": int(buy_r2),
                    "build_factory": int(build_factory),
                    "add_l1": int(add_l1), "add_l2": int(add_l2),
                    "loan": int(loan), "repay": int(repay),
                }
            }
            save_decisions(all_dec)
            st.success("已提交！老師端會即時看到你的組別已完成。")
            st.rerun()

    # 簡易資源表
    with st.expander("📊 目前資源（僅供參考）"):
        bs = t.get('BS', {})
        st.write(pd.DataFrame([{
            "現金": bs.get('cash', 0), "貸款": bs.get('bank_loan', 0),
            "工廠": t.get('factories', 0), "P1 線": t.get('lines_p1', 0), "P2 線": t.get('lines_p2', 0),
            "R1 庫存": t.get('inventory_R1_units', 0), "R2 庫存": t.get('inventory_R2_units', 0),
            "P1 庫存": t.get('inventory_P1_units', 0), "P2 庫存": t.get('inventory_P2_units', 0),
        }]))

# ---------- 老師端 ----------
def teacher_view():
    season = st.session_state.game_season
    st.header(f"👨‍🏫 老師端（第 {season} 季）")

    all_dec = load_decisions()
    season_dec = all_dec.get(season, {})

    # 提交狀態一覽
    st.subheader("📮 提交狀態")
    rows = []
    for t in TEAM_LIST:
        info = season_dec.get(t)
        rows.append({
            "組別": t,
            "是否提交": "✅" if (isinstance(info, dict) and info.get("submitted")) else "—",
            "提交時間": (info or {}).get("timestamp", "")
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    who = st.selectbox("查看某一組的決策內容", TEAM_LIST)
    info = season_dec.get(who)
    if info and info.get("submitted"):
        st.write(info.get("data", {}))
    else:
        st.info("尚未提交。")

    st.divider()
    if st.button("📈 結算本季 → 進入下一季"):
        # 簡化結算：把學生提交的花費/貸款寫入各組 BS，未提交者以 0 處理
        for team in TEAM_LIST:
            init_team_if_needed(team)
            t = st.session_state.teams[team]
            bs = t.get('BS', {})
            data = (season_dec.get(team) or {}).get("data", {})  # 沒交則空

            # CAPEX
            capex = data.get("build_factory", 0) * GLOBAL_PARAMS['factory_cost'] + \
                    data.get("add_l1", 0) * GLOBAL_PARAMS['line_p1_cost'] + \
                    data.get("add_l2", 0) * GLOBAL_PARAMS['line_p2_cost']
            t['factories'] += data.get("build_factory", 0)
            t['lines_p1']  += data.get("add_l1", 0)
            t['lines_p2']  += data.get("add_l2", 0)
            bs['fixed_assets_value'] = force_numeric(bs.get('fixed_assets_value', 0)) + capex
            bs['cash'] = force_numeric(bs.get('cash', 0)) - capex

            # 原料
            cost_r1 = data.get("buy_r1", 0) * GLOBAL_PARAMS['raw_material_cost_R1']
            cost_r2 = data.get("buy_r2", 0) * GLOBAL_PARAMS['raw_material_cost_R2']
            t['inventory_R1_units'] += data.get("buy_r1", 0)
            t['inventory_R2_units'] += data.get("buy_r2", 0)
            bs['cash'] -= (cost_r1 + cost_r2)

            # 廣告
            bs['cash'] -= data.get("ad", 0)

            # 貸款
            loan  = data.get("loan", 0)
            repay = data.get("repay", 0)
            bs['bank_loan'] = force_numeric(bs.get('bank_loan', 0)) + loan - repay
            bs['cash'] += loan - repay

            # 利息（簡化：按期末餘額計）
            interest = force_numeric(bs.get('bank_loan', 0)) * GLOBAL_PARAMS['bank_loan_interest_rate_per_season']
            bs['cash'] -= interest

            # 緊急貸款：現金為負時自動借款補到 0 並收罰息
            if bs.get('cash', 0) < 0:
                need = -bs['cash']
                penalty = need * GLOBAL_PARAMS['emergency_loan_interest_rate']
                bs['cash'] = 0
                bs['bank_loan'] += need
                bs['cash'] -= penalty

            t['BS'] = balance_bs(bs)

        # 進入下一季並清除該季提交檔
        clear_decisions()
        st.session_state.game_season += 1
        st.success(f"第 {season} 季結算完成，已進入第 {st.session_state.game_season} 季。")
        st.rerun()

# ---------- 頂部工具列 ----------
def header_bar():
    left, right = st.columns([3, 1])
    with left:
        who = st.session_state.team_key if st.session_state.role == "student" else "老師"
        st.caption(f"登入身分：{who}｜目前季別：第 {st.session_state.game_season} 季")
    with right:
        if st.button("登出"):
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.team_key = None
            st.success("已登出")
            st.rerun()

# ---------- 入口 ----------
def main():
    if not st.session_state.logged_in:
        login_view()
    else:
        header_bar()
        if st.session_state.role == "teacher":
            teacher_view()
        elif st.session_state.role == "student":
            student_view(st.session_state.team_key)
        else:
            st.error("未知身分，請重新登入。")
            st.session_state.logged_in = False
            st.rerun()

if __name__ == "__main__":
    main()
