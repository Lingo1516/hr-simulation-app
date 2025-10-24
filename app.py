# -*- coding: utf-8 -*-
# Nova Manufacturing Sim - V7.0 EMBA+ (Competition, RD Levels, Depreciation, Events, Exports)
# Author: ChatGPT (2025-10)
# 特色：
# - 雙客群需求模型（價格敏感/高端）＋多隊競爭分配市占
# - RD 等級制，提升需求與/或降低加工成本
# - 固定資產帳：建置、折舊（直線法）、出售（殘值）、維護費
# - 通路折扣/回扣、退貨率；供應商延遲與成本差異
# - 隨機事件（黑天鵝）＋保險（降低損害）
# - 現金流量表（CFO/CFI/CFF 簡化）＋ KPI 儀表板
# - 老師端：公告欄、鎖定/截止提交、查看密碼；一鍵結算；Excel 與 HTML 報告匯出
# - 決策持久化：decisions_state.pkl；老師設定持久化：teacher_state.pkl

import os, pickle, numbers, random, json
from datetime import datetime
import pandas as pd
import streamlit as st

# ---------- Streamlit rerun 兼容墊片 ----------
if not hasattr(st, "rerun"):
    def _compat_rerun():
        st.experimental_rerun()
    st.rerun = _compat_rerun

# ---------- 持久化檔案 ----------
DECISIONS_FILE = "decisions_state.pkl"
TEACHER_FILE = "teacher_state.pkl"

# ---------- 基本設定 ----------
TEAM_LIST = [f"第 {i} 組" for i in range(1, 11)]
PASSWORDS = {
    "admin": "admin123",  # 老師密碼
    "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660",
    "第 7 組": "ice112", "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526",
}

# 固資與成本參數
PARAM = {
    "factory_cost": 5_000_000,  "factory_lines_cap": 8, "factory_maint": 100_000, "factory_life_seasons": 40, # 10年*4季
    "line_p1_cost": 1_000_000,  "line_p1_cap": 1_000,  "line_p1_maint": 20_000,  "line_p1_life": 20,
    "line_p2_cost": 1_200_000,  "line_p2_cap": 800,    "line_p2_maint": 25_000,  "line_p2_life": 20,
    "rm_cost_r1": 100, "rm_cost_r2": 150,
    "labor_p1": 50, "labor_p2": 70,
    "holding_rate": 0.02,
    "lost_sales_penalty": 20,
    "overtime_multiplier": 1.4,
    "bank_rate": 0.02, "emg_rate": 0.05,
    "salvage_rate": 0.6,  # 出售殘值%
}

# RD 等級（效果與成本回饋）
RD = {
    "max_level": 5,
    # lvl → (需求乘數增益, 勞務成本降低%)
    1: (1.00, 0.00),
    2: (1.03, 0.02),
    3: (1.07, 0.04),
    4: (1.12, 0.06),
    5: (1.18, 0.08),
}

# 市場情境（含雙客群）
SCENARIOS = {
    1: {
        "title": "開局市場（穩定）",
        # 敏感客 / 高端客 base 需求
        "demand_base": {"p1": {"sens": 18_000, "prem": 12_000}, "p2": {"sens": 8_000, "prem": 16_000}},
        "price_ref": {"p1": 300, "p2": 450},
        "elasticity": {   # 價格彈性（敏感 > 高端）
            "p1": {"sens": -1.3, "prem": -0.7},
            "p2": {"sens": -0.9, "prem": -1.2},
        },
        "ad_power": 0.35,  # 廣告遞減指數
        "channel": {"online": 1.0, "retail": 0.92},  # 通路效率
        "supplier": {
            "A": {"delay": 0.12, "cost_adj": -0.04},
            "B": {"delay": 0.04, "cost_adj":  0.00},
            "C": {"delay": 0.00, "cost_adj":  0.05},
        },
        "returns_rate": 0.03,     # 退貨率
        "rebate_rate": 0.02,      # 回扣（淨額下修）
        "event_probs": {"supply_shock": 0.10, "demand_drop": 0.08, "quality_recall": 0.03},
    },
    2: {
        "title": "供應趨緊（原料上漲）",
        "demand_base": {"p1": {"sens": 16_000, "prem": 12_000}, "p2": {"sens": 7_000, "prem": 15_000}},
        "price_ref": {"p1": 320, "p2": 470},
        "elasticity": {
            "p1": {"sens": -1.4, "prem": -0.8},
            "p2": {"sens": -1.0, "prem": -1.25},
        },
        "ad_power": 0.32,
        "channel": {"online": 1.0, "retail": 0.90},
        "supplier": {
            "A": {"delay": 0.18, "cost_adj": -0.02},
            "B": {"delay": 0.06, "cost_adj":  0.00},
            "C": {"delay": 0.00, "cost_adj":  0.07},
        },
        "returns_rate": 0.035,
        "rebate_rate": 0.02,
        "event_probs": {"supply_shock": 0.16, "demand_drop": 0.10, "quality_recall": 0.04},
    },
    3: {
        "title": "需求分化（高端偏好）",
        "demand_base": {"p1": {"sens": 14_000, "prem": 12_000}, "p2": {"sens": 6_000, "prem": 19_000}},
        "price_ref": {"p1": 330, "p2": 490},
        "elasticity": {
            "p1": {"sens": -1.1, "prem": -0.6},
            "p2": {"sens": -0.9, "prem": -1.35},
        },
        "ad_power": 0.30,
        "channel": {"online": 0.98, "retail": 1.02},
        "supplier": {
            "A": {"delay": 0.15, "cost_adj": -0.03},
            "B": {"delay": 0.04, "cost_adj":  0.00},
            "C": {"delay": 0.00, "cost_adj":  0.06},
        },
        "returns_rate": 0.028,
        "rebate_rate": 0.015,
        "event_probs": {"supply_shock": 0.09, "demand_drop": 0.07, "quality_recall": 0.05},
    },
}

