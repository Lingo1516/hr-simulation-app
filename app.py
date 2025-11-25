# -*- coding: utf-8 -*-
# Nova BOSS 企業經營模擬系統 V10.0 (產能初始狀態說明版)
# Author: Gemini (2025-11-25)

import streamlit as st
import pandas as pd
import os
import pickle
import time
from datetime import datetime

# ==========================================
# 0. 頁面設定
# ==========================================
st.set_page_config(page_title="Nova BOSS 戰情室", layout="wide", page_icon="🏭")

# ==========================================
# 1. 系統參數
# ==========================================
SYSTEM_NAME = "Nova BOSS 企業經營模擬 V10.0"
DB_FILE = "nova_boss_v10.pkl"
TEAMS_LIST = [f"第 {i} 組" for i in range(1, 11)]

PARAMS = {
    "capacity_per_line": 1000,
    "line_setup_cost": 500_000,
    "rm_cost": {"R1": 100, "R2": 150},
    "labor_cost": {"P1": 60, "P2": 90},
    "base_demand": {"P1": 25000, "P2": 18000},
    "price_ref": {"P1": 200, "P2": 350},
}

# ==========================================
# 2. 資料庫邏輯
# ==========================================
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "season": 1,
            "teacher": {"status": "OPEN", "announcement": "歡迎來到 Nova BOSS！", "seed": 2025},
            "teams": {}, "decisions": {}
        }
    try:
        with open(DB_FILE, "rb") as f: return pickle.load(f)
    except: return load_db()

def save_db(db):
    with open(DB_FILE, "wb") as f: pickle.dump(db, f)

def init_team_state(team_name):
    # 重點：初始設定給 5 條產線
    return {
        "cash": 8_000_000,
        "inventory": {"R1": 2000, "R2": 2000, "P1": 500, "P2": 500},
        "capacity_lines": 5, # <--- 這裡！初始就有 5 條
        "loan": 2_000_000, 
        "rd_level": {"P1": 0, "P2": 0}, 
        "history": []
    }

# ==========================================
# 3. 風險監控
# ==========================================
def analyze_team_risk(db, team):
    season = db["season"]
    state = db["teams"].get(team, init_team_state(team))
    dec = db["decisions"].get(season, {}).get(team)
    risk = {"cash": "⚪", "stock": "⚪", "msg": "未提交"}
    if not dec: return risk

    cost_all = (dec["production"]["P1"]*60 + dec["production"]["P2"]*90) + \
               (dec["buy_rm"]["R1"]*100 + dec["buy_rm"]["R2"]*150) + \
               (dec["ad"]["P1"] + dec["ad"]["P2"] + dec["rd"]["P1"] + dec["rd"]["P2"]) + \
               (dec["ops"]["buy_lines"]*500000)
    est_cash = state['cash'] - cost_all + dec["finance"]["loan_add"] - dec["finance"]["loan_pay"]
    
    if est_cash < 0: risk["cash"] = "🔴 破產"
    elif est_cash < 1000000: risk["cash"] = "🟡 吃緊"
    else: risk["cash"] = "🟢 安全"

    avail_p1 = state["inventory"]["P1"] + dec["production"]["P1"]
    avail_p2 = state["inventory"]["P2"] + dec["production"]["P2"]
    if avail_p1 == 0 and avail_p2 == 0: risk["stock"] = "🔴 斷貨"
    elif avail_p1 < 2000: risk["stock"] = "🟡 偏低"
    else: risk["stock"] = "🟢 充足"
    
    risk["msg"] = f"餘額 ${est_cash/10000:.0f}萬"
    return risk

