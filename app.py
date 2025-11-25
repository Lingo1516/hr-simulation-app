# -*- coding: utf-8 -*-
# Nova BOSS 企業經營模擬系統 V11.1 (修復變數名稱錯誤版)
# Author: Gemini (2025-11-25)

import streamlit as st
import pandas as pd
import os
import pickle
import time

# ==========================================
# 0. 頁面設定
# ==========================================
st.set_page_config(page_title="Nova BOSS 戰情室", layout="wide", page_icon="🏭")

# ==========================================
# 1. 系統參數
# ==========================================
SYSTEM_NAME = "Nova BOSS 企業經營模擬 V11.1"
DB_FILE = "nova_boss_v11.pkl"
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
# 2. 資料庫核心
# ==========================================
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "season": 1,
            "teacher": {"status": "OPEN", "announcement": "歡迎來到 Nova BOSS！", "ranking": []},
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
# 3. 結算引擎
# ==========================================
def run_simulation(db):
    season = db["season"]
    decs = db["decisions"].get(season, {})
    
    scores_p1 = {}; scores_p2 = {}; t_s1 = 0; t_s2 = 0
    leaderboard = []

    # 1. 計算分數
    for team in TEAMS_LIST:
        d = decs.get(team, {"price":{"P1":999,"P2":999}, "ad":{"P1":0,"P2":0}, "rd":{"P1":0,"P2":0}})
        st_tm = db["teams"].get(team, init_team_state(team))
        
        p1 = d["price"]["P1"] if d["price"]["P1"] > 0 else 999
        p2 = d["price"]["P2"] if d["price"]["P2"] > 0 else 999
        
        s1 = 100 * ((PARAMS["price_ref"]["P1"]/p1)**2.5) * (1+d["ad"]["P1"]/500000) * (1+st_tm["rd_level"]["P1"]*0.05)
        s2 = 100 * ((PARAMS["price_ref"]["P2"]/p2)**1.2) * (1+d["ad"]["P2"]/500000) * (1+st_tm["rd_level"]["P2"]*0.05)
        scores_p1[team] = s1; t_s1 += s1
        scores_p2[team] = s2; t_s2 += s2
        
        if d["rd"]["P1"] >= PARAMS["rd_threshold"]: st_tm["rd_level"]["P1"] += 1
        if d["rd"]["P2"] >= PARAMS["rd_threshold"]: st_tm["rd_level"]["P2"] += 1
        db["teams"][team] = st_tm

    # 2. 執行結算
    for team in TEAMS_LIST:
        st_tm = db["teams"][team]; d = decs.get(team)
        if not d: continue

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
        st_tm["loan"] += (d["finance"]["loan_add"] - d["finance"]["loan_pay"])
        st_tm["capacity_lines"] += d["ops"]["buy_lines"]
        
        if st_tm["cash"] < 0:
            ems = abs(st_tm["cash"])
            st_tm["loan"] += ems
            st_tm["cash"] = 0
            
        net_profit = rev - cost_mat - cost_mfg - cost_opex - interest
        st_tm["history"].append({
            "Season": season, "Revenue": rev, "NetProfit": net_profit, 
            "Cash": st_tm["cash"], "Sales": sale1+sale2
        })
        leaderboard.append({"Team": team, "Revenue": rev, "Profit": net_profit, "Cash": st_tm["cash"]})

    leaderboard.sort(key=lambda x: x["Profit"], reverse=True)
    db["teacher"]["ranking"] = leaderboard
    db["season"] += 1
    db["teacher"]["status"] = "OPEN"
    db["decisions"] = {}
    save_db(db)

