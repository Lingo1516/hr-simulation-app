# -*- coding: utf-8 -*-
# Nova BOSS 企業經營模擬系統 V13.1 (定價邏輯優化版)
# Author: Gemini (2025-11-25)

import streamlit as st
import pandas as pd
import os
import pickle
import time
import random

# ==========================================
# 0. 頁面設定
# ==========================================
st.set_page_config(page_title="Nova BOSS 經營模擬", layout="wide", page_icon="🏭")

# ==========================================
# 1. 系統參數
# ==========================================
SYSTEM_NAME = "Nova BOSS 企業經營模擬 V13.1"
DB_FILE = "nova_boss_v13.pkl"
TEAMS_LIST = [f"第 {i} 組" for i in range(1, 11)]

PARAMS = {
    "capacity_per_line": 1000,
    "line_setup_cost": 500_000,
    "rd_threshold": 50_000,
    "rm_cost": {"R1": 100, "R2": 150},
    "labor_cost": {"P1": 60, "P2": 90},
    "base_demand": {"P1": 25000, "P2": 18000},
    "price_ref": {"P1": 200, "P2": 350},
}

# ==========================================
# 2. 輔助函式：白話文翻譯機 (邏輯修正區)
# ==========================================
def analyze_price_p1(price):
    cost = 160 
    ref = PARAMS["price_ref"]["P1"] # 200
    
    if price < cost: 
        return f"💸 **賠錢賣！** 成本$160，定價${price}，每賣一個虧 ${cost - price}！"
    if price == cost: 
        return "😐 **做白工**。價格等於成本，沒賺頭。"
    
    # 修正：給予緩衝區間，不要一點點差異就說是高價
    if price >= ref * 1.25: # > 250
        return "😰 **太貴了！** 大眾產品定太高，消費者會跑光光。"
    if price > ref * 1.05: # 211 ~ 250
        return "📈 **稍高於行情**。犧牲部分銷量換取較高毛利，適合產能不足時。"
    if price < ref * 0.95: # < 190
        return "🔥 **殺價搶市**。價格極具競爭力，銷量會大增，請注意產能是否足夠！"
        
    # 190 ~ 210 之間
    return "✅ **標準行情**。符合大眾市場預期，銷量穩定。"

def analyze_price_p2(price):
    cost = 240
    ref = PARAMS["price_ref"]["P2"] # 350
    
    if price < cost: 
        return f"💸 **賠錢賣！** 成本$240，定價${price}，虧損中。"
    
    if price >= ref * 1.3: # > 455
        return "😰 **定價過高**。即使是高端產品，這價格也太離譜了。"
    if price > ref * 1.05: # 368 ~ 455
        return "💎 **精品策略**。鎖定頂級客群，若有投入廣告與RD效果更佳。"
    if price < ref * 0.95: # < 332
        return "📉 **平價高端**。用低價吸引高端客戶，薄利多銷。"
        
    return "✅ **合理區間**。符合高端市場行情。"

def analyze_cash(cash):
    if cash < 0: return "🛑 **危險！會倒閉！** 現金是負的，請去「3. 財務」借款！"
    if cash < 1000000: return "⚠️ **危險邊緣**。現金剩不到 100 萬，建議多借一點備用。"
    return "🟢 **資金安全**。"

# ==========================================
# 3. 資料庫核心
# ==========================================
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "season": 1,
            "teacher": {"status": "OPEN", "announcement": "歡迎！請依照順序進行決策。", "ranking": []},
            "teams": {}, "decisions": {}
        }
    try:
        with open(DB_FILE, "rb") as f: return pickle.load(f)
    except: return load_db()

def save_db(db):
    with open(DB_FILE, "wb") as f: pickle.dump(db, f)

def init_team_state(team_name):
    return {
        "cash": 8_000_000,
        "inventory": {"R1": 2000, "R2": 2000, "P1": 500, "P2": 500},
        "capacity_lines": 5, 
        "loan": 2_000_000, 
        "rd_level": {"P1": 0, "P2": 0}, 
        "history": []
    }

