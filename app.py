# -*- coding: utf-8 -*-
# Nova BOSS 企業經營模擬系統 V9.6 (完整穩定版)
# Author: Gemini (2025-11-25)
# ---------------------------------------------------------
# 包含功能：
# 1. 戰情室模式：左師右生，單一畫面監控。
# 2. 風險雷達：老師端即時顯示各組「破產」或「斷貨」紅燈。
# 3. 智能學生介面：含浮動提示(Tooltip)、即時成本試算、紅字防呆。
# 4. 市場情報：自動顯示上季平均成交價。

import streamlit as st
import pandas as pd
import os
import pickle
import time
from datetime import datetime

# ==========================================
# 0. 頁面設定 (必須放在程式的第一行)
# ==========================================
st.set_page_config(page_title="Nova BOSS 戰情室", layout="wide", page_icon="🏭")

# ==========================================
# 1. 系統參數與設定
# ==========================================
SYSTEM_NAME = "Nova BOSS 企業經營模擬 V9.6"
DB_FILE = "nova_boss_v96.pkl"

# 產生 10 組
TEAMS_LIST = [f"第 {i} 組" for i in range(1, 11)]

# 經濟與成本參數 (寫死供全域呼叫)
PARAMS = {
    "capacity_per_line": 1000,   # 每條產線產能
    "line_setup_cost": 500_000,  # 擴充產線成本
    "rm_cost": {"R1": 100, "R2": 150},
    "labor_cost": {"P1": 60, "P2": 90},
    "base_demand": {"P1": 25000, "P2": 18000},
    "price_ref": {"P1": 200, "P2": 350},  # 參考售價
}

# ==========================================
# 2. 資料庫核心邏輯
# ==========================================
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "season": 1,
            "teacher": {"status": "OPEN", "announcement": "歡迎來到 Nova BOSS！請開始第 1 季決策。", "seed": 2025},
            "teams": {},      # 各組資產狀態
            "decisions": {}   # 各組當季決策
        }
    try:
        with open(DB_FILE, "rb") as f:
            return pickle.load(f)
    except:
        return load_db()

def save_db(db):
    with open(DB_FILE, "wb") as f:
        pickle.dump(db, f)

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
# 3. 風險分析邏輯 (Risk Monitor)
# ==========================================
def analyze_team_risk(db, team):
    season = db["season"]
    state = db["teams"].get(team, init_team_state(team))
    dec = db["decisions"].get(season, {}).get(team)
    
    risk_status = {"cash": "⚪", "stock": "⚪", "msg": "尚未提交"}
    if not dec:
        return risk_status

    # 1. 現金流預測
    cost_prod = (dec["production"]["P1"] * 60) + (dec["production"]["P2"] * 90)
    cost_mat  = (dec["buy_rm"]["R1"] * 100) + (dec["buy_rm"]["R2"] * 150)
    cost_exp  = dec["ad"]["P1"] + dec["ad"]["P2"] + dec["rd"]["P1"] + dec["rd"]["P2"]
    cost_capex = dec["ops"]["buy_lines"] * 500_000
    total_out = cost_prod + cost_mat + cost_exp + cost_capex
    net_loan = dec["finance"]["loan_add"] - dec["finance"]["loan_pay"]
    
    est_cash = state['cash'] - total_out + net_loan
    
    if est_cash < 0:
        risk_status["cash"] = "🔴 破產"
    elif est_cash < 1000000:
        risk_status["cash"] = "🟡 吃緊"
    else:
        risk_status["cash"] = "🟢 安全"

    # 2. 庫存斷貨預警
    avail_p1 = state["inventory"]["P1"] + dec["production"]["P1"]
    avail_p2 = state["inventory"]["P2"] + dec["production"]["P2"]
    
    if avail_p1 == 0 and avail_p2 == 0:
        risk_status["stock"] = "🔴 斷貨"
    elif avail_p1 < 2000 or avail_p2 < 1000:
        risk_status["stock"] = "🟡 偏低"
    else:
        risk_status["stock"] = "🟢 充足"
        
    risk_status["msg"] = f"預估餘額 ${est_cash/10000:.0f}萬"
    return risk_status

