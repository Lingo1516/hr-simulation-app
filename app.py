# -*- coding: utf-8 -*-
# Nova BOSS 企業經營模擬系統 V15.1 (戰績排名通知版)
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
SYSTEM_NAME = "Nova BOSS 企業經營模擬 V15.1"
DB_FILE = "nova_boss_v15_1.pkl"
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

# AI 顧問報告生成
def generate_strategy_report(rec):
    report = []
    dt = rec.get("Details", {})
    p1_price = dt.get('PriceP1', 200)
    p1_sales = dt.get('SaleQtyP1', 0)
    if p1_sales < 500:
        if p1_price > 220:
            report.append("🔴 **P1 滯銷**：定價過高 ($" + str(p1_price) + ")，建議降價。")
        else:
            report.append("🟠 **P1 銷量低**：可能是缺貨或對手太強。")
    
    net_profit = rec['NetProfit']
    if net_profit < 0:
        report.append(f"💸 **虧損警報**：本季虧損 ${abs(net_profit):,.0f}。請檢查毛利與費用。")
    
    if rec['EndCash'] < 0:
        report.append("🛑 **資金斷鏈**：現金為負，已強制借貸，請注意利息壓力。")

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
        
        # 財務明細
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
        # 排行榜用 NetProfit 排序
        leaderboard.append({"Team": team, "Revenue": rev, "Profit": net_profit, "Cash": st_tm["cash"]})

    # 排序並存檔
    leaderboard.sort(key=lambda x: x["Profit"], reverse=True)
    db["teacher"]["ranking"] = leaderboard
    db["season"] += 1
    db["teacher"]["status"] = "OPEN"
    db["decisions"] = {}
    save_db(db)

# ==========================================
# 5. 老師面板
# ==========================================
def render_teacher_panel(db, container):
    season = db["season"]
    with container:
        st.markdown(f"### 👨‍🏫 老師控制台 (S{season})")
        
        if season > 1:
            with st.expander(f"🏆 上一季 (S{season-1}) 戰績排行榜", expanded=True):
                df_rank = pd.DataFrame(db["teacher"]["ranking"])
                df_rank.columns = ["組別", "本季營收", "本季淨利", "手頭現金"]
                st.dataframe(df_rank, hide_index=True, use_container_width=True)
                st.caption("💡 注意：排行榜顯示的是「該季度」的表現，而非累積總和。")

        with st.expander("⚙️ 遊戲控制與演示", expanded=True):
            status_list = []
            for t in TEAMS_LIST:
                is_sub = t in db["decisions"].get(season, {})
                status_list.append({"組別": t, "狀態": "✅ 已交" if is_sub else "⏳ 未交"})
            st.dataframe(pd.DataFrame(status_list).T, hide_index=True, use_container_width=True)
            
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("🎲 幫沒交的組隨機填 (演示用)"):
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
                save_db(db)
                st.success("已自動產生資料！")
                time.sleep(1); st.rerun()

            if col_btn2.button("🚀 結算本季", type="primary"):
                run_simulation(db)
                st.balloons(); time.sleep(1); st.rerun()
            
            st.divider()
            if st.button("🧨 重置遊戲"):
                if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()