# ==========================================
# 4. 結算引擎
# ==========================================
def run_simulation(db):
    season = db["season"]
    decs = db["decisions"].get(season, {})
    
    # 算分數
    scores_p1 = {}; scores_p2 = {}; t_s1 = 0; t_s2 = 0
    for team in TEAMS_LIST:
        d = decs.get(team, {"price":{"P1":999,"P2":999}, "ad":{"P1":0,"P2":0}, "rd":{"P1":0,"P2":0}})
        st_tm = db["teams"].get(team, init_team_state(team))
        
        p1_p = d["price"]["P1"] if d["price"]["P1"] > 0 else 999
        p2_p = d["price"]["P2"] if d["price"]["P2"] > 0 else 999

        s1 = 100 * ((PARAMS["price_ref"]["P1"]/p1_p)**2.5) * (1+d["ad"]["P1"]/500000) * (1+st_tm["rd_level"]["P1"]*0.05)
        s2 = 100 * ((PARAMS["price_ref"]["P2"]/p2_p)**1.2) * (1+d["ad"]["P2"]/500000) * (1+st_tm["rd_level"]["P2"]*0.05)
        scores_p1[team] = s1; t_s1 += s1
        scores_p2[team] = s2; t_s2 += s2
        
        if d["rd"]["P1"]>0: st_tm["rd_level"]["P1"]+=1
        if d["rd"]["P2"]>0: st_tm["rd_level"]["P2"]+=1
        db["teams"][team] = st_tm

    # 結算
    for team in TEAMS_LIST:
        st_tm = db["teams"][team]; d = decs.get(team)
        if not d: continue
        
        st_tm["inventory"]["R1"] += d["buy_rm"]["R1"]
        st_tm["inventory"]["R2"] += d["buy_rm"]["R2"]
        
        real_prod1 = min(d["production"]["P1"], st_tm["inventory"]["R1"])
        real_prod2 = min(d["production"]["P2"], st_tm["inventory"]["R2"])
        
        st_tm["inventory"]["R1"] -= real_prod1
        st_tm["inventory"]["R2"] -= real_prod2
        st_tm["inventory"]["P1"] += real_prod1
        st_tm["inventory"]["P2"] += real_prod2
        
        share1 = scores_p1[team]/t_s1 if t_s1>0 else 0
        share2 = scores_p2[team]/t_s2 if t_s2>0 else 0
        sale1 = min(int(PARAMS["base_demand"]["P1"]*share1), st_tm["inventory"]["P1"])
        sale2 = min(int(PARAMS["base_demand"]["P2"]*share2), st_tm["inventory"]["P2"])
        st_tm["inventory"]["P1"] -= sale1; st_tm["inventory"]["P2"] -= sale2
        
        rev = sale1*d["price"]["P1"] + sale2*d["price"]["P2"]
        cost = (d["buy_rm"]["R1"]*100 + d["buy_rm"]["R2"]*150) + \
               (real_prod1*60 + real_prod2*90) + \
               (d["ad"]["P1"]+d["ad"]["P2"]+d["rd"]["P1"]+d["rd"]["P2"]) + \
               (d["ops"]["buy_lines"]*500000)
        net_loan = d["finance"]["loan_add"] - d["finance"]["loan_pay"]
        
        st_tm["cash"] += (rev - cost + net_loan)
        st_tm["loan"] += net_loan
        st_tm["capacity_lines"] += d["ops"]["buy_lines"]
        
        if st_tm["cash"] < 0:
            st_tm["loan"] += abs(st_tm["cash"]); st_tm["cash"] = 0
            
        st_tm["history"].append({"Season":season, "Revenue":rev, "Cash":st_tm["cash"]})

    db["season"] += 1
    db["teacher"]["status"] = "OPEN"
    db["decisions"] = {}
    save_db(db)

# ==========================================
# 5. UI 渲染：老師
# ==========================================
def render_teacher_panel(db, container):
    season = db["season"]
    with container:
        st.info(f"👨‍🏫 戰情監控室｜第 {season} 季", icon="📡")
        with st.expander("🚨 風險監控", expanded=True):
            data = []
            for t in TEAMS_LIST:
                r = analyze_team_risk(db, t)
                sub = t in db["decisions"].get(season, {})
                data.append({"組別":t, "狀態":"✅" if sub else "❌", "現金":r["cash"], "庫存":r["stock"], "備註":r["msg"] if sub else "--"})
            st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)
            if any(d["狀態"]=="❌" for d in data): st.warning("尚有未提交組別")
            else: st.success("全員已提交")

        with st.expander("⚙️ 控制台", expanded=False):
            ann = st.text_area("公告", value=db["teacher"]["announcement"], height=60)
            if st.button("更新公告"): db["teacher"]["announcement"]=ann; save_db(db); st.rerun()
            c1, c2 = st.columns(2)
            if c1.button("🔒 鎖定/解鎖"): 
                db["teacher"]["status"] = "OPEN" if db["teacher"]["status"]=="LOCKED" else "LOCKED"
                save_db(db); st.rerun()
            if c2.button("🚀 結算", type="primary", disabled=any(d["狀態"]=="❌" for d in data)):
                run_simulation(db); st.balloons(); time.sleep(1); st.rerun()
        
        if st.button("🧨 重置系統"): 
            if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()