# ==========================================
# 4. 老師面板
# ==========================================
def render_teacher_panel(db, container):
    season = db["season"]
    with container:
        st.markdown(f"### 👨‍🏫 戰情室 (S{season})")
        
        if season > 1 and db["teacher"]["ranking"]:
            with st.expander(f"🏆 上一季 (S{season-1}) 戰報", expanded=True):
                df_rank = pd.DataFrame(db["teacher"]["ranking"])
                st.dataframe(df_rank, hide_index=True, use_container_width=True)
                winner = df_rank.iloc[0]['Team']
                st.success(f"👑 獲利王：**{winner}**")

        with st.expander("🚨 提交監控", expanded=True):
            status_list = []
            for t in TEAMS_LIST:
                is_sub = t in db["decisions"].get(season, {})
                status_list.append({"組別": t, "狀態": "✅" if is_sub else "Waiting..."})
            st.dataframe(pd.DataFrame(status_list).T, hide_index=True)
            
            not_sub = len(TEAMS_LIST) - len(db["decisions"].get(season, {}))
            if not_sub == 0:
                if st.button("🚀 執行結算", type="primary", use_container_width=True):
                    run_simulation(db)
                    st.balloons(); time.sleep(1); st.rerun()
            else:
                st.warning(f"還有 {not_sub} 組未提交")

        with st.expander("⚙️ 設定", expanded=False):
            if st.button("🔒 鎖定/解鎖"):
                db["teacher"]["status"] = "OPEN" if db["teacher"]["status"]=="LOCKED" else "LOCKED"
                save_db(db); st.rerun()
            if st.button("🧨 重置遊戲"):
                if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()