# ==========================================
# 4. 結算引擎
# ==========================================
def run_simulation(db):
    season = db["season"]
    decs = db["decisions"].get(season, {})
    leaderboard = []

    for t in TEAMS_LIST:
        if t not in decs:
            decs[t] = {
                "price":{"P1":200,"P2":350}, "ad":{"P1":0,"P2":0},
                "production":{"P1":0,"P2":0}, "buy_rm":{"R1":0,"R2":0},
                "rd":{"P1":0,"P2":0}, "ops":{"buy_lines":0,"sell_lines":0},
                "finance":{"loan_add":0,"loan_pay":0}
            }

    scores_p1 = {}; scores_p2 = {}; t_s1 = 0; t_s2 = 0
    for team in TEAMS_LIST:
        d = decs[team]
        st_tm = db["teams"].get(team, init_team_state(team))
        
        p1 = max(1, d["price"]["P1"])
        p2 = max(1, d["price"]["P2"])

        s1 = 100 * ((PARAMS["price_ref"]["P1"]/p1)**2.5) * (1+d["ad"]["P1"]/500000) * (1+st_tm["rd_level"]["P1"]*0.05)
        s2 = 100 * ((PARAMS["price_ref"]["P2"]/p2)**1.2) * (1+d["ad"]["P2"]/500000) * (1+st_tm["rd_level"]["P2"]*0.05)
        scores_p1[team] = s1; t_s1 += s1
        scores_p2[team] = s2; t_s2 += s2
        
        if d["rd"]["P1"] >= PARAMS["rd_threshold"]: st_tm["rd_level"]["P1"] += 1
        if d["rd"]["P2"] >= PARAMS["rd_threshold"]: st_tm["rd_level"]["P2"] += 1
        db["teams"][team] = st_tm

    for team in TEAMS_LIST:
        st_tm = db["teams"][team]; d = decs[team]

        st_tm["inventory"]["R1"] += d["buy_rm"]["R1"]
        st_tm["inventory"]["R2"] += d["buy_rm"]["R2"]
        
        real_prod1 = min(d["production"]["P1"], st_tm["inventory"]["R1"])
        real_prod2 = min(d["production"]["P2"], st_tm["inventory"]["R2"])
        st_tm["inventory"]["R1"] -= real_prod1; st_tm["inventory"]["R2"] -= real_prod2
        st_tm["inventory"]["P1"] += real_prod1; st_tm["inventory"]["P2"] += real_prod2
        
        share1 = scores_p1[team]/t_s1 if t_s1>0 else 0
        share2 = scores_p2[team]/t_s2 if t_s2>0 else 0
        sale1 = min(int(PARAMS["base_demand"]["P1"]*share1), st_tm["inventory"]["P1"])
        sale2 = min(int(PARAMS["base_demand"]["P2"]*share2), st_tm["inventory"]["P2"])
        st_tm["inventory"]["P1"] -= sale1; st_tm["inventory"]["P2"] -= sale2
        
        rev = sale1*d["price"]["P1"] + sale2*d["price"]["P2"]
        cost_mat = (d["buy_rm"]["R1"]*100 + d["buy_rm"]["R2"]*150)
        cost_mfg = (real_prod1*60 + real_prod2*90)
        cost_opex = (d["ad"]["P1"]+d["ad"]["P2"]+d["rd"]["P1"]+d["rd"]["P2"])
        cost_capex = (d["ops"]["buy_lines"]*500000)
        interest = st_tm["loan"] * 0.02
        
        net_cash_flow = rev - cost_mat - cost_mfg - cost_opex - cost_capex - interest + d["finance"]["loan_add"] - d["finance"]["loan_pay"]
        
        st_tm["cash"] += net_cash_flow
        st_tm["loan"] += (d["finance