# ---------- 工具 ----------
def fnum(x, default=0.0):
    if isinstance(x, numbers.Number): return float(x)
    if isinstance(x, str):
        try: return float(x.replace(",", ""))
        except Exception: return float(default)
    return float(default)

def load_pickle(path, default):
    if not os.path.exists(path): return default
    try:
        with open(path, "rb") as f: return pickle.load(f)
    except Exception: return default

def save_pickle(path, data):
    with open(path, "wb") as f: pickle.dump(data, f)

def load_decisions() -> dict:
    return load_pickle(DECISIONS_FILE, {})

def save_decisions(d: dict):
    save_pickle(DECISIONS_FILE, d)

def clear_decisions():
    if os.path.exists(DECISIONS_FILE):
        try: os.remove(DECISIONS_FILE)
        except Exception: pass

def load_teacher_state() -> dict:
    # {'locks': {season: True/False}, 'announcement': '...', 'seed': 42}
    data = load_pickle(TEACHER_FILE, {})
    data.setdefault('locks', {})
    data.setdefault('announcement', "")
    data.setdefault('seed', 42)
    return data

def save_teacher_state(d: dict):
    save_pickle(TEACHER_FILE, d)

def balance_bs(bs):
    cash = fnum(bs.get("cash", 0)); inv = fnum(bs.get("inventory_value", 0))
    fa = fnum(bs.get("fixed_assets_value", 0)); dep = fnum(bs.get("accumulated_depreciation", 0))
    loan = fnum(bs.get("bank_loan", 0)); eq = fnum(bs.get("shareholder_equity", 0))
    ta = cash + inv + fa - dep; tle = loan + eq
    if abs(ta - tle) > 1: eq += (ta - tle)
    bs.update({
        "cash": cash, "inventory_value": inv, "fixed_assets_value": fa, "accumulated_depreciation": dep,
        "bank_loan": loan, "shareholder_equity": eq,
        "total_assets": ta, "total_liabilities_and_equity": loan + eq
    }); return bs

def init_team_if_needed(team):
    if "teams" not in st.session_state: st.session_state.teams = {}
    if team in st.session_state.teams: return
    fixed_assets = PARAM["factory_cost"] + PARAM["line_p1_cost"] + PARAM["line_p2_cost"]
    bs = balance_bs({
        "cash": 10_000_000, "inventory_value": 0, "fixed_assets_value": fixed_assets,
        "accumulated_depreciation": 0, "bank_loan": 0, "shareholder_equity": 10_000_000 + fixed_assets
    })
    st.session_state.teams[team] = {
        "team_name": team,
        "factories": 1, "lines_p1": 1, "lines_p2": 1,
        "inv_r1": 2_000, "inv_r2": 2_000,
        "inv_p1": 500, "inv_p2": 500,
        "rd_level_p1": 1, "rd_level_p2": 1,
        "BS": bs,
        # 現金流紀錄（最近一季）
        "CASHFLOW": {"CFO": 0.0, "CFI": 0.0, "CFF": 0.0}
    }

# ---------- UI 初始化 ----------
st.set_page_config(layout="wide")
if "game_season" not in st.session_state: st.session_state.game_season = 1
if "logged_in"  not in st.session_state: st.session_state.logged_in = False
if "role"       not in st.session_state: st.session_state.role = None
if "team_key"   not in st.session_state: st.session_state.team_key = None
if "teams"      not in st.session_state: st.session_state.teams = {}

# ---------- 登入/登出 ----------
def login_view():
    st.title("🏭 Nova Manufacturing Sim — 登入")
    role = st.radio("選擇身分", ["學生", "老師"], horizontal=True)
    if role == "老師":
        pw = st.text_input("老師密碼", type="password")
        if st.button("登入（老師端）"):
            if pw == PASSWORDS.get("admin"):
                st.session_state.logged_in = True
                st.session_state.role = "teacher"
                st.success("老師登入成功"); st.rerun()
            else:
                st.error("老師密碼錯誤")
    else:
        team = st.selectbox("選擇你的組別", TEAM_LIST, index=0)
        pw = st.text_input("該組密碼（老師提供）", type="password")
        if st.button("登入（學生端）"):
            if pw == PASSWORDS.get(team):
                st.session_state.logged_in = True
                st.session_state.role = "student"
                st.session_state.team_key = team
                init_team_if_needed(team)
                st.success(f"{team} 登入成功"); st.rerun()
            else:
                st.error("密碼錯誤，請向老師確認。")

