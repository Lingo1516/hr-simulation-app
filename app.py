# -*- coding: utf-8 -*-
# Nova BOSS 企業經營模擬系統 V22.0 (雙按鈕優化版)
# Author: Gemini (2025-11-27)

import streamlit as st
import pandas as pd
import os
import pickle
import time
import random

# ==========================================
# 0. 頁面設定
# ==========================================
st.set_page_config(page_title="Nova BOSS", layout="wide", page_icon="🏭")

# ==========================================
# 1. 系統參數
# ==========================================
SYSTEM_NAME = "Nova BOSS 企業經營模擬 V22.0"
DB_FILE = "nova_boss_v22.pkl"
TEAMS_LIST = [f"第 {i} 組" for i in range(1, 11)]

# 帳號設定
USERS = {"admin": "admin"}
for t in TEAMS_LIST: USERS[t] = "1234"

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
# 2. 輔助函式
# ==========================================
def analyze_price_p1(price):
    cost = 160 
    ref = PARAMS["price_ref"]["P1"]
    if price < cost: return f"💸 **賠本賣！** 成本$160，每賣虧 ${cost - price}。"
    if price == cost: return "😐 **做白工**。價格等於成本。"
    if price >= ref * 1.25: return "😰 **太貴了**！銷量會很慘。"
    if price > ref * 1.05: return "📈 **稍高行情**。適合產能不足時。"
    if price < ref * 0.95: return "🔥 **殺價搶市**。銷量大增，注意產能。"
    return "✅ **標準行情**。"

def analyze_price_p2(price):
    cost = 240
    ref = PARAMS["price_ref"]["P2"]
    if price < cost: return f"💸 **賠本賣！** 成本$240，每賣虧 ${cost - price}。"
    if price >= ref * 1.3: return "😰 **太貴了**！"
    return "✅ **合理區間**。"

def analyze_cash(cash):
    if cash < 0: return "🛑 **危險！會倒閉！** 現金是負的，請去「3. 財務」借款！"
    if cash < 1000000: return "⚠️ **危險邊緣**。現金剩不到 100 萬。"
    return "🟢 **資金安全**。"

def generate_strategy_report(rec):
    report = []
    dt = rec.get("Details", {})
    p1_price = dt.get('PriceP1', 200)
    p1_sales = dt.get('SaleQtyP1', 0)
    if p1_sales < 500:
        if p1_price > 220: report.append("🔴 **P1 滯銷**：定價過高，建議降價。")
        else: report.append("🟠 **P1 銷量低**：可能是缺貨或對手太強。")
    
    net_profit = rec['NetProfit']
    if net_profit < 0:
        report.append(f"💸 **虧損警報**：本季虧損 ${abs(net_profit):,.0f}。")
    
    if rec['EndCash'] < 0:
        report.append("🛑 **資金斷鏈**：現金為負，已強制借貸。")
    return report

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

    # 補齊機器人
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
        start_cash = st_tm["cash"]

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
        
        rev_p1 = sale1 * d["price"]["P1"]
        rev_p2 = sale2 * d["price"]["P2"]
        rev = rev_p1 + rev_p2
        
        cost_mat = (d["buy_rm"]["R1"]*100 + d["buy_rm"]["R2"]*150)
        cost_mfg = (real_prod1*60 + real_prod2*90)
        cost_ad = (d["ad"]["P1"] + d["ad"]["P2"])
        cost_rd = (d["rd"]["P1"] + d["rd"]["P2"])
        cost_capex = (d["ops"]["buy_lines"]*500000)
        interest = st_tm["loan"] * 0.02
        
        total_expense = cost_mat + cost_mfg + cost_ad + cost_rd + cost_capex + interest
        net_loan = d["finance"]["loan_add"] - d["finance"]["loan_pay"]
        
        st_tm["cash"] += (rev - total_expense + net_loan)
        st_tm["loan"] += net_loan
        st_tm["capacity_lines"] += d["ops"]["buy_lines"]
        
        if st_tm["cash"] < 0:
            ems = abs(st_tm["cash"])
            st_tm["loan"] += ems
            st_tm["cash"] = 0
            
        net_profit = rev - total_expense
        
        st_tm["history"].append({
            "Season": season, 
            "StartCash": start_cash, 
            "Revenue": rev, 
            "Expense": total_expense, 
            "NetProfit": net_profit, 
            "EndCash": st_tm["cash"], 
            "Sales": sale1+sale2,
            "NetLoan": net_loan,
            "Details": {
                "SaleQtyP1": sale1, "PriceP1": d["price"]["P1"], "RevP1": rev_p1,
                "SaleQtyP2": sale2, "PriceP2": d["price"]["P2"], "RevP2": rev_p2,
                "BuyQtyR1": d["buy_rm"]["R1"], "CostMat": cost_mat,
                "CostMfg": cost_mfg, "CostAd": cost_ad, "CostRD": cost_rd,
                "CostCapex": cost_capex, "Interest": interest
            }
        })
        leaderboard.append({"Team": team, "Revenue": rev, "Profit": net_profit, "Cash": st_tm["cash"]})

    leaderboard.sort(key=lambda x: x["Profit"], reverse=True)
    db["teacher"]["ranking"] = leaderboard
    db["season"] += 1
    db["teacher"]["status"] = "OPEN"
    db["decisions"] = {}
    save_db(db)

