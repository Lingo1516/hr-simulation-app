# -*- coding: utf-8 -*-
# Nova BOSS 企業經營模擬系統 V9.5 (完整單一檔案版)
# Author: Gemini (2025-11-25)
# ---------------------------------------------------------
# 包含功能：
# 1. 戰情室模式：左師右生，單一畫面監控。
# 2. 風險雷達：老師端即時顯示各組「破產」或「斷貨」紅燈。
# 3. 學生防呆：原料不足無法生產、現金不足顯示紅字警告。
# 4. 自動結算：市場競賽邏輯 (價格/廣告/RD 分數計算)。

import streamlit as st
import pandas as pd
import os
import pickle
import time
from datetime import datetime

# ==========================================
# 0. 頁面設定 (必須放在第一行)
# ==========================================
st.set_page_config(page_title="Nova BOSS 戰情室", layout="wide", page_icon="🏭")

# ==========================================
# 1. 系統參數與設定
# ==========================================
SYSTEM_NAME = "Nova BOSS 企業經營模擬 V9.5"
DB_FILE = "nova_boss_v95.pkl"

# 產生 10 組
TEAMS_LIST = [f"第 {i} 組" for i in range(1, 11)]

# 經濟與成本參數
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
        # 初始化全新資料庫
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
        return load_db() # 讀取失敗則重置

def save_db(db):
    with open(DB_FILE, "wb") as f:
        pickle.dump(db, f)

def init_team_state(team_name):
    # 初始資產負債狀態
    return {
        "cash": 8_000_000,
        "inventory": {"R1": 2000, "R2": 2000, "P1": 500, "P2": 500},
        "capacity_lines": 5, # 初始 5 條線
        "loan": 2_000_000,
        "rd_level": {"P1": 0, "P2": 0}, # 研發等級
        "history": [] # 歷史紀錄
    }

# ==========================================
# 3. 風險分析邏輯 (Risk Monitor)
# ==========================================
def analyze_team_risk(db, team):
    season = db["season"]
    state = db["teams"].get(team, init_team_state(team))
    dec = db["decisions"].get(season, {}).get(team)
    
    # 預設狀態 (若未提交)
    risk_status = {"cash": "⚪", "stock": "⚪", "msg": "尚未提交"}
    if not dec:
        return risk_status

    # 1. 現金流預測
    # 預估支出 = 生產成本 + 原料採購 + 行銷RD + 建廠
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
    # 預估可賣量 = 現有成品 + 本季生產
    avail_p1 = state["inventory"]["P1"] + dec["production"]["P1"]
    avail_p2 = state["inventory"]["P2"] + dec["production"]["P2"]
    
    if avail_p1 == 0 and avail_p2 == 0:
        risk_status["stock"] = "🔴 斷貨" # 完全沒貨賣
    elif avail_p1 < 3000 or avail_p2 < 2000:
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
    
    # --- Step 1: 計算市場分數 (Market Score) ---
    scores_p1 = {}
    scores_p2 = {}
    total_s1 = 0
    total_s2 = 0
    
    for team in TEAMS_LIST:
        # 若該組沒提交，給予極差的預設值
        d = decs.get(team, {
            "price":{"P1":999,"P2":999}, 
            "ad":{"P1":0,"P2":0}, 
            "rd":{"P1":0,"P2":0}
        })
        state = db["teams"].get(team, init_team_state(team))
        
        # P1 分數：價格彈性 2.5 (高敏感)
        p1_price_factor = (PARAMS["price_ref"]["P1"] / d["price"]["P1"]) ** 2.5
        p1_ad_factor = 1 + (d["ad"]["P1"] / 500_000)
        p1_rd_factor = 1 + (state["rd_level"]["P1"] * 0.05)
        s1 = 100 * p1_price_factor * p1_ad_factor * p1_rd_factor
        
        # P2 分數：價格彈性 1.2 (低敏感)
        p2_price_factor = (PARAMS["price_ref"]["P2"] / d["price"]["P2"]) ** 1.2
        p2_ad_factor = 1 + (d["ad"]["P2"] / 500_000)
        p2_rd_factor = 1 + (state["rd_level"]["P2"] * 0.05)
        s2 = 100 * p2_price_factor * p2_ad_factor * p2_rd_factor
        
        scores_p1[team] = s1; total_s1 += s1
        scores_p2[team] = s2; total_s2 += s2

        # 預先升級 RD (下季生效)
        # 簡易邏輯：投入 > 0 就升級 (可自行調整難度)
        if d["rd"]["P1"] > 0: state["rd_level"]["P1"] += 1
        if d["rd"]["P2"] > 0: state["rd_level"]["P2"] += 1
        db["teams"][team] = state # 暫存狀態

    # --- Step 2: 結算各組 ---
    for team in TEAMS_LIST:
        state = db["teams"][team]
        d = decs.get(team)
        if not d: continue # 跳過未提交者
        
        # A. 生產與扣料
        # 再次檢查原料限制 (雖然前端擋了，後端再保險一次)
        prod1 = min(d["production"]["P1"], state["inventory"]["R1"])
        prod2 = min(d["production"]["P2"], state["inventory"]["R2"])
        
        # 扣原料 -> 加成品
        state["inventory"]["R1"] -= prod1
        state["inventory"]["R2"] -= prod2
        state["inventory"]["P1"] += prod1
        state["inventory"]["P2"] += prod2
        
        # 進原料
        state["inventory"]["R1"] += d["buy_rm"]["R1"]
        state["inventory"]["R2"] += d["buy_rm"]["R2"]
        
        # B. 銷售 (Market Share)
        share1 = scores_p1[team] / total_s1 if total_s1 > 0 else 0
        share2 = scores_p2[team] / total_s2 if total_s2 > 0 else 0
        
        demand1 = int(PARAMS["base_demand"]["P1"] * share1)
        demand2 = int(PARAMS["base_demand"]["P2"] * share2)
        
        # 實際出貨 (受庫存限制)
        sale1 = min(demand1, state["inventory"]["P1"])
        sale2 = min(demand2, state["inventory"]["P2"])
        
        state["inventory"]["P1"] -= sale1
        state["inventory"]["P2"] -= sale2
        
        # C. 現金流計算
        revenue = (sale1 * d["price"]["P1"]) + (sale2 * d["price"]["P2"])
        
        cost_mat = (d["buy_rm"]["R1"] * 100) + (d["buy_rm"]["R2"] * 150)
        cost_mfg = (prod1 * 60) + (prod2 * 90)
        cost_opex = d["ad"]["P1"] + d["ad"]["P2"] + d["rd"]["P1"] + d["rd"]["P2"]
        cost_capex = d["ops"]["buy_lines"] * 500_000
        
        net_loan = d["finance"]["loan_add"] - d["finance"]["loan_pay"]
        
        cash_flow = revenue - cost_mat - cost_mfg - cost_opex - cost_capex + net_loan
        state["cash"] += cash_flow
        state["loan"] += net_loan
        
        # 擴廠 (產線增加)
        state["capacity_lines"] += d["ops"]["buy_lines"]
        
        # 緊急融資 (若現金 < 0)
        if state["cash"] < 0:
            emergency = abs(state["cash"])
            state["loan"] += emergency
            state["cash"] = 0 # 歸零
            
        # 紀錄歷史
        state["history"].append({
            "Season": season,
            "Revenue": revenue,
            "Cash": state["cash"],
            "Sales P1": sale1,
            "Sales P2": sale2
        })
        
    # --- Step 3: 推進季度 ---
    db["season"] += 1
    db["teacher"]["status"] = "OPEN"
    db["decisions"] = {} # 清空決策
    save_db(db)

