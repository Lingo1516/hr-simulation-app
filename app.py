# -*- coding: utf-8 -*-
# Nova BOSS Simulator V9.0 - Command Center Edition
# Author: Gemini (2025-11-25)
# ---------------------------------------------------------
# 新增特色：
# 1. 左右分割畫面 (Split View)：左師右生，即時對照。
# 2. 進度儀表板 (Progress Dashboard)：右側上方即時顯示全班提交狀況。
# 3. 視角切換 (Spy Mode)：老師可隨時切換查看/操作任一組學生的畫面。

import streamlit as st
import pandas as pd
import os
import pickle
import time
from datetime import datetime

# ==========================================
# 1. 系統常數與參數
# ==========================================
SYSTEM_NAME = "Nova BOSS 經營戰情室 V9.0"
DB_FILE = "nova_boss_v9.pkl"

# 產生 10 組
TEAMS_LIST = [f"第 {i} 組" for i in range(1, 11)]

# 經濟參數 (同 V8.0)
PARAMS = {
    "tax_rate": 0.25,
    "interest_rate": 0.02,
    "capacity_per_line": 1000,
    "line_setup_cost": 500_000,
    "line_resale_val": 0.4,
    "rm_cost": {"R1": 100, "R2": 150},
    "labor_cost": {"P1": 60, "P2": 90},
    "base_demand": {"P1": 25000, "P2": 18000},
}

# ==========================================
# 2. 資料庫核心邏輯
# ==========================================
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "season": 1,
            "teacher": {"status": "OPEN", "announcement": "歡迎來到戰情室模式！", "seed": 2025},
            "teams": {},
            "decisions": {}
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
        "fixed_assets": 5_000_000,
        "accumulated_dep": 0,
        "loan": 2_000_000,
        "equity": 11_000_000 + (2000*100 + 2000*150 + 500*160 + 500*240),
        "capacity_lines": 5,
        "rd_level": {"P1": 1, "P2": 1},
        "history": []
    }

# ==========================================
# 3. UI 渲染函式 (Modular UI)
# ==========================================