# ==========================================
# 5. 登入頁面
# ==========================================
def render_login_page():
    st.markdown(f"<h1 style='text-align: center;'>🏭 {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab_teacher, tab_student = st.tabs(["👨‍🏫 老師登入 (Admin)", "🧑‍🎓 學生登入 (Team)"])
    
    with tab_teacher:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.form("teacher_login"):
                t_user = st.text_input("帳號")
                t_pw = st.text_input("密碼", type="password")
                if st.form_submit_button("老師登入", type="primary", use_container_width=True):
                    if t_user == "admin" and t_pw == USERS["admin"]:
                        st.session_state["logged_in"] = True
                        st.session_state["user"] = "admin"
                        st.session_state["role"] = "teacher"
                        st.success("歡迎老師！")
                        time.sleep(0.5); st.rerun()
                    else: st.error("帳號或密碼錯誤")

    with tab_student:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.form("student_login"):
                s_team = st.selectbox("請選擇你的組別", TEAMS_LIST)
                s_pw = st.text_input("組別密碼", type="password")
                if st.form_submit_button("學生登入", type="primary", use_container_width=True):
                    if s_team in USERS and USERS[s_team] == s_pw:
                        st.session_state["logged_in"] = True
                        st.session_state["user"] = s_team
                        st.session_state["role"] = "student"
                        st.success(f"{s_team} 登入成功！")
                        time.sleep(0.5); st.rerun()
                    else: st.error("密碼錯誤")

# ==========================================
# 6. 老師面板
# ==========================================
def render_teacher_panel(db):
    season = db["season"]
    with st.sidebar:
        if st.button("🔄 刷新數據", type="primary"): st.rerun()
        st.write("---")
        if st.button("登出"): st.session_state.clear(); st.rerun()

    st.info(f"👨‍🏫 老師戰情室 (S{season})", icon="👨‍🏫")
    
    if season > 1:
        with st.expander(f"🏆 上季 (S{season-1}) 戰績排行榜", expanded=True):
            df_rank = pd.DataFrame(db["teacher"]["ranking"])
            if not df_rank.empty:
                df_rank.columns = ["組別", "本季營收", "本季淨利", "手頭現金"]
                st.dataframe(df_rank, hide_index=True, use_container_width=True)

    with st.expander("⚙️ 遊戲控制", expanded=True):
        status_list = []
        for t in TEAMS_LIST:
            is_sub = t in db["decisions"].get(season, {})
            status_list.append({"組別": t, "狀態": "✅ 已交" if is_sub else "⏳ 未交"})
        st.dataframe(pd.DataFrame(status_list).T, hide_index=True, use_container_width=True)
        
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("🎲 隨機代打 (演示用)"):
            for t in TEAMS_LIST:
                if t not in db["decisions"].get(season, {}):
                    rand_dec = {
                        "price":{"P1":random.randint(180,220),"P2":random.randint(330,370)},
                        "ad":{"P1":50000,"P2":50000},
                        "production":{"P1":1000,"P2":500},
                        "buy_rm":{"R1":1000,"R2":500},
                        "rd":{"P1":0,"P2":0}, "ops":{"buy_lines":0,"sell_lines":0},
                        "finance":{"loan_add":0,"loan_pay":0}
                    }
                    if season not in db["decisions"]: db["decisions"][season] = {}
                    db["decisions"][season][t] = rand_dec
            save_db(db); st.success("已自動產生！"); time.sleep(1); st.rerun()

        if col_btn2.button("🚀 結算本季", type="primary"):
            run_simulation(db); st.balloons(); time.sleep(1); st.rerun()
        
        st.divider()
        if st.button("🧨 重置遊戲"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()

# ==========================================
# 7. 學生面板 (雙按鈕版)
# ==========================================
def render_student_area(db, team_name):
    season = db["season"]
    
    with st.sidebar:
        st.title(f"👤 {team_name}")
        if st.button("🔄 刷新頁面"): st.rerun()
        st.write("---")
        if st.button("登出"): st.session_state.clear(); st.rerun()

    st.title(f"🏭 {team_name} 決策端 (Season {season})")
    
    if team_name not in db["teams"]: db["teams"][team_name]=init_team_state(team_name); save_db(db); st.rerun()
    st_tm = db["teams"][team_name]

    # 狀態檢查
    is_submitted = team_name in db["decisions"].get(season, {})

    # --- 戰績通知 ---
    if season > 1 and db["teacher"]["ranking"]:
        my_rank = 999
        my_profit = 0
        for idx, row in enumerate(db["teacher"]["ranking"]):
            if row["Team"] == team_name:
                my_rank = idx + 1
                my_profit = row["Profit"]
                break
        if my_rank == 1: st.success(f"🏆 **恭喜！上季第 {my_rank} 名 (獲利王)！** 淨利 ${my_profit:,.0f}")
        elif my_rank <= 3: st.info(f"🥈 **表現優異！上季第 {my_rank} 名！** 淨利 ${my_profit:,.0f}")
        else: st.warning(f"💪 **再接再厲！上季第 {my_rank} 名。** 淨利 ${my_profit:,.0f}")

        # 排行榜表格
        st.markdown(f"**🏆 上季 (S{season-1}) 市場戰報**")
        df_rank = pd.DataFrame(db["teacher"]["ranking"])
        df_student_view = df_rank[["Team", "Profit"]].copy()
        df_student_view.columns = ["組別", "本季淨利"]
        df_student_view.index = range(1, len(df_student_view) + 1)
        st.dataframe(df_student_view, use_container_width=True)
        st.divider()

    # --- AI 顧問 ---
    if st_tm['history']:
        with st.expander(f"🕵️ **AI 經營顧問診斷**", expanded=False):
            for adv in generate_strategy_report(st_tm['history'][-1]): st.write(adv)

    if db["teacher"]["status"] == "LOCKED":
        st.error("⛔ 老師正在結算中，請稍候..."); return

    # --- 資金橋 ---
    if not st_tm['history']:
        st.markdown("### 💰 資金流向")
        r1, r2 = st.columns(2)
        r1.metric("1. 初始資金", "$8,000,000")
        r2.metric("2. 本季期初現金", "$8,000,000", delta="由此開始")
    else:
        last_rec = st_tm['history'][-1]
        net_change = last_rec['Revenue'] - last_rec['Expense'] + last_rec.get('NetLoan', 0)
        dt = last_rec.get("Details", {})
        st.markdown("### 💰 資金流向")
        c1, c2, c3 = st.columns(3)
        c1.metric("上季期初", f"${last_rec['StartCash']:,.0f}")
        c2.metric("淨變動", f"{net_change:+,.0f}", delta="點我看細項", help=f"營收 ${last_rec['Revenue']:,.0f} - 支出 ${last_rec['Expense']:,.0f}")
        c3.metric("本季期初", f"${st_tm['cash']:,.0f}", delta="可用資金", delta_color="normal")
        
        with st.expander("🔍 查看詳細帳目 (算式)", expanded=False):
            d1, d2 = st.columns(2)
            d1.success(f"**🟢 營收 (+${last_rec['Revenue']:,.0f})**")
            d1.write(f"* P1: {dt.get('SaleQtyP1',0)}個 x ${dt.get('PriceP1',0)} = ${dt.get('RevP1',0):,.0f}")
            d1.write(f"* P2: {dt.get('SaleQtyP2',0)}個 x ${dt.get('PriceP2',0)} = ${dt.get('RevP2',0):,.0f}")
            d2.error(f"**🔴 支出 (-${last_rec['Expense']:,.0f})**")
            d2.write(f"* 原料: ${dt.get('CostMat',0):,.0f} | 加工: ${dt.get('CostMfg',0):,.0f}")
            d2.write(f"* 費用: ${dt.get('CostAd',0)+dt.get('CostRD',0):,.0f} | 利息: ${dt.get('Interest',0):,.0f}")

    # --- 庫存與負債 ---
    st.markdown("---")
    i1, i2 = st.columns([2, 1])
    with i1:
        st.markdown("###### 🏭 營運庫存")
        o1, o2, o3, o4, o5 = st.columns(5)
        o1.metric("R1原料", f"{st_tm['inventory']['R1']}")
        o2.metric("R2原料", f"{st_tm['inventory']['R2']}")
        o3.metric("P1成品", f"{st_tm['inventory']['P1']}")
        o4.metric("P2成品", f"{st_tm['inventory']['P2']}")
        o5.metric("產線", f"{st_tm['capacity_lines']}")
    with i2:
        st.markdown("###### 🏦 負債")
        st.metric("貸款總額", f"${st_tm['loan']:,.0f}", delta=f"利息 -${st_tm['loan']*0.02:,.0f}/季", delta_color="inverse")

    # --- 決策輸入 ---
    st.markdown("### 📝 決策輸入")
    st.info("👇 請依照 **Step 1 -> Step 2 -> Step 3** 的順序完成決策。")
    
    old_dec = db["decisions"].get(season, {}).get(team_name, {})
    def get_nest(k1, k2, d): return old_dec.get(k1, {}).get(k2, d) if isinstance(old_dec, dict) else d

    st.subheader("Step 1: 行銷定價")
    with st.container(border=True):
        mk1, mk2 = st.columns(2)
        with mk1:
            p1_p = st.number_input("P1 價格 (成本$160)", 100, 500, get_nest("price","P1", 200), key=f"{team_name}_p1p")
            st.caption(analyze_price_p1(p1_p))
            p1_ad = st.number_input("P1 廣告", 0, 1000000, get_nest("ad","P1", 50000), step=10000, key=f"{team_name}_p1ad")
        with mk2:
            p2_p = st.number_input("P2 價格 (成本$240)", 200, 800, get_nest("price","P2", 350), key=f"{team_name}_p2p")
            st.caption(analyze_price_p2(p2_p))
            p2_ad = st.number_input("P2 廣告", 0, 1000000, get_nest("ad","P2", 50000), step=10000, key=f"{team_name}_p2ad")

    st.subheader("Step 2: 生產與擴充")
    with st.container(border=True):
        cap = st_tm['capacity_lines'] * 1000
        st.info(f"💡 本季產能上限：**{cap:,}**")
        pd1, pd2 = st.columns(2)
        with pd1:
            br1 = st.number_input("買 R1 原料 ($100)", 0, 20000, get_nest("buy_rm","R1",0), key=f"{team_name}_br1")
            avail_r1 = st_tm['inventory']['R1'] + br1
            pp1 = st.number_input(f"生產 P1 (夠做:{avail_r1})", 0, 20000, get_nest("production","P1",0), key=f"{team_name}_pp1")
            if pp1 > avail_r1: st.error("❌ 原料不足")
        with pd2:
            br2 = st.number_input("買 R2 原料 ($150)", 0, 20000, get_nest("buy_rm","R2",0), key=f"{team_name}_br2")
            avail_r2 = st_tm['inventory']['R2'] + br2
            pp2 = st.number_input(f"生產 P2 (夠做:{avail_r2})", 0, 20000, get_nest("production","P2",0), key=f"{team_name}_pp2")
            if pp2 > avail_r2: st.error("❌ 原料不足")
        
        if (pp1+pp2) > cap: st.error("❌ 產能不足")

        with st.expander("進階：擴充與研發"):
            ex1, ex2 = st.columns(2)
            bl = ex1.number_input("買產線 ($50萬)", 0, 5, get_nest("ops","buy_lines",0), key=f"{team_name}_bl")
            ex1.caption("⚠️ 下季生效")
            rd1 = ex2.number_input("RD P1", 0, 1000000, get_nest("rd","P1",0), step=50000, key=f"{team_name}_rd1")
            rd2 = ex2.number_input("RD P2", 0, 1000000, get_nest("rd","P2",0), step=50000, key=f"{team_name}_rd2")

    st.subheader("Step 3: 財務")
    with st.container(border=True):
        cost = (pp1*60+pp2*90) + (br1*100+br2*150) + (p1_ad+p2_ad+rd1+rd2) + (bl*500000)
        f1, f2 = st.columns([2, 1])
        f1.write(f"🧾 總支出預估: **${cost:,.0f}**")
        precash = st_tm['cash'] - cost
        if precash < 0: f1.error(f"⚠️ 會破產! 缺 ${abs(precash):,.0f}")
        else: f1.success(f"✅ 安全 (剩 ${precash:,.0f})")
        
        ln = f2.number_input("借款 (+)", 0, 10000000, get_nest("finance","loan_add",0), step=100000, key=f"{team_name}_ln")
        py = f2.number_input("還款 (-)", 0, 10000000, get_nest("finance","loan_pay",0), step=100000, key=f"{team_name}_py")

    st.divider()
    has_err = (pp1 > avail_r1) or (pp2 > avail_r2) or ((pp1+pp2)>cap)
    
    # --- 🔥 雙按鈕邏輯 (核心修改) ---
    col_submit, col_next = st.columns(2)
    
    # 按鈕 1: 提交/修改
    label_sub = "✏️ 修改並重新提交" if is_submitted else "✅ 提交決策"
    if col_submit.button(label_sub, type="secondary", use_container_width=True, disabled=has_err, key=f"{team_name}_sub"):
        new_dec = {
            "price":{"P1":p1_p,"P2":p2_p}, "ad":{"P1":p1_ad,"P2":p2_ad},
            "production":{"P1":pp1,"P2":pp2}, "buy_rm":{"R1":br1,"R2":br2},
            "rd":{"P1":rd1,"P2":rd2}, "ops":{"buy_lines":bl,"sell_lines":0},
            "finance":{"loan_add":ln,"loan_pay":py}
        }
        if season not in db["decisions"]: db["decisions"][season] = {}
        db["decisions"][season][team_name] = new_dec
        save_db(db); st.balloons(); st.success("提交成功！"); time.sleep(1); st.rerun()

    # 按鈕 2: 進入下一季
    if is_submitted:
        if col_next.button("🚀 進入下一季 (刷新)", type="primary", use_container_width=True):
            st.rerun() # 只要重整，如果老師結算了，season 就會變，畫面自然跳轉

# ==========================================
# 8. 主程式
# ==========================================
def main():
    # container 用來控制 layout
    container = st.container()
    
    if "logged_in" not in st.session_state:
        render_login_page()
    else:
        db = load_db()
        role = st.session_state["role"]
        user = st.session_state["user"]
        
        if role == "teacher":
            render_teacher_panel(db) 
        else:
            render_student_area(db, user)

if __name__ == "__main__":
    main()