# ==========================================
# 4. 結算引擎 (Simulation Engine)
# ==========================================
def run_simulation(db):
    season = db["season"]
    decs = db["decisions"].get(season, {})
    
    # --- Step 1: 計算市場分數 ---
    scores_p1 = {}; scores_p2 = {}
    total_s1 = 0; total_s2 = 0
    
    for team in TEAMS_LIST:
        d = decs.get(team, {
            "price":{"P1":999,"P2":999}, "ad":{"P1":0,"P2":0}, "rd":{"P1":0,"P2":0}
        })
        state = db["teams"].get(team, init_team_state(team))
        
        # P1 (高敏感)
        p1_price_factor = (PARAMS["price_ref"]["P1"] / d["price"]["P1"]) ** 2.5
        p1_ad_factor = 1 + (d["ad"]["P1"] / 500_000)
        p1_rd_factor = 1 + (state["rd_level"]["P1"] * 0.05)
        s1 = 100 * p1_price_factor * p1_ad_factor * p1_rd_factor
        
        # P2 (低敏感)
        p2_price_factor = (PARAMS["price_ref"]["P2"] / d["price"]["P2"]) ** 1.2
        p2_ad_factor = 1 + (d["ad"]["P2"] / 500_000)
        p2_rd_factor = 1 + (state["rd_level"]["P2"] * 0.05)
        s2 = 100 * p2_price_factor * p2_ad_factor * p2_rd_factor
        
        scores_p1[team] = s1; total_s1 += s1
        scores_p2[team] = s2; total_s2 += s2

        # RD 升級
        if d["rd"]["P1"] > 0: state["rd_level"]["P1"] += 1
        if d["rd"]["P2"] > 0: state["rd_level"]["P2"] += 1
        db["teams"][team] = state

    # --- Step 2: 結算各組 ---
    for team in TEAMS_LIST:
        state = db["teams"][team]
        d = decs.get(team)
        if not d: continue 
        
        # A. 生產
        prod1 = min(d["production"]["P1"], state["inventory"]["R1"])
        prod2 = min(d["production"]["P2"], state["inventory"]["R2"])
        state["inventory"]["R1"] -= prod1
        state["inventory"]["R2"] -= prod2
        state["inventory"]["P1"] += prod1
        state["inventory"]["P2"] += prod2
        state["inventory"]["R1"] += d["buy_rm"]["R1"]
        state["inventory"]["R2"] += d["buy_rm"]["R2"]
        
        # B. 銷售
        share1 = scores_p1[team] / total_s1 if total_s1 > 0 else 0
        share2 = scores_p2[team] / total_s2 if total_s2 > 0 else 0
        sale1 = min(int(PARAMS["base_demand"]["P1"] * share1), state["inventory"]["P1"])
        sale2 = min(int(PARAMS["base_demand"]["P2"] * share2), state["inventory"]["P2"])
        state["inventory"]["P1"] -= sale1
        state["inventory"]["P2"] -= sale2
        
        # C. 現金流
        revenue = (sale1 * d["price"]["P1"]) + (sale2 * d["price"]["P2"])
        cost_mat = (d["buy_rm"]["R1"] * 100) + (d["buy_rm"]["R2"] * 150)
        cost_mfg = (prod1 * 60) + (prod2 * 90)
        cost_opex = d["ad"]["P1"] + d["ad"]["P2"] + d["rd"]["P1"] + d["rd"]["P2"]
        cost_capex = d["ops"]["buy_lines"] * 500_000
        net_loan = d["finance"]["loan_add"] - d["finance"]["loan_pay"]
        
        cash_flow = revenue - cost_mat - cost_mfg - cost_opex - cost_capex + net_loan
        state["cash"] += cash_flow
        state["loan"] += net_loan
        state["capacity_lines"] += d["ops"]["buy_lines"]
        
        if state["cash"] < 0:
            state["loan"] += abs(state["cash"])
            state["cash"] = 0 
            
        state["history"].append({
            "Season": season, "Revenue": revenue, "Cash": state["cash"],
            "Sales P1": sale1, "Sales P2": sale2
        })
        
    db["season"] += 1
    db["teacher"]["status"] = "OPEN"
    db["decisions"] = {}
    save_db(db)