# ==========================================
# 5. UI 渲染：老師面板 (Teacher Panel)
# ==========================================
def render_teacher_panel(db, container):
    season = db["season"]
    with container:
        st.info(f"👨‍🏫 戰情監控室｜第 {season} 季", icon="📡")
        
        # 1. 全班風險雷達 (Risk Radar)
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
            
            df_risk = pd.DataFrame(risk_data)
            st.dataframe(df_risk, use_container_width=True, hide_index=True)
            
            # 統計
            not_sub = len([x for x in risk_data if x["提交"] == "❌"])
            if not_sub > 0:
                st.warning(f"還有 {not_sub} 組尚未提交！")
            else:
                st.success("全員已提交，可以結算了！")

        # 2. 遊戲控制
        with st.expander("⚙️ 流程控制", expanded=False):
            ann = st.text_area("公告內容", value=db["teacher"]["announcement"], height=70, key="t_ann")
            if st.button("💾 更新公告", key="btn_save_anno"):
                db["teacher"]["announcement"] = ann
                save_db(db)
                st.success("已更新")
            
            c1, c2 = st.columns(2)
            is_locked = (db["teacher"]["status"] == "LOCKED")
            with c1:
                btn_label = "🔓 解鎖" if is_locked else "🔒 鎖定"
                if st.button(btn_label, key="btn_lock", use_container_width=True):
                    db["teacher"]["status"] = "OPEN" if is_locked else "LOCKED"
                    save_db(db)
                    st.rerun()
            with c2:
                if st.button("🚀 執行結算", type="primary", use_container_width=True, key="btn_run", disabled=(not_sub > 0)):
                    run_simulation(db)
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
        
        # 3. 重置
        st.divider()
        if st.button("🧨 重置整個系統 (清除資料)", key="btn_reset_all"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()

# ==========================================
# 6. UI 渲染：學生操作區 (Student Area)
# ==========================================
def render_student_area(db, container):
    season = db["season"]
    with container:
        # 標題與進度
        c_head, c_prog = st.columns([1, 2])
        with c_head:
            st.header("學生端模擬")
        with c_prog:
            done_cnt = len(db["decisions"].get(season, {}))
            st.progress(done_cnt/len(TEAMS_LIST), text=f"本季進度: {done_cnt}/{len(TEAMS_LIST)}")

        # 視角選擇
        target_team = st.selectbox("👁️ 選擇操作組別 (God Mode)：", TEAMS_LIST, key="sel_target_team")
        
        # 初始化該組
        if target_team not in db["teams"]:
            db["teams"][target_team] = init_team_state(target_team)
            save_db(db); st.rerun()
            
        state = db["teams"][target_team]
        
        # 顯示資源儀表板
        st.markdown(f"#### 📝 {target_team} 決策面板")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("現金", f"${state['cash']:,.0f}")
        m2.metric("原料庫存 (R1/R2)", f"{state['inventory']['R1']} / {state['inventory']['R2']}")
        m3.metric("成品庫存 (P1/P2)", f"{state['inventory']['P1']} / {state['inventory']['P2']}")
        m4.metric("產線數", f"{state['capacity_lines']} 條")

        # 鎖定狀態
        if db["teacher"]["status"] == "LOCKED":
            st.error("⛔ 本季已鎖定，等待老師結算。")
            if target_team in db["decisions"].get(season, {}):
                st.info("已提交。")
            return

        # 決策表單
        with st.form(key=f"form_{target_team}"):
            k = target_team
            t1, t2, t3 = st.tabs(["1. 行銷 (Marketing)", "2. 生產 (Production)", "3. 財務 (Finance)"])
            
            with t1:
                c1, c2 = st.columns(2)
                d_p1_p = c1.number_input("P1 價格", 100, 500, 200, key=f"{k}_p1p", help="參考價 $200")
                d_p1_ad = c1.number_input("P1 廣告", 0, 1000000, 50000, step=10000, key=f"{k}_p1ad")
                d_p2_p = c2.number_input("P2 價格", 200, 800, 350, key=f"{k}_p2p", help="參考價 $350")
                d_p2_ad = c2.number_input("P2 廣告", 0, 1000000, 50000, step=10000, key=f"{k}_p2ad")

            with t2:
                st.caption(f"目前總產能: {state['capacity_lines'] * 1000} 單位")
                max_cap = state['capacity_lines'] * 1000
                c1, c2 = st.columns(2)
                
                # P1 生產區
                with c1:
                    max_p1 = min(max_cap, state['inventory']['R1'])
                    d_prod_p1 = st.number_input(f"P1 生產 (Max: {max_p1})", 0, 20000, 0, key=f"{k}_pp1")
                    # 防呆
                    err_p1 = d_prod_p1 > state['inventory']['R1']
                    if err_p1: st.error(f"❌ 原料 R1 不足 (剩 {state['inventory']['R1']})")
                    d_buy_r1 = st.number_input("R1 採購", 0, 50000, d_prod_p1, key=f"{k}_br1")

                # P2 生產區
                with c2:
                    max_p2 = min(max_cap, state['inventory']['R2'])
                    d_prod_p2 = st.number_input(f"P2 生產 (Max: {max_p2})", 0, 20000, 0, key=f"{k}_pp2")
                    # 防呆
                    err_p2 = d_prod_p2 > state['inventory']['R2']
                    if err_p2: st.error(f"❌ 原料 R2 不足 (剩 {state['inventory']['R2']})")
                    d_buy_r2 = st.number_input("R2 採購", 0, 50000, d_prod_p2, key=f"{k}_br2")

                st.divider()
                c3, c4 = st.columns(2)
                d_buy_line = c3.number_input("購買產線 (條)", 0, 5, 0, help="每條 50萬", key=f"{k}_bl")
                d_rd_p1 = c4.number_input("RD P1 投入", 0, 500000, 0, step=50000, key=f"{k}_rd1")
                d_rd_p2 = c4.number_input("RD P2 投入", 0, 500000, 0, step=50000, key=f"{k}_rd2")

            with t3:
                c1, c2 = st.columns(2)
                d_loan = c1.number_input("銀行借款", 0, 5000000, 0, step=100000, key=f"{k}_loan")
                d_pay = c2.number_input("償還貸款", 0, 5000000, 0, step=100000, key=f"{k}_pay")

            # 預算試算與防呆檢查
            cost_prod = (d_prod_p1 * 60) + (d_prod_p2 * 90)
            cost_mat  = (d_buy_r1 * 100) + (d_buy_r2 * 150)
            cost_exp  = d_p1_ad + d_p2_ad + d_rd_p1 + d_rd_p2
            cost_capex = d_buy_line * 500_000
            total_out = cost_prod + cost_mat + cost_exp + cost_capex
            
            est_cash = state['cash'] - total_out + d_loan - d_pay
            
            has_error = err_p1 or err_p2
            
            st.markdown("---")
            if est_cash < 0:
                st.error(f"⚠️ 現金不足警告！預估餘額 ${est_cash:,.0f} (請借款或減少支出)")
            else:
                st.success(f"✅ 預算正常。預估餘額 ${est_cash:,.0f}")

            # 提交按鈕
            btn_submit = st.form_submit_button("✅ 提交決策", type="primary", use_container_width=True, disabled=has_error)
            
            if btn_submit:
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
    
    # 左右分割佈局
    left_col, right_col = st.columns([1, 2], gap="large")
    
    # 渲染左側 (老師)
    render_teacher_panel(db, left_col)
    
    # 渲染右側 (學生)
    render_student_area(db, right_col)

if __name__ == "__main__":
    main()
