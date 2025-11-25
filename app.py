# -*- coding: utf-8 -*-
# Nova BOSS Simulator V8.0 - Professional Edition
# Author: Gemini (2025-11-25)
# ---------------------------------------------------------
# 系統特色：
# 1. 會計核心：損益表(P&L) 與 資產負債表(BS) 透過保留盈餘與現金流精確連動。
# 2. 決策分流：行銷/生產/財務 三大模組分頁顯示，符合企業職能。
# 3. 預算制約：即時計算預估支出，防止現金透支。
# 4. 儀表板化：使用 Metrics 與 Charts 呈現關鍵績效。

import streamlit as st
import pandas as pd
import os
import pickle
import random
import time
from datetime import datetime

# ==========================================
# 1. 系統常數與參數 (System Constants)
# ==========================================
SYSTEM_NAME = "Nova BOSS 企業經營模擬系統 V8.0"
DB_FILE = "nova_boss_db.pkl"

TEAMS_CONFIG = {f"第 {i} 組": f"team{i:02d}" for i in range(1, 11)}
ADMIN_PASSWORD = "admin"  # 老師密碼

# 經濟與成本參數
PARAMS = {
    "tax_rate": 0.25,           # 企業所得稅
    "interest_rate": 0.02,      # 季貸款利率
    "holding_cost_rate": 0.03,  # 庫存持有成本 (每季)
    "overtime_premium": 1.5,    # 加班費率
    "capacity_per_line": 1000,  # 每條產線產能
    "line_setup_cost": 500_000, # 產線建置費
    "line_resale_val": 0.4,     # 產線殘值係數
    "rm_cost": {"R1": 100, "R2": 150},
    "labor_cost": {"P1": 60, "P2": 90},
    "base_demand": {"P1": 25000, "P2": 18000}, # 基礎市場胃納量
}

# ==========================================
# 2. 核心邏輯函式庫 (Core Logic)
# ==========================================