def header_bar():
    left, right = st.columns([3,1])
    with left:
        who = st.session_state.team_key if st.session_state.role == "student" else "老師"
        st.caption(f"登入：{who}｜季別：第 {st.session_state.game_season} 季")
    with right:
        if st.button("登出"):
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.team_key = None
            st.success("已登出"); st.rerun()

# ---------- 需求與競爭分配 ----------
def attractiveness(score_inputs, scn, product, segment):
    # score_inputs: dict(price, ad, quality_multi, channel_multi, rd_level, discount_net)
    ref = scn["price_ref"][product]
    p = fnum(score_inputs["price"])
    ad = max(0.0, fnum(score_inputs["ad"]))
    ad_score = (ad / 100_000.0) ** scn["ad_power"] if ad > 0 else 0.0
    q_mult = score_inputs["quality_multi"]
    ch_mult = score_inputs["channel_multi"]
    # 價格調折扣後的有效價
    eff_price = max(1.0, p * (1.0 - fnum(score_inputs.get("discount_net", 0.0))))
    price_ratio = eff_price / ref
    elast = scn["elasticity"][product][segment]
    # 綜合吸引力（越大越好）
    return (1.0 + ad_score) * q_mult * ch_mult / (price_ratio ** abs(elast))

def split_market_across_teams(teams_payload, scn, product):
    """teams_payload: {team_key: {'sens':score,'prem':score,'cap':可售量}} → 回傳銷量分配"""
    result = {k: 0.0 for k in teams_payload.keys()}
    for seg in ["sens", "prem"]:
        demand = scn["demand_base"][product][seg]
        total_score = sum(tp[seg] for tp in teams_payload.values())
        if total_score <= 0:
            # 沒有吸引力 → 全部無法轉換
            continue
        # 先按比例分配，再受「可售量(cap)」限制
        tentative = {k: demand * (tp[seg] / total_score) for k, tp in teams_payload.items()}
        # 容量/庫存限制
        for k, qty in tentative.items():
            cap = teams_payload[k]["cap"]
            alloc = min(qty, cap - result[k])
            result[k] += max(0.0, alloc)
        # 若有剩餘需求，按尚有cap的隊伍再分（簡化：一次補）
        leftover = demand - sum(result.values())
        if leftover > 1e-6:
            cap_left = {k: teams_payload[k]["cap"] - result[k] for k in result}
            cap_sum = sum(max(0.0, v) for v in cap_left.values())
            if cap_sum > 0:
                for k in result:
                    add = leftover * max(0.0, cap_left[k]) / cap_sum
                    result[k] += add
    return result