# ==========================================
# 6. UI 渲染：學生 (含初始資產說明)
# ==========================================
def render_student_area(db, container):
    season = db["season"]
    with container:
        c1, c2 = st.columns([1,2])
        c1.header("學生端")
        done = len(db["decisions"].get(season, {}))
        c2.progress(done/len(TEAMS_LIST), f"進度: {done}/{len(TEAMS_LIST)}")
        
        who = st.selectbox("👁️ 操作視角", TEAMS_LIST)
        if who not in db["teams"]: db["teams"][who]=init_team_state(who); save_db(db); st.rerun()
        st_tm = db["teams"][who]

        st.info(f"📊 上季行情： P1 ${PARAMS['price_ref']['P1']} | P2 ${PARAMS['price_ref']['P2']}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("現金", f"${st_tm['cash']:,.0f}")
        m2.metric("倉庫原料", f"{st_tm['inventory']['R1']} / {st_tm['inventory']['R2']}")
        m3.metric("倉庫成品", f"{st_tm['inventory']['P1']} / {st_tm['inventory']['P2']}")
        m4.metric("產線", f"{st_tm['capacity_lines']} 條")

        if db["teacher"]["status"]=="LOCKED": st.error("已鎖定"); return

        with st.form(f"form_{who}"):
            t1, t2, t3 = st.tabs(["1. 行銷", "2. 生產與供應", "3. 財務"])
            
            with t1:
                c_a, c_b = st.columns(2)
                with c_a:
                    st.markdown("### P1 大眾型")
                    d_p1_p = st.number_input("P1 價格", 100, 500, PARAMS['price_ref']['P1'], key="p1p")
                    st.caption("💡 價格越低銷量越好 (高敏感)")
                    d_p1_ad = st.number_input("P1 廣告", 0, 2000000, 50000, step=10000, key="p1ad")
                with c_b:
                    st.markdown("### P2 高端型")
                    d_p2_p = st.number_input("P2 價格", 200, 800, PARAMS['price_ref']['P2'], key="p2p")
                    st.caption("💡 重視品質與品牌 (低敏感)")
                    d_p2_ad = st.number_input("P2 廣告", 0, 2000000, 50000, step=10000, key="p2ad")
                
                with st.expander("📖 行銷規則", expanded=True):
                    st.markdown("* **價格**：P1 參考價$200 (敏感)，P2 參考價$350 (不敏感)。\n* **廣告**：投入資金可提升吸引力。")

            with t2:
                # --- 修正重點：清楚標示現有資產 ---
                cap = st_tm['capacity_lines'] * 1000
                st.warning(f"🏭 **初始資產說明**：目前已擁有 **{st_tm['capacity_lines']} 條產線**。本季立即可生產 **{cap:,}** 單位。")
                
                col_p1, col_p2 = st.columns(2)
                
                with col_p1:
                    st.markdown("### 1️⃣ P1 原料採購")
                    d_buy_r1 = st.number_input("R1 採購量 (單價$100)", 0, 50000, 0, key="br1")
                    total_r1 = st_tm['inventory']['R1'] + d_buy_r1
                    st.caption(f"✅ 可用原料 = {total_r1}")
                    
                    st.markdown("### 2️⃣ P1 生產排程")
                    max_prod_p1 = min(cap, total_r1)
                    d_prod_p1 = st.number_input(f"P1 生產量 (上限 {max_prod_p1})", 0, 20000, 0, key="pp1")
                    st.caption(f"💸 加工費: ${d_prod_p1 * 60:,.0f}")
                    if d_prod_p1 > total_r1: st.error("❌ 原料不足")
                
                with col_p2:
                    st.markdown("### 1️⃣ P2 原料採購")
                    d_buy_r2 = st.number_input("R2 採購量 (單價$150)", 0, 50000, 0, key="br2")
                    total_r2 = st_tm['inventory']['R2'] + d_buy_r2
                    st.caption(f"✅ 可用原料 = {total_r2}")
                    
                    st.markdown("### 2️⃣ P2 生產排程")
                    max_prod_p2 = min(cap, total_r2)
                    d_prod_p2 = st.number_input(f"P2 生產量 (上限 {max_prod_p2})", 0, 20000, 0, key="pp2")
                    st.caption(f"💸 加工費: ${d_prod_p2 * 90:,.0f}")
                    if d_prod_p2 > total_r2: st.error("❌ 原料不足")
                    if (d_prod_p1 + d_prod_p2) > cap: st.error("❌ 產能超載")

                st.divider()
                ca, cb = st.columns(2)
                
                d_buy_ln = ca.number_input("購買新產線 (條)", 0, 5, 0, key="bl", help="每條增加 1000 產能")
                ca.caption(f"💰 費用: ${d_buy_ln * 500000:,} | 🏭 下季生效")
                
                d_rd1 = cb.number_input("RD P1 投入", 0, 500000, 0, step=50000, key="rd1")
                d_rd2 = cb.number_input("RD P2 投入", 0, 500000, 0, step=50000, key="rd2")
                cb.caption("🚀 有投入 ➡️ 下季等級+1 ➡️ 訂單+5%")

                with st.expander("📖 生產與研發規則", expanded=True):
                    st.markdown("""
                    * **初始狀態**：所有組別開局即擁有 5 條產線 (5,000 產能)。
                    * **擴充產線**：本季購買，**下季** 產能才會增加 (+1000/條)。
                    * **RD 研發**：本季投入資金，**下季** 產品等級升級 (訂單+5%)。
                    """)

            with t3:
                ca, cb = st.columns(2)
                d_loan = ca.number_input("借款", 0, 5000000, 0, step=100000, key="ln")
                d_pay = cb.number_input("還款", 0, 5000000, 0, step=100000, key="py")
                with st.expander("📖 財務規則"):
                    st.markdown("* **利率**：季利率 2%。\n* **緊急融資**：現金 < 0 時系統強制借款。")

            cost = (d_prod_p1*60+d_prod_p2*90) + (d_buy_r1*100+d_buy_r2*150) + \
                   (d_p1_ad+d_p2_ad+d_rd1+d_rd2) + (d_buy_ln*500000)
            est_cash = st_tm['cash'] - cost + d_loan - d_pay
            err = (d_prod_p1 > (st_tm['inventory']['R1']+d_buy_r1)) or \
                  (d_prod_p2 > (st_tm['inventory']['R2']+d_buy_r2)) or \
                  ((d_prod_p1+d_prod_p2) > cap)

            st.markdown("---")
            if est_cash < 0: st.error(f"⚠️ 現金不足警告: ${est_cash:,.0f}")
            else: st.success(f"✅ 預估餘額: ${est_cash:,.0f}")

            if st.form_submit_button("提交決策", type="primary", use_container_width=True, disabled=err):
                dec = {
                    "price":{"P1":d_p1_p,"P2":d_p2_p}, "ad":{"P1":d_p1_ad,"P2":d_p2_ad},
                    "production":{"P1":d_prod_p1,"P2":d_prod_p2}, "buy_rm":{"R1":d_buy_r1,"R2":d_buy_r2},
                    "rd":{"P1":d_rd1,"P2":d_rd2}, "ops":{"buy_lines":d_buy_ln,"sell_lines":0},
                    "finance":{"loan_add":d_loan,"loan_pay":d_pay}
                }
                if season not in db["decisions"]: db["decisions"][season]={}
                db["decisions"][season][who] = dec
                save_db(db); st.toast("已保存！"); time.sleep(0.5); st.rerun()

def main():
    db = load_db()
    st.title(f"🏢 {SYSTEM_NAME}")
    l, r = st.columns([1,2], gap="large")
    render_teacher_panel(db, l)
    render_student_area(db, r)

if __name__ == "__main__":
    main()