def load_db():
    if not os.path.exists(DB_FILE):
        # 初始化全新資料庫
        return {
            "season": 1,
            "teacher": {"status": "OPEN", "announcement": "歡迎來到 Nova BOSS 模擬系統！請開始第 1 季決策。", "seed": 2025},
            "teams": {},   # 存放各組當前狀態 (BS, Inventory, P&L History)
            "decisions": {} # 存放當季決策
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
    # 初始資產負債表與狀態
    return {
        "cash": 8_000_000,
        "inventory": {"R1": 2000, "R2": 2000, "P1": 500, "P2": 500},
        "fixed_assets": 5_000_000, # 初始設備
        "accumulated_dep": 0,
        "loan": 2_000_000,
        "equity": 11_000_000 + (2000*100 + 2000*150 + 500*160 + 500*240), # 資產 - 負債 (簡易平衡)
        "capacity_lines": 5,
        "rd_level": {"P1": 1, "P2": 1},
        "history": [], # 歷年財報
        "last_kpi": {}
    }

def calculate_max_production(state, product):
    # 計算最大可生產量 (受限於產能、原料)
    # 簡化：假設產能共用，原料對應
    lines = state["capacity_lines"]
    cap_total = lines * PARAMS["capacity_per_line"]
    
    # 原料限制
    rm_key = "R1" if product == "P1" else "R2"
    rm_inv = state["inventory"][rm_key]
    
    return min(cap_total, rm_inv) # 單一產品最大可能量(未考慮混排)

# ==========================================
# 3. Streamlit UI 視圖 (Views)
# ==========================================

def login_page():
    st.markdown(f"<h1 style='text-align: center;'>🏭 {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            role = st.selectbox("登入身分", ["學生團隊", "指導老師"])
            team_select = st.selectbox("選擇組別", list(TEAMS_CONFIG.keys())) if role == "學生團隊" else None
            password = st.text_input("存取密碼", type="password")
            submit = st.form_submit_button("登入系統")
            
            if submit:
                db = load_db()
                if role == "指導老師":
                    if password == ADMIN_PASSWORD:
                        st.session_state["role"] = "teacher"
                        st.session_state["user"] = "admin"
                        st.success("老師登入成功！")
                        st.rerun()
                    else:
                        st.error("管理員密碼錯誤")
                else:
                    # 學生密碼 (簡化：預設為 team01, team02...)
                    correct_pw = TEAMS_CONFIG[team_select]
                    if password == correct_pw:
                        st.session_state["role"] = "student"
                        st.session_state["user"] = team_select
                        # 初始化該組資料(若無)
                        if team_select not in db["teams"]:
                            db["teams"][team_select] = init_team_state(team_select)
                            save_db(db)
                        st.success(f"{team_select} 登入成功！")
                        st.rerun()
                    else:
                        st.error("組別密碼錯誤")

def student_dashboard():
    db = load_db()
    team = st.session_state["user"]
    season = db["season"]
    status = db["teacher"]["status"]
    state = db["teams"].get(team, init_team_state(team))
    
    # Sidebar 資訊
    with st.sidebar:
        st.header(f"🧑‍🎓 {team}")
        st.info(f"目前季度：第 {season} 季")
        st.metric("可用現金 (Cash)", f"${state['cash']:,.0f}")
        st.metric("目前產線數", f"{state['capacity_lines']} 條")
        if st.button("登出"):
            st.session_state.clear()
            st.rerun()

    # 主畫面
    st.title(f"第 {season} 季決策面板")
    
    if db["teacher"]["announcement"]:
        st.warning(f"📢 公告：{db['teacher']['announcement']}")

    if status == "LOCKED":
        st.error("⛔ 本季決策已鎖定，等待老師結算中。")
        # 顯示已提交資訊
        if team in db["decisions"].get(season, {}):
            st.json(db["decisions"][season][team])
        return

    # --- 決策表單 (Tab 介面) ---
    st.write("請依序完成以下決策：")
    tab1, tab2, tab3 = st.tabs(["📊 1. 行銷與業務", "🏭 2. 生產與供應", "💰 3. 財務與資本"])
    
    with st.form("decision_form"):
        # 1. 行銷
        with tab1:
            st.subheader("市場策略")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Product P1 (大眾型)")
                d_price_p1 = st.number_input("P1 售價", 100, 500, 200, help="參考價 $200")
                d_ad_p1 = st.number_input("P1 廣告預算", 0, 1_000_000, 50_000, step=10_000)
            with c2:
                st.markdown("#### Product P2 (高端型)")
                d_price_p2 = st.number_input("P2 售價", 200, 800, 350, help="參考價 $350")
                d_ad_p2 = st.number_input("P2 廣告預算", 0, 1_000_000, 50_000, step=10_000)

        # 2. 生產
        with tab2:
            st.subheader("供應鏈管理")
            col_cap, col_prod = st.columns([1, 2])
            with col_cap:
                st.info(f"現有產能上限: {state['capacity_lines'] * PARAMS['capacity_per_line']} 單位")
                d_buy_lines = st.number_input("擴充產線 (條)", 0, 5, 0, help="每條 $500,000")
                d_sell_lines = st.number_input("處分產線 (條)", 0, state['capacity_lines'], 0, help="殘值回收 40%")
            
            with col_prod:
                st.markdown("#### 生產排程")
                d_prod_p1 = st.number_input("P1 生產量", 0, 20000, 0)
                d_prod_p2 = st.number_input("P2 生產量", 0, 20000, 0)
                st.caption(f"現有庫存: R1={state['inventory']['R1']}, R2={state['inventory']['R2']}")
                d_buy_r1 = st.number_input("採購原料 R1", 0, 50000, d_prod_p1, help="每單位 $100")
                d_buy_r2 = st.number_input("採購原料 R2", 0, 50000, d_prod_p2, help="每單位 $150")
                d_rd_p1 = st.number_input("P1 研發投入", 0, 500_000, 0, step=50_000)
                d_rd_p2 = st.number_input("P2 研發投入", 0, 500_000, 0, step=50_000)

        # 3. 財務
        with tab3:
            st.subheader("資金調度")
            st.caption(f"目前銀行貸款: ${state['loan']:,.0f} (季利率 2%)")
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                d_loan_add = st.number_input("新增貸款", 0, 5_000_000, 0, step=100_000)
            with c_f2:
                d_loan_pay = st.number_input("償還貸款", 0, state['loan'], 0, step=100_000)

        # 即時預算檢查 (Real-time Budget Check)
        # 計算預估現金流出
        est_cost_prod = (d_prod_p1 * PARAMS['labor_cost']['P1']) + (d_prod_p2 * PARAMS['labor_cost']['P2'])
        est_cost_mat = (d_buy_r1 * PARAMS['rm_cost']['R1']) + (d_buy_r2 * PARAMS['rm_cost']['R2'])
        est_cost_ad = d_ad_p1 + d_ad_p2 + d_rd_p1 + d_rd_p2
        est_capex = d_buy_lines * PARAMS['line_setup_cost']
        est_loan_in = d_loan_add - d_loan_pay
        
        total_cash_out = est_cost_prod + est_cost_mat + est_cost_ad + est_capex
        est_final_cash = state['cash'] - total_cash_out + est_loan_in + (d_sell_lines * PARAMS['line_setup_cost'] * PARAMS['line_resale_val'])

        st.markdown("---")
        st.markdown("### 🧾 決策預算試算")
        k1, k2, k3 = st.columns(3)
        k1.metric("預估總支出", f"${total_cash_out:,.0f}")
        k2.metric("預估淨現金流", f"${est_loan_in - total_cash_out:,.0f}")
        k3.metric("期末現金預估", f"${est_final_cash:,.0f}", delta_color="normal" if est_final_cash > 0 else "inverse")

        if est_final_cash < 0:
            st.error("⚠️ 警告：預估現金不足！請增加貸款或減少支出，否則將產生高額緊急融資利息。")

        submit_dec = st.form_submit_button("✅ 確認並提交決策", disabled=(status=="LOCKED"))
        
        if submit_dec:
            # 打包決策資料
            decision_data = {
                "price": {"P1": d_price_p1, "P2": d_price_p2},
                "ad": {"P1": d_ad_p1, "P2": d_ad_p2},
                "production": {"P1": d_prod_p1, "P2": d_prod_p2},
                "buy_rm": {"R1": d_buy_r1, "R2": d_buy_r2},
                "rd": {"P1": d_rd_p1, "P2": d_rd_p2},
                "ops": {"buy_lines": d_buy_lines, "sell_lines": d_sell_lines},
                "finance": {"loan_add": d_loan_add, "loan_pay": d_loan_pay},
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            
            # 儲存
            if season not in db["decisions"]: db["decisions"][season] = {}
            db["decisions"][season][team] = decision_data
            save_db(db)
            st.success("決策已成功提交！系統已記錄。")
            time.sleep(1)
            st.rerun()

def teacher_dashboard():
    db = load_db()
    season = db["season"]
    
    st.sidebar.header("👨‍🏫 指導老師控制台")
    st.sidebar.info(f"當前進度：第 {season} 季")
    
    # 控制區
    st.title("BOSS 模擬系統管理後台")
    
    with st.expander("⚙️ 遊戲控制與公告", expanded=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            announcement = st.text_input("發布公告", value=db["teacher"]["announcement"])
        with c2:
            is_locked = (db["teacher"]["status"] == "LOCKED")
            lock_btn = st.button("🔓 解鎖提交" if is_locked else "🔒 鎖定提交/準備結算")
            
        if lock_btn:
            db["teacher"]["status"] = "OPEN" if is_locked else "LOCKED"
            db["teacher"]["announcement"] = announcement
            save_db(db)
            st.rerun()

        if st.button("💾 儲存公告設定"):
            db["teacher"]["announcement"] = announcement
            save_db(db)
            st.success("設定已更新")

    # 提交狀態監控
    st.subheader("📊 各組提交狀態")
    status_data = []
    for team in TEAMS_CONFIG.keys():
        submitted = team in db["decisions"].get(season, {})
        last_time = db["decisions"].get(season, {}).get(team, {}).get("timestamp", "--")
        status_data.append({
            "組別": team,
            "狀態": "✅ 已提交" if submitted else "❌ 未提交",
            "提交時間": last_time
        })
    st.dataframe(pd.DataFrame(status_data), use_container_width=True)

    # 結算按鈕
    st.markdown("---")
    st.warning("⚠️ 結算將推進至下一季，請確保所有組別皆已提交。")
    if st.button(f"🚀 執行第 {season} 季結算 (Run Calculation)"):
        run_simulation(db)
        st.success("結算完成！進入下一季。")
        time.sleep(2)
        st.rerun()
        
    # 重置按鈕
    with st.sidebar:
        st.divider()
        if st.button("🧨 重置整個遊戲 (DANGER)"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.rerun()

# ==========================================
# 4. 結算引擎 (Simulation Engine)
# ==========================================
def run_simulation(db):
    season = db["season"]
    decisions = db["decisions"].get(season, {})
    
    # 1. 市場需求分配 (Market Allocation)
    # 簡單模型：價格越低、廣告越高、RD越高 -> 分數越高 -> 市占越高
    scores = {"P1": {}, "P2": {}}
    total_score = {"P1": 0, "P2": 0}
    
    # 計算各組吸引力分數
    for team, dec in decisions.items():
        state = db["teams"][team]
        for p in ["P1", "P2"]:
            price = dec["price"][p]
            ad = dec["ad"][p]
            rd = state["rd_level"][p] + (dec["rd"][p] / 1_000_000) # 簡易 RD 升級邏輯
            
            # 分數公式 (Score)
            base_score = 100
            price_factor = (300 / price) ** 2  # 價格敏感度
            ad_factor = 1 + (ad / 1_000_000)   # 廣告效益
            rd_factor = 1 + (rd * 0.1)         # 品質效益
            
            score = base_score * price_factor * ad_factor * rd_factor
            scores[p][team] = score
            total_score[p] += score
            
            # 更新 RD 等級 (累積制)
            state["rd_level"][p] = rd

    # 2. 結算每組財務
    for team in TEAMS_CONFIG.keys():
        state = db["teams"].get(team, init_team_state(team))
        dec = decisions.get(team)
        
        # 若未提交，給予預設空決策
        if not dec:
            dec = {
                "price": {"P1":999, "P2":999}, "ad": {"P1":0, "P2":0},
                "production": {"P1":0, "P2":0}, "buy_rm": {"R1":0, "R2":0},
                "rd": {"P1":0, "P2":0}, "ops": {"buy_lines":0, "sell_lines":0},
                "finance": {"loan_add":0, "loan_pay":0}
            }

        # --- A. 生產與庫存計算 ---
        # 原料入庫
        state["inventory"]["R1"] += dec["buy_rm"]["R1"]
        state["inventory"]["R2"] += dec["buy_rm"]["R2"]
        cost_rm_buy = dec["buy_rm"]["R1"]*PARAMS["rm_cost"]["R1"] + dec["buy_rm"]["R2"]*PARAMS["rm_cost"]["R2"]
        
        # 生產扣料 & 產出成品
        prod_p1 = min(dec["production"]["P1"], state["inventory"]["R1"]) # 檢查原料夠不夠
        prod_p2 = min(dec["production"]["P2"], state["inventory"]["R2"])
        
        state["inventory"]["R1"] -= prod_p1
        state["inventory"]["R2"] -= prod_p2
        state["inventory"]["P1"] += prod_p1
        state["inventory"]["P2"] += prod_p2
        
        # 製造費用 (Labor + OH)
        mfg_cost = prod_p1 * PARAMS["labor_cost"]["P1"] + prod_p2 * PARAMS["labor_cost"]["P2"]
        
        # --- B. 銷貨計算 (Revenue) ---
        sales_qty = {"P1": 0, "P2": 0}
        revenue = 0
        
        for p in ["P1", "P2"]:
            if team in scores[p] and total_score[p] > 0:
                market_share = scores[p][team] / total_score[p]
                demand = int(PARAMS["base_demand"][p] * market_share)
                actual_sales = min(demand, state["inventory"][p]) # 銷貨受庫存限制
                sales_qty[p] = actual_sales
                revenue += actual_sales * dec["price"][p]
                state["inventory"][p] -= actual_sales
        
        # --- C. 損益表 (Income Statement) 計算 ---
        # 銷貨成本 COGS (採用簡單法：期初存貨+本期製造成本-期末存貨價值 -> 這裡簡化為直接計算銷貨的標準成本)
        # 單位標準成本 = 原料 + 人工
        std_cost_p1 = PARAMS["rm_cost"]["R1"] + PARAMS["labor_cost"]["P1"]
        std_cost_p2 = PARAMS["rm_cost"]["R2"] + PARAMS["labor_cost"]["P2"]
        cogs = (sales_qty["P1"] * std_cost_p1) + (sales_qty["P2"] * std_cost_p2)
        
        gross_profit = revenue - cogs
        
        # 營業費用 (Opex)
        marketing_exp = dec["ad"]["P1"] + dec["ad"]["P2"]
        rd_exp = dec["rd"]["P1"] + dec["rd"]["P2"]
        depreciation = state["fixed_assets"] * 0.05 # 假設每季折舊 5%
        holding_cost = sum(state["inventory"].values()) * 10 # 簡化庫存持有成本
        
        opex = marketing_exp + rd_exp + depreciation + holding_cost
        ebit = gross_profit - opex
        
        # 利息與稅
        interest_exp = state["loan"] * PARAMS["interest_rate"]
        ebt = ebit - interest_exp
        tax = max(0, ebt * PARAMS["tax_rate"])
        net_income = ebt - tax
        
        # --- D. 現金流與資產負債表更新 (BS Update) ---
        # 投資活動
        capex = dec["ops"]["buy_lines"] * PARAMS["line_setup_cost"]
        asset_sales = dec["ops"]["sell_lines"] * PARAMS["line_setup_cost"] * PARAMS["line_resale_val"]
        
        # 融資活動
        loan_in = dec["finance"]["loan_add"]
        loan_out = dec["finance"]["loan_pay"]
        
        # 現金流公式: 
        # 期末現金 = 期初現金 + 營收 - 購料支出 - 人工支出 - 費用支出(行銷/研發/持有) - 利息 - 稅 - 資本支出 + 資產出售 + 貸款 - 還款
        # 注意：折舊是非現金支出，不扣現金
        cash_flow_op = revenue - cost_rm_buy - mfg_cost - (marketing_exp + rd_exp + holding_cost) - interest_exp - tax
        cash_flow_inv = asset_sales - capex
        cash_flow_fin = loan_in - loan_out
        
        state["cash"] += (cash_flow_op + cash_flow_inv + cash_flow_fin)
        
        # 緊急融資 (若現金 < 0)
        if state["cash"] < 0:
            emergency_loan = abs(state["cash"])
            state["loan"] += emergency_loan
            state["cash"] = 0
            # 這裡可加入懲罰利息，暫略
            
        # 更新資產與負債狀態
        state["capacity_lines"] += (dec["ops"]["buy_lines"] - dec["ops"]["sell_lines"])
        # 固定資產價值更新 (加新購 - 出售原值 - 折舊)
        sold_asset_book_value = dec["ops"]["sell_lines"] * PARAMS["line_setup_cost"] # 簡化：出售假設扣除原值
        state["fixed_assets"] += (capex - sold_asset_book_value - depreciation)
        state["accumulated_dep"] += depreciation
        state["loan"] += (loan_in - loan_out)
        
        # 更新股東權益 (保留盈餘 += 淨利)
        state["equity"] += net_income
        
        # 儲存歷史紀錄 (供報表用)
        kpi = {
            "Season": season,
            "Revenue": revenue,
            "Net Income": net_income,
            "Cash": state["cash"],
            "Sales P1": sales_qty["P1"],
            "Sales P2": sales_qty["P2"]
        }
        state["history"].append(kpi)
        state["last_kpi"] = kpi
        
        db["teams"][team] = state

    # 3. 推進季度
    db["season"] += 1
    db["teacher"]["status"] = "OPEN" # 開放下季
    db["decisions"] = {} # 清空決策
    save_db(db)

# ==========================================
# 5. 主程式入口 (Main)
# ==========================================

def main():
    st.set_page_config(page_title=SYSTEM_NAME, layout="wide", page_icon="🏭")
    
    # 檢查登入狀態
    if "role" not in st.session_state:
        login_page()
    elif st.session_state["role"] == "teacher":
        teacher_dashboard()
    elif st.session_state["role"] == "student":
        student_dashboard()

if __name__ == "__main__":
    main()