# ==========================================
# 6. 學生面板 (含戰績排名)
# ==========================================
def render_student_area(db, container):
    season = db["season"]
    with container:
        c1, c2 = st.columns([2, 1])
        c1.header(f"學生決策端 (Season {season})")
        who = c2.selectbox("切換操作組別", TEAMS_LIST)
        
        if who not in db["teams"]: db["teams"][who]=init_team_state(who); save_db(db); st.rerun()
        st_tm = db["teams"][who]

        # --- 🔥 戰績排名通知 (新功能) ---
        if season > 1 and db["teacher"]["ranking"]:
            # 找出自己的排名
            my_rank = 999
            my_profit = 0
            for idx, row in enumerate(db["teacher"]["ranking"]):
                if row["Team"] == who:
                    my_rank = idx + 1
                    my_profit = row["Profit"]
                    break
            
            # 根據排名給予不同顏色的回饋
            if my_rank == 1:
                st.success(f"🏆 **恭喜！上一季你們是第 {my_rank} 名 (獲利王)！** 本季淨利 ${my_profit:,.0f}")
            elif my_rank <= 3:
                st.info(f"🥈 **表現優異！上一季排名第 {my_rank} 名！** 本季淨利 ${my_profit:,.0f}")
            elif my_rank <= 7:
                st.warning(f"📊 **再接再厲！上一季排名第 {my_rank} 名。** 本季淨利 ${my_profit:,.0f}")
            else:
                st.error(f"💪 **請加油！上一季排名第 {my_rank} 名。** 本季淨利 ${my_profit:,.0f}，請檢查策略！")
        # ------------------------------

        st.info("👇 請依照 **Step 1 -> Step 2 -> Step 3** 的順序完成決策。")
        
        if db["teacher"]["status"] == "LOCKED":
            st.error("⛔ 老師正在結算中，請稍候..."); return

        # --- 1. 資金橋 ---
        if not st_tm['history']:
            st.markdown("### 💰 資金流向")
            r1_c1, r1_c2 = st.columns(2)
            r1_c1.metric("1. 初始資金", "$8,000,000")
            r1_c2.metric("2. 本季期初現金", "$8,000,000", delta="由此開始")
        else:
            last_rec = st_tm['history'][-1]
            net_change = last_rec['Revenue'] - last_rec['Expense'] + last_rec.get('NetLoan', 0)
            dt = last_rec.get("Details", {})
            
            st.markdown("### 💰 資金流向 (上一季結果分解)")
            r1_c1, r1_c2, r1_c3 = st.columns(3)
            r1_c1.metric(f"1. S{season-1} 期初", f"${last_rec['StartCash']:,.0f}")
            r1_c2.metric(f"2. S{season-1} 營收", f"+${last_rec['Revenue']:,.0f}")
            r1_c3.metric(f"3. S{season-1} 支出", f"-${last_rec['Expense']:,.0f}")
            
            with st.expander("🔍 點此查看：詳細帳目算式 (Drill-down)", expanded=False):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.success(f"**🟢 營收細項 (+${last_rec['Revenue']:,.0f})**")
                    st.write(f"* P1 銷售: {dt.get('SaleQtyP1',0)}個 × ${dt.get('PriceP1',0)} = ${dt.get('RevP1',0):,.0f}")
                    st.write(f"* P2 銷售: {dt.get('SaleQtyP2',0)}個 × ${dt.get('PriceP2',0)} = ${dt.get('RevP2',0):,.0f}")
                with col_d2:
                    st.error(f"**🔴 支出細項 (-${last_rec['Expense']:,.0f})**")
                    st.write(f"* 原料: ${dt.get('CostMat',0):,.0f}")
                    st.write(f"* 加工: ${dt.get('CostMfg',0):,.0f}")
                    st.write(f"* 行銷RD: ${dt.get('CostAd',0)+dt.get('CostRD',0):,.0f}")
                    st.write(f"* 擴廠: ${dt.get('CostCapex',0):,.0f}")
                    st.write(f"* 利息: ${dt.get('Interest',0):,.0f}")

            st.write("---") 
            r2_c1, r2_c2 = st.columns([1, 2])
            r2_c1.metric(f"4. 淨變動", f"{net_change:+,.0f}", delta="含借貸變動")
            r2_c2.metric(f"5. S{season} 本季期初現金", f"${st_tm['cash']:,.0f}", delta="本季可用資金", delta_color="normal")

        # --- 2. 庫存與負債 ---
        st.markdown("---")
        col_info1, col_info2 = st.columns([2, 1])
        with col_info1:
            st.markdown("###### 🏭 營運庫存")
            o1, o2, o3, o4, o5 = st.columns(5)
            o1.metric("R1原料", f"{st_tm['inventory']['R1']}")
            o2.metric("R2原料", f"{st_tm['inventory']['R2']}")
            o3.metric("P1成品", f"{st_tm['inventory']['P1']}")
            o4.metric("P2成品", f"{st_tm['inventory']['P2']}")
            o5.metric("產線", f"{st_tm['capacity_lines']}條")
        
        with col_info2:
            st.markdown("###### 🏦 負債狀況")
            st.metric("銀行貸款總額", f"${st_tm['loan']:,.0f}", delta=f"利息 -${st_tm['loan']*0.02:,.0f}/季", delta_color="inverse")

        # --- 3. 決策輸入區 ---
        old_dec = db["decisions"].get(season, {}).get(who, {})
        def get_nest(k1, k2, d): return old_dec.get(k1, {}).get(k2, d) if isinstance(old_dec, dict) else d

        st.markdown("### 📝 決策輸入")
        st.subheader("Step 1: 想要賣多少錢？ (行銷)")
        with st.container(border=True):
            col_mk1, col_mk2 = st.columns(2)
            with col_mk1:
                st.markdown("##### 🛒 P1 大眾產品")
                p1_p = st.number_input("P1 售價 (成本$160)", 100, 500, get_nest("price","P1", 200), key="p1p")
                st.caption(analyze_price_p1(p1_p)) 
                p1_ad = st.number_input("P1 廣告費 (建議 $50,000)", 0, 1000000, get_nest("ad","P1", 50000), step=10000, key="p1ad")

            with col_mk2:
                st.markdown("##### 💎 P2 高端產品")
                p2_p = st.number_input("P2 售價 (成本$240)", 200, 800, get_nest("price","P2", 350), key="p2p")
                st.caption(analyze_price_p2(p2_p))
                p2_ad = st.number_input("P2 廣告費 (建議 $50,000)", 0, 1000000, get_nest("ad","P2", 50000), step=10000, key="p2ad")

        st.subheader("Step 2: 想要生產多少？ (生產)")
        with st.container(border=True):
            cap = st_tm['capacity_lines'] * 1000
            st.info(f"💡 你的工廠本季最多只能做 **{cap:,}** 個產品。")
            
            col_pd1, col_pd2 = st.columns(2)
            with col_pd1:
                st.markdown("**1️⃣ 先買原料 R1**")
                br1 = st.number_input("買多少 R1？ ($100/個)", 0, 20000, get_nest("buy_rm","R1",0), key="br1")
                avail_r1 = st_tm['inventory']['R1'] + br1
                st.markdown(f"**2️⃣ 再排生產 P1** (原料夠做: {avail_r1})")
                pp1 = st.number_input("生產多少 P1？", 0, 20000, get_nest("production","P1",0), key="pp1")
                if pp1 > avail_r1: st.error(f"❌ 原料不足！你只有 {avail_r1} 個原料。")

            with col_pd2:
                st.markdown("**1️⃣ 先買原料 R2**")
                br2 = st.number_input("買多少 R2？ ($150/個)", 0, 20000, get_nest("buy_rm","R2",0), key="br2")
                avail_r2 = st_tm['inventory']['R2'] + br2
                st.markdown(f"**2️⃣ 再排生產 P2** (原料夠做: {avail_r2})")
                pp2 = st.number_input("生產多少 P2？", 0, 20000, get_nest("production","P2",0), key="pp2")
                if pp2 > avail_r2: st.error(f"❌ 原料不足！你只有 {avail_r2} 個原料。")
            
            if (pp1 + pp2) > cap: st.error(f"❌ 產能爆炸了！你只能做 {cap} 個，但你排了 {pp1+pp2} 個。")

            with st.expander("進階選項：擴充產線 & 研發升級"):
                c_ex1, c_ex2 = st.columns(2)
                bl = c_ex1.number_input("買新產線 ($50萬/條)", 0, 5, get_nest("ops","buy_lines",0), key="bl")
                c_ex1.caption("⚠️ 下季才會生效")
                rd1 = c_ex2.number_input("RD P1 投入", 0, 1000000, get_nest("rd","P1",0), step=50000, key="rd1")
                rd2 = c_ex2.number_input("RD P2 投入", 0, 1000000, get_nest("rd","P2",0), step=50000, key="rd2")
                if rd1 >= 50000 or rd2 >= 50000: c_ex2.success("✨ 有投入夠多錢，下季會升級！")

        st.subheader("Step 3: 錢夠不夠？ (財務)")
        with st.container(border=True):
            total_cost = (pp1*60 + pp2*90) + (br1*100 + br2*150) + (p1_ad + p2_ad) + (rd1 + rd2) + (bl * 500000)
            
            c_fn1, c_fn2 = st.columns([2, 1])
            with c_fn1:
                st.write(f"🧾 本季總支出預估： **${total_cost:,.0f}**")
                pre_cash = st_tm['cash'] - total_cost
                if pre_cash < 0:
                    st.error(f"⚠️ 警告：你的現金會變成 ${pre_cash:,.0f} (破產)，請右邊趕快借錢！")
                else:
                    st.success(f"✅ 安全：付完錢後還剩 ${pre_cash:,.0f}。")

            with c_fn2:
                st.warning(f"📢 初始狀態：本團隊目前負債 **${st_tm['loan']:,}** (承接舊工廠貸款)。")
                ln = st.number_input("跟銀行借款 (+)", 0, 10000000, get_nest("finance","loan_add",0), step=100000, key="ln")
                py = st.number_input("償還貸款 (-)", 0, 10000000, get_nest("finance","loan_pay",0), step=100000, key="py")

        st.divider()
        final_cash = st_tm['cash'] - total_cost + ln - py
        
        col_submit, col_msg = st.columns([1, 2])
        with col_msg:
            st.markdown(f"### 預估期末現金： ${final_cash:,.0f}")
            st.caption(analyze_cash(final_cash))

        has_error = (pp1 > avail_r1) or (pp2 > avail_r2) or ((pp1+pp2) > cap)
        
        if col_submit.button("✅ 送出決策 (提交)", type="primary", use_container_width=True, disabled=has_error):
            new_dec = {
                "price":{"P1":p1_p,"P2":p2_p}, "ad":{"P1":p1_ad,"P2":p2_ad},
                "production":{"P1":pp1,"P2":pp2}, "buy_rm":{"R1":br1,"R2":br2},
                "rd":{"P1":rd1,"P2":rd2}, "ops":{"buy_lines":bl,"sell_lines":0},
                "finance":{"loan_add":ln,"loan_pay":py}
            }
            if season not in db["decisions"]: db["decisions"][season] = {}
            db["decisions"][season][who] = new_dec
            save_db(db)
            st.balloons()
            st.success("🎉 提交成功！請等待老師結算。")
            time.sleep(2); st.rerun()

def main():
    db = load_db()
    st.title(f"🏢 {SYSTEM_NAME}")
    l, r = st.columns([1, 2], gap="large")
    render_teacher_panel(db, l)
    render_student_area(db, r)

if __name__ == "__main__":
    main()