# ==========================================
# 5. 學生面板
# ==========================================
def render_student_area(db, container):
    season = db["season"]
    with container:
        c1, c2 = st.columns([2, 1])
        c1.header(f"學生決策端 (Season {season})")
        
        who = c2.selectbox("切換組別", TEAMS_LIST)
        if who not in db["teams"]: db["teams"][who]=init_team_state(who); save_db(db); st.rerun()
        st_tm = db["teams"][who]

        st.info(f"📊 上季均價：P1 ${PARAMS['price_ref']['P1']} | P2 ${PARAMS['price_ref']['P2']}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💰 現金", f"${st_tm['cash']:,.0f}")
        m2.metric("📦 庫存(R1/R2)", f"{st_tm['inventory']['R1']} / {st_tm['inventory']['R2']}")
        m3.metric("🏭 產線數", f"{st_tm['capacity_lines']}")
        m4.metric("📈 RD等級", f"P1: Lv{st_tm['rd_level']['P1']} | P2: Lv{st_tm['rd_level']['P2']}")

        if db["teacher"]["status"] == "LOCKED":
            st.error("⛔ 本季決策已鎖定，請等待老師結算。")
            return

        tabs = st.tabs(["1. 行銷與定價", "2. 生產與供應", "3. 財務", "4. 📜 歷史財報"])
        
        old_dec = db["decisions"].get(season, {}).get(who, {})
        def get_nest(k1, k2, default): 
            return old_dec.get(k1, {}).get(k2, default) if isinstance(old_dec, dict) else default

        with tabs[0]:
            c_a, c_b = st.columns(2)
            with c_a:
                st.markdown("##### P1 大眾產品")
                p1_p = st.number_input("P1 價格", 100, 600, get_nest("price","P1", 200), key="p1p")
                p1_ad = st.number_input("P1 廣告費", 0, 5000000, get_nest("ad","P1", 50000), step=10000, key="p1ad")
                st.caption(f"預估毛利: ${p1_p - 160}/個")
            with c_b:
                st.markdown("##### P2 高端產品")
                p2_p = st.number_input("P2 價格", 200, 1000, get_nest("price","P2", 350), key="p2p")
                p2_ad = st.number_input("P2 廣告費", 0, 5000000, get_nest("ad","P2", 50000), step=10000, key="p2ad")
                st.caption(f"預估毛利: ${p2_p - 240}/個")

        with tabs[1]:
            cap = st_tm['capacity_lines'] * 1000
            st.success(f"🏭 目前工廠產能上限： **{cap:,}** 單位 (本季可用)")
            
            c_a, c_b = st.columns(2)
            with c_a:
                st.markdown("##### P1 供應鏈")
                br1 = st.number_input("1. 採購 R1 原料 ($100)", 0, 50000, get_nest("buy_rm","R1",0), key="br1")
                avail_r1 = st_tm['inventory']['R1'] + br1
                st.caption(f"可用原料: {st_tm['inventory']['R1']} + {br1} = **{avail_r1}**")
                
                pp1 = st.number_input(f"2. P1 生產量 (Max:{min(cap, avail_r1)})", 0, 20000, get_nest("production","P1",0), key="pp1")
                if pp1 > avail_r1: st.error("❌ 原料不足")

            with c_b:
                st.markdown("##### P2 供應鏈")
                br2 = st.number_input("1. 採購 R2 原料 ($150)", 0, 50000, get_nest("buy_rm","R2",0), key="br2")
                avail_r2 = st_tm['inventory']['R2'] + br2
                st.caption(f"可用原料: {st_tm['inventory']['R2']} + {br2} = **{avail_r2}**")
                
                pp2 = st.number_input(f"2. P2 生產量 (Max:{min(cap, avail_r2)})", 0, 20000, get_nest("production","P2",0), key="pp2")
                if pp2 > avail_r2: st.error("❌ 原料不足")
            
            if (pp1 + pp2) > cap: st.error(f"❌ 產能超載! 總量 {pp1+pp2} > 上限 {cap}")

            st.divider()
            c_c, c_d = st.columns(2)
            bl = c_c.number_input("購買新產線 ($50萬/條)", 0, 10, get_nest("ops","buy_lines",0), key="bl")
            c_c.write(f"💰 擴充費用: **${bl * 500000:,}** (下季生效)")
            
            rd1 = c_d.number_input("RD P1 投入", 0, 2000000, get_nest("rd","P1",0), step=50000, key="rd1")
            rd2 = c_d.number_input("RD P2 投入", 0, 2000000, get_nest("rd","P2",0), step=50000, key="rd2")
            if rd1 >= 50000 or rd2 >= 50000: c_d.success("✅ 符合升級門檻")
            else: c_d.caption("ℹ️ 升級門檻: $50,000")

        with tabs[2]:
            c_a, c_b = st.columns(2)
            ln = c_a.number_input("新增借款", 0, 10000000, get_nest("finance","loan_add",0), step=100000, key="ln")
            py = c_b.number_input("償還貸款", 0, 10000000, get_nest("finance","loan_pay",0), step=100000, key="py")
            st.caption(f"預計本季利息支出: ${st_tm['loan']*0.02:,.0f}")

        with tabs[3]:
            if st_tm["history"]:
                st.dataframe(pd.DataFrame(st_tm["history"]), use_container_width=True)
            else:
                st.info("尚無歷史資料")

        st.divider()
        st.subheader("🧾 決策總覽與提交")
        
        total_cost = (pp1*60 + pp2*90) + (br1*100 + br2*150) + (p1_ad + p2_ad) + (rd1 + rd2) + (bl * 500000)
        net_finance = ln - py
        est_end_cash = st_tm['cash'] - total_cost + net_finance
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("總預估支出", f"${total_cost:,.0f}")
        col_res2.metric("財務淨流", f"${net_finance:,.0f}")
        col_res3.metric("期末現金預估", f"${est_end_cash:,.0f}", delta_color="normal" if est_end_cash>=0 else "inverse")
        
        has_error = (pp1 > avail_r1) or (pp2 > avail_r2) or ((pp1+pp2) > cap)
        
        if est_end_cash < 0:
            st.error(f"⚠️ 現金不足！預估赤字 ${est_end_cash:,.0f}，請增加借款。")
        
        if st.button("✅ 確認並提交決策", type="primary", use_container_width=True, disabled=has_error):
            new_dec = {
                "price":{"P1":p1_p,"P2":p2_p}, "ad":{"P1":p1_ad,"P2":p2_ad},
                "production":{"P1":pp1,"P2":pp2}, "buy_rm":{"R1":br1,"R2":br2},
                "rd":{"P1":rd1,"P2":rd2}, "ops":{"buy_lines":bl,"sell_lines":0},
                "finance":{"loan_add":ln,"loan_pay":py}
            }
            if season not in db["decisions"]: db["decisions"][season] = {}
            db["decisions"][season][who] = new_dec
            save_db(db)
            st.toast("決策已保存！", icon="🎉")
            time.sleep(1)
            st.rerun()

def main():
    db = load_db()
    st.title(f"🏢 {SYSTEM_NAME}")
    l, r = st.columns([1, 2], gap="large")
    render_teacher_panel(db, l)
    render_student_area(db, r)

if __name__ == "__main__":
    main()