# ==========================================
# 5. UI 渲染：老師面板
# ==========================================
def render_teacher_panel(db, container):
    season = db["season"]
    with container:
        st.info(f"👨‍🏫 戰情監控室｜第 {season} 季", icon="📡")
        
        # 1. 全班風險雷達
        with st.expander("🚨 全班風險監控 (Risk Radar)", expanded=True):
            risk_data = []
            for team in TEAMS_LIST:
                status = analyze_team_risk(db, team)
                submitted = team in db["decisions"].get(season, {})
                risk_data.append({
                    "組別": team,
                    "提交": "✅" if submitted else "❌",
                    "現金預警": status["cash"],
                    "庫存預警": status["stock"],
                    "財務摘要": status["msg"] if submitted else "--"
                })
            
            st.dataframe(pd.DataFrame(risk_data), use_container_width=True, hide_index=True)
            
            not_sub = len([x for x in risk_data if x["提交"] == "❌"])
            if not_sub > 0:
                st.warning(f"還有 {not_sub} 組未提交！")
            else:
                st.success("全員已提交！")

        # 2. 遊戲控制
        with st.expander("⚙️ 流程控制", expanded=False):
            ann = st.text_area("公告內容", value=db["teacher"]["announcement"], height=70, key="t_ann")
            if st.button("💾 更新公告", key="btn_save_anno"):
                db["teacher"]["announcement"] = ann
                save_db(db); st.success("已更新")
            
            c1, c2 = st.columns(2)
            is_locked = (db["teacher"]["status"] == "LOCKED")
            with c1:
                btn_label = "🔓 解鎖" if is_locked else "🔒 鎖定"
                if st.button(btn_label, key="btn_lock", use_container_width=True):
                    db["teacher"]["status"] = "OPEN" if is_locked else "LOCKED"
                    save_db(db); st.rerun()
            with c2:
                if st.button("🚀 執行結算", type="primary", use_container_width=True, key="btn_run", disabled=(not_sub > 0)):
                    run_simulation(db)
                    st.balloons()
                    time.sleep(1); st.rerun()
        
        # 3. 重置
        st.divider()
        if st.button("🧨 重置系統", key="btn_reset_all"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()

# ==========================================
# 6. UI 渲染：學生面板 (V9.6 智能提示版)
# ==========================================
def render_student_area(db, container):
    season = db["season"]
    with container:
        # 標題
        c_head, c_prog = st.columns([1, 2])
        with c_head:
            st.header("學生端模擬")
        with c_prog:
            done_cnt = len(db["decisions"].get(season, {}))
            st.progress(done_cnt/len(TEAMS_LIST), text=f"本季進度: {done_cnt}/{len(TEAMS_LIST)}")

        # 視角
        target_team = st.selectbox("👁️ 選擇操作組別：", TEAMS_LIST, key="sel_target_team")
        if target_team not in db["teams"]:
            db["teams"][target_team] = init_team_state(target_team)
            save_db(db); st.rerun()
        state = db["teams"][target_team]
        
        # --- 市場情報 ---
        if season == 1:
            ref_p1_msg = f"${PARAMS['price_ref']['P1']} (歷史均價)"
            ref_p2_msg = f"${PARAMS['price_ref']['P2']} (歷史均價)"
        else:
            last_decs = db["decisions"].get(season - 1, {})
            if last_decs:
                avg_p1 = sum(d["price"]["P1"] for d in last_decs.values()) / len(last_decs)
                avg_p2 = sum(d["price"]["P2"] for d in last_decs.values()) / len(last_decs)
                ref_p1_msg = f"${avg_p1:.0f} (上季平均)"
                ref_p2_msg = f"${avg_p2:.0f} (上季平均)"
            else:
                ref_p1_msg = "無資料"; ref_p2_msg = "無資料"

        with st.expander("📊 市場行情快報", expanded=True):
            st.info(f"💡 P1 行情: {ref_p1_msg} | 💡 P2 行情: {ref_p2_msg}")

        # 資源
        st.markdown(f"#### 📝 {target_team} 決策面板")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("現金水位", f"${state['cash']:,.0f}")
        m2.metric("原料庫存", f"{state['inventory']['R1']} / {state['inventory']['R2']}")
        m3.metric("成品庫存", f"{state['inventory']['P1']} / {state['inventory']['P2']}")
        m4.metric("產線數", f"{state['capacity_lines']} 條")

        if db["teacher"]["status"] == "LOCKED":
            st.error("⛔ 本季已鎖定，等待老師結算。"); return

        # --- 決策表單 ---
        with st.form(key=f"form_{target_team}"):
            k = target_team
            t1, t2, t3 = st.tabs(["1. 行銷", "2. 生產", "3. 財務"])
            
            with t1:
                st.markdown("##### 🎯 價格與推廣")
                c1, c2 = st.columns(2)
                with c1:
                    d_p1_p = st.number_input("P1 價格", 100, 500, PARAMS['price_ref']['P1'], key=f"{k}_p1p", help="價格越低銷量越高，P1 價格敏感。")
                    d_p1_ad = st.number_input("P1 廣告", 0, 2000000, 50000, step=10000, key=f"{k}_p1ad", help="增加曝光。")
                    st.caption(f"ℹ️ P1 預估毛利: ${d_p1_p - 160}/個")
                with c2:
                    d_p2_p = st.number_input("P2 價格", 200, 800, PARAMS['price_ref']['P2'], key=f"{k}_p2p", help="P2 重視品質，價格彈性低。")
                    d_p2_ad = st.number_input("P2 廣告", 0, 2000000, 50000, step=10000, key=f"{k}_p2ad", help="高端客戶受廣告影響深。")
                    st.caption(f"ℹ️ P2 預估毛利: ${d_p2_p - 240}/個")

            with t2:
                st.markdown("##### 🏭 生產與供應")
                current_cap = state['capacity_lines'] * 1000
                st.info(f"工廠產能上限： **{current_cap:,}** 單位")
                c1, c2 = st.columns(2)
                
                with c1:
                    max_p1 = min(current_cap, state['inventory']['R1'])
                    d_prod_p1 = st.number_input(f"P1 生產 (Max:{max_p1})", 0, 20000, 0, key=f"{k}_pp1")
                    st.caption(f"💸 加工費: ${d_prod_p1*60:,}")
                    if d_prod_p1 > state['inventory']['R1']: st.error("❌ 原料 R1 不足")
                    d_buy_r1 = st.number_input("R1 採購 ($100)", 0, 50000, d_prod_p1, key=f"{k}_br1")

                with c2:
                    d_prod_p2 = st.number_input(f"P2 生產", 0, 20000, 0, key=f"{k}_pp2")
                    st.caption(f"💸 加工費: ${d_prod_p2*90:,}")
                    if d_prod_p2 > state['inventory']['R2']: st.error("❌ 原料 R2 不足")
                    if (d_prod_p1 + d_prod_p2) > current_cap: st.error("❌ 產能超載")
                    d_buy_r2 = st.number_input("R2 採購 ($150)", 0, 50000, d_prod_p2, key=f"{k}_br2")

                st.divider()
                c3, c4 = st.columns(2)
                d_buy_line = c3.number_input("購買產線 ($50萬)", 0, 5, 0, key=f"{k}_bl", help="下季啟用")
                d_rd_p1 = c4.number_input("RD P1 投入", 0, 500000, 0, step=50000, key=f"{k}_rd1")
                d_rd_p2 = c4.number_input("RD P2 投入", 0, 500000, 0, step=50000, key=f"{k}_rd2")

            with t3:
                st.markdown("##### 💰 資金調度")
                c1, c2 = st.columns(2)
                d_loan = c1.number_input("新增借款", 0, 5000000, 0, step=100000, key=f"{k}_loan")
                d_pay = c2.number_input("償還貸款", 0, 5000000, 0, step=100000, key=f"{k}_pay")

            # 預算試算
            cost_total = (d_prod_p1*60 + d_prod_p2*90) + (d_buy_r1*100 + d_buy_r2*150) + \
                         (d_p1_ad + d_p2_ad + d_rd_p1 + d_rd_p2) + (d_buy_line*500000)
            est_cash = state['cash'] - cost_total + d_loan - d_pay
            
            has_error = (d_prod_p1 > state['inventory']['R1']) or \
                        (d_prod_p2 > state['inventory']['R2']) or \
                        ((d_prod_p1 + d_prod_p2) > current_cap)
            
            st.markdown("---")
            if est_cash < 0:
                st.error(f"⚠️ 現金赤字警告！預估餘額 ${est_cash:,.0f} (請借款或刪減支出)")
            else:
                st.success(f"✅ 資金充裕。預估餘額 ${est_cash:,.0f}")

            if st.form_submit_button("✅ 提交決策", type="primary", use_container_width=True, disabled=has_error):
                dec_data = {
                    "price": {"P1": d_p1_p, "P2": d_p2_p},
                    "ad": {"P1": d_p1_ad, "P2": d_p2_ad},
                    "production": {"P1": d_prod_p1, "P2": d_prod_p2},
                    "buy_rm": {"R1": d_buy_r1, "R2": d_buy_r2},
                    "rd": {"P1": d_rd_p1, "P2": d_rd_p2},
                    "ops": {"buy_lines": d_buy_line, "sell_lines": 0},
                    "finance": {"loan_add": d_loan, "loan_pay": d_pay},
                }
                if season not in db["decisions"]: db["decisions"][season] = {}
                db["decisions"][season][target_team] = dec_data
                save_db(db)
                st.toast(f"{target_team} 決策已保存！", icon="🎉")
                time.sleep(0.5)
                st.rerun()

# ==========================================
# 7. 主程式 (Main)
# ==========================================
def main():
    db = load_db()
    st.title(f"🏢 {SYSTEM_NAME}")
    
    left_col, right_col = st.columns([1, 2], gap="large")
    render_teacher_panel(db, left_col)
    render_student_area(db, right_col)

if __name__ == "__main__":
    main()