# --- A. 老師控制面板 (左側) ---
def render_teacher_panel(db, container):
    season = db["season"]
    with container:
        st.info(f"👨‍🏫 老師指揮官｜第 {season} 季", icon="👨‍🏫")
        
        # 1. 遊戲控制
        with st.expander("⚙️ 遊戲控制", expanded=True):
            ann = st.text_area("公告內容", value=db["teacher"]["announcement"], height=70, key="t_ann")
            
            c1, c2 = st.columns(2)
            is_locked = (db["teacher"]["status"] == "LOCKED")
            with c1:
                if st.button("💾 更新設定", key="btn_save_anno"):
                    db["teacher"]["announcement"] = ann
                    save_db(db)
                    st.success("已更新")
            with c2:
                btn_label = "🔓 解鎖提交" if is_locked else "🔒 鎖定提交"
                if st.button(btn_label, key="btn_lock"):
                    db["teacher"]["status"] = "OPEN" if is_locked else "LOCKED"
                    save_db(db)
                    st.rerun()

            st.divider()
            st.markdown("#### 🚀 季度結算")
            st.caption("當所有組別提交後，按下此鈕計算並進入下一季。")
            if st.button(f"執行第 {season} 季結算", type="primary", use_container_width=True, key="btn_run"):
                run_simulation(db)
                st.success("結算完成！")
                time.sleep(1)
                st.rerun()

        # 2. 數據下載
        with st.expander("📥 報表中心"):
            st.button("下載本季 Excel 報表 (Demo)", key="btn_dl_excel", disabled=True, help="連接後端後可啟用")
            
        # 3. 危險區域
        st.divider()
        if st.button("🧨 重置整個遊戲", key="btn_reset_all"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()

# --- B. 學生狀態與畫面 (右側) ---
def render_student_area(db, container):
    season = db["season"]
    decisions = db["decisions"].get(season, {})
    
    with container:
        # --- B1. 全班進度看板 (Progress) ---
        st.warning(f"📊 全班進度監控 (Season {season})", icon="📊")
        
        # 計算進度
        submitted_count = len(decisions)
        total_teams = len(TEAMS_LIST)
        progress = submitted_count / total_teams
        st.progress(progress, text=f"提交進度: {submitted_count}/{total_teams}")
        
        # 進度網格 (更直觀的燈號)
        status_cols = st.columns(5)
        for i, team in enumerate(TEAMS_LIST):
            is_done = team in decisions
            with status_cols[i % 5]:
                if is_done:
                    st.success(f"{team}")
                else:
                    st.caption(f"{team}")
        
        st.divider()

        # --- B2. 單一學生視角 (Student View) ---
        col_sel, col_role = st.columns([2, 1])
        with col_sel:
            target_team = st.selectbox("👁️ 監控/操作視角：", TEAMS_LIST, key="sel_target_team")
        with col_role:
            st.caption("目前模擬角色")
            st.markdown(f"**{target_team}**")

        # 初始化該組資料
        if target_team not in db["teams"]:
            db["teams"][target_team] = init_team_state(target_team)
            save_db(db) # 確保初始化被存檔
            st.rerun()

        state = db["teams"][target_team]
        
        # 渲染該組的決策介面
        st.markdown(f"### 📝 {target_team} 決策面板")
        
        # 鎖定狀態檢查
        if db["teacher"]["status"] == "LOCKED":
            st.error("⛔ 老師已鎖定本季，無法修改。")
            if target_team in decisions:
                st.json(decisions[target_team]) # 顯示已提交內容
            return

        # 顯示簡易財務摘要
        m1, m2, m3 = st.columns(3)
        m1.metric("現金", f"${state['cash']:,.0f}")
        m2.metric("庫存(P1/P2)", f"{state['inventory']['P1']}/{state['inventory']['P2']}")
        m3.metric("貸款", f"${state['loan']:,.0f}")

        # Tab 介面
        tab1, tab2, tab3 = st.tabs(["行銷", "生產", "財務"])
        
        with st.form(key=f"form_{target_team}"):
            # 為了避免 key 衝突，所有 input 都要加上 target_team 前綴
            k = target_team 
            
            with tab1:
                c1, c2 = st.columns(2)
                with c1:
                    d_p1_price = st.number_input("P1 價格", 100, 500, 200, key=f"{k}_p1_p")
                    d_p1_ad = st.number_input("P1 廣告", 0, 1000000, 50000, key=f"{k}_p1_ad")
                with c2:
                    d_p2_price = st.number_input("P2 價格", 200, 800, 350, key=f"{k}_p2_p")
                    d_p2_ad = st.number_input("P2 廣告", 0, 1000000, 50000, key=f"{k}_p2_ad")
            
            with tab2:
                c1, c2 = st.columns(2)
                with c1:
                    d_prod_p1 = st.number_input("P1 生產", 0, 10000, 0, key=f"{k}_p1_prod")
                    d_buy_r1 = st.number_input("R1 採購", 0, 20000, d_prod_p1, key=f"{k}_r1_buy")
                with c2:
                    d_prod_p2 = st.number_input("P2 生產", 0, 10000, 0, key=f"{k}_p2_prod")
                    d_buy_r2 = st.number_input("R2 採購", 0, 20000, d_prod_p2, key=f"{k}_r2_buy")
                
                st.markdown("---")
                c3, c4 = st.columns(2)
                with c3:
                    d_buy_line = st.number_input("買產線", 0, 5, 0, key=f"{k}_buy_l")
                with c4:
                    d_rd_p1 = st.number_input("RD P1", 0, 500000, 0, step=50000, key=f"{k}_rd1")
                    d_rd_p2 = st.number_input("RD P2", 0, 500000, 0, step=50000, key=f"{k}_rd2")
            
            with tab3:
                c1, c2 = st.columns(2)
                d_loan = c1.number_input("借款", 0, 5000000, 0, step=100000, key=f"{k}_loan")
                d_pay = c2.number_input("還款", 0, 5000000, 0, step=100000, key=f"{k}_pay")

            # 預算試算 (Budget Check)
            est_out = (d_prod_p1*60 + d_prod_p2*90) + (d_buy_r1*100 + d_buy_r2*150) + \
                      (d_p1_ad + d_p2_ad + d_rd_p1 + d_rd_p2) + (d_buy_line*500000)
            est_cash = state['cash'] - est_out + d_loan - d_pay
            
            st.caption(f"預估支出: ${est_out:,.0f} | 預估餘額: ${est_cash:,.0f}")
            if est_cash < 0:
                st.error("⚠️ 警告：預估現金不足！")

            if st.form_submit_button("✅ 提交決策", type="primary", use_container_width=True):
                # 儲存決策
                dec_data = {
                    "price": {"P1": d_p1_price, "P2": d_p2_price},
                    "ad": {"P1": d_p1_ad, "P2": d_p2_ad},
                    "production": {"P1": d_prod_p1, "P2": d_prod_p2},
                    "buy_rm": {"R1": d_buy_r1, "R2": d_buy_r2},
                    "rd": {"P1": d_rd_p1, "P2": d_rd_p2},
                    "ops": {"buy_lines": d_buy_line, "sell_lines": 0},
                    "finance": {"loan_add": d_loan, "loan_pay": d_pay},
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                if season not in db["decisions"]: db["decisions"][season] = {}
                db["decisions"][season][target_team] = dec_data
                save_db(db)
                st.success(f"{target_team} 決策已保存！")
                st.rerun()

# ==========================================
# 4. 結算邏輯 (同 V8.0，略做精簡)
# ==========================================
def run_simulation(db):
    season = db["season"]
    decs = db["decisions"].get(season, {})
    
    # 簡易市場分配
    scores_p1 = {}; scores_p2 = {}
    total_s1 = 0; total_s2 = 0
    
    for team in TEAMS_LIST:
        d = decs.get(team, {"price":{"P1":999,"P2":999}, "ad":{"P1":0,"P2":0}, "rd":{"P1":0,"P2":0}})
        s1 = (300/d["price"]["P1"]) * (1 + d["ad"]["P1"]/500000)
        s2 = (450/d["price"]["P2"]) * (1 + d["ad"]["P2"]/500000)
        scores_p1[team] = s1; total_s1 += s1
        scores_p2[team] = s2; total_s2 += s2

    # 結算各組
    for team in TEAMS_LIST:
        if team not in db["teams"]: db["teams"][team] = init_team_state(team)
        state = db["teams"][team]
        d = decs.get(team)
        
        # 若未提交則跳過不做動作 (或可設為 Default)
        if not d: continue 
        
        # 1. 扣料與生產
        prod1 = min(d["production"]["P1"], state["inventory"]["R1"])
        prod2 = min(d["production"]["P2"], state["inventory"]["R2"])
        state["inventory"]["R1"] += (d["buy_rm"]["R1"] - prod1)
        state["inventory"]["R2"] += (d["buy_rm"]["R2"] - prod2)
        state["inventory"]["P1"] += prod1
        state["inventory"]["P2"] += prod2
        
        cost_mfg = prod1*60 + prod2*90
        cost_mat = d["buy_rm"]["R1"]*100 + d["buy_rm"]["R2"]*150
        
        # 2. 銷售
        share1 = scores_p1[team]/total_s1 if total_s1 > 0 else 0
        share2 = scores_p2[team]/total_s2 if total_s2 > 0 else 0
        sale1 = min(int(PARAMS["base_demand"]["P1"] * share1), state["inventory"]["P1"])
        sale2 = min(int(PARAMS["base_demand"]["P2"] * share2), state["inventory"]["P2"])
        state["inventory"]["P1"] -= sale1
        state["inventory"]["P2"] -= sale2
        
        rev = sale1 * d["price"]["P1"] + sale2 * d["price"]["P2"]
        
        # 3. 現金流
        exp_ad = d["ad"]["P1"] + d["ad"]["P2"]
        exp_rd = d["rd"]["P1"] + d["rd"]["P2"]
        capex = d["ops"]["buy_lines"] * 500000
        
        # 現金變動 = 營收 - 材料費 - 加工費 - 廣告 - RD - 建廠 + 貸款 - 還款
        net_cash = rev - cost_mat - cost_mfg - exp_ad - exp_rd - capex + d["finance"]["loan_add"] - d["finance"]["loan_pay"]
        state["cash"] += net_cash
        state["loan"] += (d["finance"]["loan_add"] - d["finance"]["loan_pay"])
        state["capacity_lines"] += d["ops"]["buy_lines"]
        
        # 紀錄歷史
        state["history"].append({"Season": season, "Revenue": rev, "Cash": state["cash"]})
        
    db["season"] += 1
    db["teacher"]["status"] = "OPEN"
    db["decisions"] = {}
    save_db(db)

# ==========================================
# 5. 主程式佈局 (Main Layout)
# ==========================================
def main():
    st.set_page_config(page_title=SYSTEM_NAME, layout="wide", page_icon="🏢")
    st.title(f"🏢 {SYSTEM_NAME}")
    
    db = load_db()
    
    # 使用 container 來分割畫面
    left_col, right_col = st.columns([1, 2], gap="large")
    
    # 渲染左側 (老師)
    render_teacher_panel(db, left_col)
    
    # 渲染右側 (學生/進度)
    render_student_area(db, right_col)

if __name__ == "__main__":
    main()