# ---------- 單隊結算（回傳 KPI 與三大現金流） ----------
def settle_one_team(season, team_key, decision, scn, teacher_state):
    init_team_if_needed(team_key)
    t = st.session_state.teams[team_key]
    bs = t["BS"]

    CFO = 0.0; CFI = 0.0; CFF = 0.0  # 現金流三表

    # --- 老師公告只是顯示，不影響結算 ---

    # --- 固資：建置與出售 ---
    build_factory = int(fnum(decision.get("build_factory", 0)))
    add_l1 = int(fnum(decision.get("add_l1", 0)))
    add_l2 = int(fnum(decision.get("add_l2", 0)))
    sell_factory = int(fnum(decision.get("sell_factory", 0)))
    sell_l1 = int(fnum(decision.get("sell_l1", 0)))
    sell_l2 = int(fnum(decision.get("sell_l2", 0)))

    # 容量上限檢查
    if t["lines_p1"] + t["lines_p2"] + add_l1 + add_l2 > (t["factories"] + build_factory) * PARAM["factory_lines_cap"]:
        add_l1 = add_l2 = 0  # 超上限則不新增

    # 建置支出
    capex = (build_factory*PARAM["factory_cost"] +
             add_l1*PARAM["line_p1_cost"] + add_l2*PARAM["line_p2_cost"])
    t["factories"] += build_factory; t["lines_p1"] += add_l1; t["lines_p2"] += add_l2
    bs["fixed_assets_value"] = fnum(bs["fixed_assets_value"]) + capex
    bs["cash"] = fnum(bs["cash"]) - capex
    CFI -= capex

    # 出售（按殘值）
    def sell_assets(qty, unit_cost):
        nonlocal bs, t, CFI
        qty = max(0, qty)
        proceeds = qty * unit_cost * PARAM["salvage_rate"]
        bs["cash"] += proceeds; CFI += proceeds
        bs["fixed_assets_value"] -= qty * unit_cost
        return qty
    sell_factory = min(sell_factory, t["factories"])
    t["factories"] -= sell_assets(sell_factory, PARAM["factory_cost"])
    sell_l1 = min(sell_l1, t["lines_p1"])
    t["lines_p1"] -= sell_assets(sell_l1, PARAM["line_p1_cost"])
    sell_l2 = min(sell_l2, t["lines_p2"])
    t["lines_p2"] -= sell_assets(sell_l2, PARAM["line_p2_cost"])

    # --- 採購（供應商） ---
    supplier = decision.get("supplier", "B")
    sup_cfg = scn["supplier"].get(supplier, scn["supplier"]["B"])
    buy_r1 = int(fnum(decision.get("buy_r1", 0)))
    buy_r2 = int(fnum(decision.get("buy_r2", 0)))
    price_r1 = PARAM["rm_cost_r1"] * (1 + sup_cfg["cost_adj"])
    price_r2 = PARAM["rm_cost_r2"] * (1 + sup_cfg["cost_adj"])
    arrive_r1 = int(buy_r1 * (1 - sup_cfg["delay"]))
    arrive_r2 = int(buy_r2 * (1 - sup_cfg["delay"]))
    t["inv_r1"] += arrive_r1; t["inv_r2"] += arrive_r2
    cash_out_rm = buy_r1*price_r1 + buy_r2*price_r2
    bs["cash"] -= cash_out_rm; CFO -= cash_out_rm

    # --- 研發等級化 ---
    rd_spend_p1 = fnum(decision.get("rd_spend_p1", 0))
    rd_spend_p2 = fnum(decision.get("rd_spend_p2", 0))
    bs["cash"] -= (rd_spend_p1 + rd_spend_p2); CFO -= (rd_spend_p1 + rd_spend_p2)

    def rd_level_up(current_lvl, spend):
        lvl = int(current_lvl)
        if lvl >= RD["max_level"]: return lvl
        # 每升 1 級需要 ~ 1,000,000（可自行調整）
        gained = int(spend // 1_000_000)
        return min(RD["max_level"], lvl + max(0, gained))
    t["rd_level_p1"] = rd_level_up(t["rd_level_p1"], rd_spend_p1)
    t["rd_level_p2"] = rd_level_up(t["rd_level_p2"], rd_spend_p2)

    rd_mult_p1, cost_cut_p1 = RD[t["rd_level_p1"]]
    rd_mult_p2, cost_cut_p2 = RD[t["rd_level_p2"]]

    # --- 生產（含加班） ---
    allow_ot = bool(decision.get("overtime", False))
    cap_mult = 1.3 if allow_ot else 1.0
    labor_mult = PARAM["overtime_multiplier"] if allow_ot else 1.0
    want_p1 = int(fnum(decision.get("produce_p1", 0)))
    want_p2 = int(fnum(decision.get("produce_p2", 0)))
    cap_p1 = int(t["lines_p1"] * PARAM["line_p1_cap"] * cap_mult)
    cap_p2 = int(t["lines_p2"] * PARAM["line_p2_cap"] * cap_mult)
    max_p1_rm = t["inv_r1"]  # 每單位需 1
    max_p2_rm = t["inv_r2"]
    prod_p1 = min(want_p1, cap_p1, max_p1_rm)
    prod_p2 = min(want_p2, cap_p2, max_p2_rm)
    t["inv_r1"] -= prod_p1; t["inv_r2"] -= prod_p2
    t["inv_p1"] += prod_p1; t["inv_p2"] += prod_p2
    # 加工成本（因 RD 降低）
    proc_cost = prod_p1 * PARAM["labor_p1"] * labor_mult * (1 - cost_cut_p1) + \
                prod_p2 * PARAM["labor_p2"] * labor_mult * (1 - cost_cut_p2)
    bs["cash"] -= proc_cost; CFO -= proc_cost

    # --- 價格/廣告/通路折扣與回扣/退貨 ---
    price_p1 = fnum(decision.get("price_p1", scn["price_ref"]["p1"]))
    price_p2 = fnum(decision.get("price_p2", scn["price_ref"]["p2"]))
    ad_p1 = fnum(decision.get("ad_p1", 0)); ad_p2 = fnum(decision.get("ad_p2", 0))
    ch_online = min(1.0, max(0.0, fnum(decision.get("channel_online", 0.5))))
    discount_retail = fnum(decision.get("discount_retail", 0.05)) # 零售折扣
    rebate_rate = scn["rebate_rate"]  # 回扣
    returns_rate = scn["returns_rate"]

    # 通路綜合效率
    ch_mult = ch_online * scn["channel"]["online"] + (1 - ch_online) * scn["channel"]["retail"]
    # 折扣/回扣淨價調整（只對零售比重影響）
    discount_net = (1 - ch_online) * discount_retail + rebate_rate

    # 品質乘數（RD 對需求的增益）
    q_mult_p1 = rd_mult_p1
    q_mult_p2 = rd_mult_p2

    # 可售量（庫存）
    sell_cap_p1 = t["inv_p1"]
    sell_cap_p2 = t["inv_p2"]

    # 吸引力分數（給競爭分配器用）
    payload_p1 = {}
    payload_p2 = {}
    payload_p1[team_key] = {
        "sens": attractiveness({"price": price_p1, "ad": ad_p1, "quality_multi": q_mult_p1,
                                "channel_multi": ch_mult, "discount_net": discount_net}, scn, "p1", "sens"),
        "prem": attractiveness({"price": price_p1, "ad": ad_p1, "quality_multi": q_mult_p1,
                                "channel_multi": ch_mult, "discount_net": discount_net}, scn, "p1", "prem"),
        "cap": sell_cap_p1
    }
    payload_p2[team_key] = {
        "sens": attractiveness({"price": price_p2, "ad": ad_p2, "quality_multi": q_mult_p2,
                                "channel_multi": ch_mult, "discount_net": discount_net}, scn, "p2", "sens"),
        "prem": attractiveness({"price": price_p2, "ad": ad_p2, "quality_multi": q_mult_p2,
                                "channel_multi": ch_mult, "discount_net": discount_net}, scn, "p2", "prem"),
        "cap": sell_cap_p2
    }

    # 其他隊伍也會一起進競爭（在 teacher 結算時填入完整 payload；若單隊模擬，先只算自己）
    # 這個函數這裡先回傳自家 payload，其餘由 teacher_view 結算時合併。

    # 回傳結算所需中間值
    mid = {
        "payload_p1": payload_p1, "payload_p2": payload_p2,
        "price_p1": price_p1, "price_p2": price_p2,
        "ad_p1": ad_p1, "ad_p2": ad_p2,
        "discount_net": discount_net, "returns_rate": returns_rate,
        "ch_online": ch_online, "ch_mult": ch_mult,
        "sell_cap_p1": sell_cap_p1, "sell_cap_p2": sell_cap_p2,
        "CFO": CFO, "CFI": CFI, "CFF": CFF
    }
    # 同時把維護費先算好（CFO）
    maint = (t["factories"] * PARAM["factory_maint"] +
             t["lines_p1"] * PARAM["line_p1_maint"] +
             t["lines_p2"] * PARAM["line_p2_maint"])
    bs["cash"] -= maint; mid["CFO"] -= maint

    # --- 折舊 ---
    dep = (t["factories"] * PARAM["factory_cost"] / PARAM["factory_life_seasons"] +
           t["lines_p1"] * PARAM["line_p1_cost"] / PARAM["line_p1_life"] +
           t["lines_p2"] * PARAM["line_p2_cost"] / PARAM["line_p2_life"])
    bs["accumulated_depreciation"] = fnum(bs.get("accumulated_depreciation", 0)) + dep
    # 折舊是非現金：不動現金，只更新股東權益在 balance 時配平

    # --- 融資 ---
    loan = fnum(decision.get("loan", 0)); repay = fnum(decision.get("repay", 0))
    bs["bank_loan"] = fnum(bs["bank_loan"]) + loan - repay
    bs["cash"] += loan - repay
    mid["CFF"] += loan - repay
    # 利息
    interest = fnum(bs["bank_loan"]) * PARAM["bank_rate"]
    bs["cash"] -= interest; mid["CFO"] -= interest

    # --- 隨機事件與保險 ---
    insure = bool(decision.get("insurance", False))
    premium = 80_000 if insure else 0
    bs["cash"] -= premium; mid["CFO"] -= premium

    # 事件：使用「老師設定 seed + season + team hash」確定性抽樣，避免每次 rerun 不同
    seed_base = int(load_teacher_state().get("seed", 42))
    rnd = random.Random(seed_base + season * 100 + hash(team_key) % 10_000)
    events = []
    probs = scn["event_probs"]
    # 供應中斷：減少可售庫存 10%（保險減至 3%）
    if rnd.random() < probs.get("supply_shock", 0.0):
        cut = 0.10 if not insure else 0.03
        t["inv_p1"] = int(t["inv_p1"] * (1 - cut))
        t["inv_p2"] = int(t["inv_p2"] * (1 - cut))
        events.append(f"供應中斷(-{int(cut*100)}% 可售庫存)")
    # 市場驟降：需求乘數 0.9（保險 0.97）
    demand_mult = 0.90 if rnd.random() < probs.get("demand_drop", 0.0) and not insure else (0.97 if insure else 1.0)
    # 品質瑕疵召回：退貨率加 3%（保險加 1%）
    if rnd.random() < probs.get("quality_recall", 0.0):
        mid["returns_rate"] += 0.03 if not insure else 0.01
        events.append("品質召回（退貨率上升）")

    mid["demand_mult"] = demand_mult
    mid["events"] = events

    # 先回寫 BS（稍後競爭分配完成會再做現金調整）
    t["BS"] = balance_bs(bs)
    return mid

# ---------- 學生端 ----------
def student_view(team_key):
    tstate = load_teacher_state()
    season = st.session_state.game_season
    scn = SCENARIOS.get(season, list(SCENARIOS.values())[-1])
    st.header(f"🎓 學生端 — {team_key}（第 {season} 季）")

    if tstate.get('announcement'):
        st.info(f"📣 老師公告：{tstate['announcement']}")

    # 鎖定檢查
    locked = tstate.get('locks', {}).get(season, False)

    # 已提交狀態
    all_dec = load_decisions(); season_dec = all_dec.get(season, {})
    info = season_dec.get(team_key)

    with st.expander(f"📌 本季情境：{scn['title']}", expanded=True):
        st.markdown("- **雙客群**：價格敏感 vs 高端偏好；不同彈性。")
        st.markdown("- **通路**：線上/零售效率差異；零售有折扣與回扣。")
        st.markdown("- **RD 等級**：提升需求乘數或降低加工成本。")
        st.markdown("- **資本**：工廠/產線可建置或出售；有折舊與維護費。")
        st.markdown("- **事件/保險**：黑天鵝造成供應或需求衝擊；投保可降低損害。")

    if info and info.get("submitted"):
        st.success(f"已提交（{info.get('timestamp','')}），如需修改請聯絡老師解鎖或重開提交。")
        with st.expander("查看已提交內容"):
            st.write(info.get("data", {}))

    # 表單
    with st.form(f"decision_form_{team_key}", clear_on_submit=False):
        st.subheader("📝 本季決策")
        c1, c2 = st.columns(2)
        with c1:
            price_p1 = st.number_input("P1 價格", 100, 1000, int(scn["price_ref"]["p1"]), 10,
                                       help="價格↑ → 單位毛利↑但需求↓；相對參考價的彈性見情境。", disabled=locked)
            ad_p1 = st.number_input("P1 廣告費", 0, 2_000_000, 50_000, 10_000,
                                    help="(費用/10萬)^(指數) 進需求；遞減報酬。", disabled=locked)
            produce_p1 = st.number_input("P1 生產量", 0, 500_000, 0, 100,
                                         help="受 P1 產線與 R1 原料限制；勾選加班可放大 30%。", disabled=locked)
            rd_spend_p1 = st.number_input("P1 研發投入", 0, 5_000_000, 0, 100_000,
                                          help="每投入 ~100萬可望升 1 級（上限 5 級），提升需求/降成本。", disabled=locked)
            buy_r1 = st.number_input("採購 R1（單位）", 0, 500_000, 0, 100,
                                     help="受供應商延遲影響到貨量。", disabled=locked)
            build_factory = st.number_input("新增工廠（座）", 0, 5, 0,
                                            help="每座 8 條線上限；含維護與折舊。", disabled=locked)
            add_l1 = st.number_input("新增 P1 線（條）", 0, 20, 0,
                                     help="建置成本 100 萬；每季維護 2 萬；有折舊。", disabled=locked)
            sell_factory = st.number_input("出售工廠（座）", 0, 5, 0,
                                           help="以殘值 60% 賣出；釋放現金但容量下降。", disabled=locked)
            sell_l1 = st.number_input("出售 P1 線（條）", 0, 20, 0,
                                      help="以殘值 60% 賣出。", disabled=locked)
        with c2:
            price_p2 = st.number_input("P2 價格", 100, 1200, int(scn["price_ref"]["p2"]), 10,
                                       help="高端客對 P2 更敏感於品質/品牌。", disabled=locked)
            ad_p2 = st.number_input("P2 廣告費", 0, 2_000_000, 50_000, 10_000,
                                    help="同上。", disabled=locked)
            produce_p2 = st.number_input("P2 生產量", 0, 500_000, 0, 100,
                                         help="受 P2 產線與 R2 原料限制；可加班。", disabled=locked)
            rd_spend_p2 = st.number_input("P2 研發投入", 0, 5_000_000, 0, 100_000,
                                          help="同上。", disabled=locked)
            buy_r2 = st.number_input("採購 R2（單位）", 0, 500_000, 0, 100,
                                     help="受供應商延遲影響到貨量。", disabled=locked)
            overtime = st.checkbox("允許加班（成本↑）", value=False, disabled=locked)
            channel_online = st.slider("通路：線上占比", 0.0, 1.0, 0.5, 0.05,
                                       help="不同季線上/零售效率不同；零售有折扣/回扣。", disabled=locked)
            discount_retail = st.slider("零售折扣（標價下修）", 0.00, 0.30, 0.05, 0.01,
                                        help="只作用於零售比重；還有回扣 rate 會進一步下修淨價。", disabled=locked)
            loan = st.number_input("舉借銀行貸款", 0, 200_000_000, 0, 100_000,
                                   help="利率 2%/季；可增加現金但增加利息。", disabled=locked)
            repay = st.number_input("償還銀行貸款", 0, 200_000_000, 0, 100_000,
                                    help="降低負債與利息。", disabled=locked)
            safety_stock = st.number_input("安全庫存（成品）", 0, 500_000, 0, 100,
                                           help="高安全庫存降低缺貨但增加持有成本。", disabled=locked)
            supplier = st.selectbox("主要供應商", ["A", "B", "C"],
                                    help="A：便宜/延遲高；B：一般；C：穩定/昂貴。", disabled=locked)
            insurance = st.checkbox("投保黑天鵝保險（保費 80,000）", value=False, disabled=locked)

        submitted = st.form_submit_button("✅ 提交決策", disabled=locked)
        if submitted:
            dec = {
                "price_p1": int(price_p1), "ad_p1": int(ad_p1), "produce_p1": int(produce_p1),
                "price_p2": int(price_p2), "ad_p2": int(ad_p2), "produce_p2": int(produce_p2),
                "rd_spend_p1": int(rd_spend_p1), "rd_spend_p2": int(rd_spend_p2),
                "buy_r1": int(buy_r1), "buy_r2": int(buy_r2),
                "build_factory": int(build_factory), "add_l1": int(add_l1), "add_l2": 0,
                "sell_factory": int(sell_factory), "sell_l1": int(sell_l1), "sell_l2": 0,
                "overtime": bool(overtime), "channel_online": float(channel_online),
                "discount_retail": float(discount_retail), "supplier": supplier,
                "loan": int(loan), "repay": int(repay), "safety_stock": int(safety_stock),
                "insurance": bool(insurance),
            }
            all_dec = load_decisions()
            if season not in all_dec: all_dec[season] = {}
            all_dec[season][team_key] = {"submitted": True, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "data": dec}
            save_decisions(all_dec)
            st.success("已提交！"); st.rerun()

    # 快速資源表
    t = st.session_state.teams[team_key]
    with st.expander("📊 目前資源/等級（參考）"):
        bs = t["BS"]
        st.write(pd.DataFrame([{
            "現金": int(bs["cash"]), "貸款": int(bs["bank_loan"]),
            "工廠": t["factories"], "P1線": t["lines_p1"], "P2線": t["lines_p2"],
            "R1庫存": t["inv_r1"], "R2庫存": t["inv_r2"], "P1庫存": t["inv_p1"], "P2庫存": t["inv_p2"],
            "RD等級_P1": t["rd_level_p1"], "RD等級_P2": t["rd_level_p2"],
        }]))

# ---------- 老師端 ----------
def teacher_view():
    season = st.session_state.game_season
    tstate = load_teacher_state()
    st.header(f"👨‍🏫 老師端（第 {season} 季）")

    # 公告欄 + 鎖定
    with st.expander("📣 公告與提交控制", expanded=True):
        ann = st.text_area("公告內容（學生首頁會顯示）", value=tstate.get('announcement', ""), height=120)
        colA, colB, colC = st.columns(3)
        with colA:
            locked = st.toggle(f"鎖定第 {season} 季提交（鎖定後學生無法提交）", value=tstate.get('locks', {}).get(season, False))
        with colB:
            seed = st.number_input("隨機事件種子（整數）", value=int(tstate.get('seed', 42)), step=1)
        with colC:
            if st.button("保存公告/設定"):
                tstate['announcement'] = ann
                tstate['seed'] = int(seed)
                tstate['locks'][season] = bool(locked)
                save_teacher_state(tstate)
                st.success("已保存")

    # 密碼總覽
    with st.expander("🔑 學生密碼總覽", expanded=False):
        df_pw = pd.DataFrame([{"組別": k, "密碼": v} for k, v in PASSWORDS.items() if k != "admin"])
        st.dataframe(df_pw, use_container_width=True)
        st.download_button("下載密碼 CSV", df_pw.to_csv(index=False), file_name="team_passwords.csv", mime="text/csv")

    # 提交狀態
    st.subheader("📮 提交狀態")
    all_dec = load_decisions(); season_dec = all_dec.get(season, {})
    rows = []
    for t in TEAM_LIST:
        info = season_dec.get(t)
        rows.append({"組別": t, "是否提交": "✅" if info and info.get("submitted") else "—",
                     "提交時間": (info or {}).get("timestamp", "")})
    df_status = pd.DataFrame(rows)
    st.dataframe(df_status, use_container_width=True)

    # 檢視單組決策
    who = st.selectbox("查看某一組決策內容", TEAM_LIST)
    info = season_dec.get(who)
    if info and info.get("submitted"):
        st.write(info["data"])
    else:
        st.info("尚未提交。")

    # 一鍵結算（多隊競爭）
    st.divider()
    if st.button("📈 結算本季 → 進入下一季"):
        scn = SCENARIOS.get(season, list(SCENARIOS.values())[-1])

        # 第一步：先讓每隊做「前置結算」（建置/採購/生產/維護/研發/利息/事件等），並得到吸引力 payload
        mids = {}
        for team in TEAM_LIST:
            init_team_if_needed(team)
            dec = (season_dec.get(team) or {}).get("data", {})
            mids[team] = settle_one_team(season, team, dec, scn, tstate)

        # 第二步：建立全隊 payload 進行競爭分配（p1/p2 分別）
        payload_p1 = {}
        payload_p2 = {}
        for team, mid in mids.items():
            for k, v in mid["payload_p1"].items(): payload_p1[k] = v
            for k, v in mid["payload_p2"].items(): payload_p2[k] = v

        sales_p1 = split_market_across_teams(payload_p1, scn, "p1")
        sales_p2 = split_market_across_teams(payload_p2, scn, "p2")

        # 第三步：計價（折扣/回扣/退貨率/需求乘數）、現金流、KPI
        kpi_rows = []
        for team in TEAM_LIST:
            t = st.session_state.teams[team]; bs = t["BS"]; mid = mids[team]
            # 需求事件乘數
            mult = mid["demand_mult"]
            sp1 = sales_p1.get(team, 0.0) * mult
            sp2 = sales_p2.get(team, 0.0) * mult
            # 退貨
            ret_rate = max(0.0, min(0.3, mid["returns_rate"]))
            ret1 = sp1 * ret_rate; ret2 = sp2 * ret_rate
            net1 = max(0.0, sp1 - ret1); net2 = max(0.0, sp2 - ret2)

            price1 = mid["price_p1"]; price2 = mid["price_p2"]
            disc = mid["discount_net"]
            # 折扣與回扣淨效
            unit1 = price1 * (1 - disc); unit2 = price2 * (1 - disc)

            revenue = net1 * unit1 + net2 * unit2
            # 出貨扣庫存
            t["inv_p1"] = max(0, t["inv_p1"] - int(sp1))
            t["inv_p2"] = max(0, t["inv_p2"] - int(sp2))
            # 收現
            bs["cash"] += revenue; mid["CFO"] += revenue

            # 庫存持有成本與缺貨懲罰
            safety = int(fnum((season_dec.get(team) or {}).get("data", {}).get("safety_stock", 0)))
            holding_units = max(0, t["inv_p1"] + t["inv_p2"] - safety)
            avg_unit_cost = (PARAM["rm_cost_r1"] + PARAM["labor_p1"] + PARAM["rm_cost_r2"] + PARAM["labor_p2"]) / 2.0
            holding_cost = holding_units * avg_unit_cost * PARAM["holding_rate"]
            bs["cash"] -= holding_cost; mid["CFO"] -= holding_cost

            # 缺貨懲罰：需求未滿足的部份（第二輪分配後理論上少）
            # 這裡簡化不再另計

            # 緊急貸款
            if bs["cash"] < 0:
                need = -bs["cash"]; penalty = need * PARAM["emg_rate"]
                bs["cash"] = 0; bs["bank_loan"] += need; bs["cash"] -= penalty; mid["CFF"] += need; mid["CFO"] -= penalty

            # 平衡表
            t["BS"] = balance_bs(bs)
            # 記錄現金流
            t["CASHFLOW"] = {"CFO": round(mid["CFO"], 2), "CFI": round(mid["CFI"], 2), "CFF": round(mid["CFF"], 2)}

            # KPI
            kpi_rows.append({
                "組別": team,
                "營收": round(revenue, 0),
                "P1銷量(含退貨前)": int(sp1), "P2銷量(含退貨前)": int(sp2),
                "退貨率": round(ret_rate*100, 1),
                "CFO": round(mid["CFO"], 0), "CFI": round(mid["CFI"], 0), "CFF": round(mid["CFF"], 0),
                "事件": ", ".join(mid["events"]) if mid["events"] else "—"
            })

        # KPI 顯示與匯出
        df_kpi = pd.DataFrame(kpi_rows).sort_values("營收", ascending=False)
        st.success("結算完成（KPI 摘要）")
        st.dataframe(df_kpi, use_container_width=True)

        # 匯出：Excel（KPI + 各組 BS/Cashflow），HTML 報告
        with pd.ExcelWriter("season_report.xlsx") as writer:
            df_kpi.to_excel(writer, index=False, sheet_name="KPI")
            bs_rows = []
            cf_rows = []
            for team in TEAM_LIST:
                t = st.session_state.teams[team]
                bs = t["BS"]; cf = t["CASHFLOW"]
                bs_rows.append({"組別": team, **{k:int(v) if isinstance(v,(int,float)) else v for k,v in bs.items()}})
                cf_rows.append({"組別": team, **cf})
            pd.DataFrame(bs_rows).to_excel(writer, index=False, sheet_name="BalanceSheet")
            pd.DataFrame(cf_rows).to_excel(writer, index=False, sheet_name="Cashflow")
        with open("season_report.xlsx", "rb") as f:
            st.download_button("⬇️ 下載 Excel 報告", f.read(), file_name=f"Season{season}_Report.xlsx")

        html = "<h2>Season {}</h2>{}".format(season, df_kpi.to_html(index=False))
        with open("season_report.html", "w", encoding="utf-8") as f: f.write(html)
        with open("season_report.html", "r", encoding="utf-8") as f:
            st.download_button("⬇️ 下載可列印 HTML（可另存 PDF）", f.read(), file_name=f"Season{season}_Report.html")

        # 進入下一季，清掉提交
        clear_decisions()
        st.session_state.game_season += 1
        st.rerun()

# ---------- 主流程 ----------
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
            st.session_state.logged_in = False; st.rerun()

if __name__ == "__main__":
    main()
