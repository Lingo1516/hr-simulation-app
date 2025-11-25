# ==========================================
# 3. UI 渲染函式 (V9.5 升級版 - 含監控與防呆)
# ==========================================

# --- 輔助：計算風險狀態 ---
def analyze_team_risk(db, team):
    season = db["season"]
    state = db["teams"].get(team, init_team_state(team))
    dec = db["decisions"].get(season, {}).get(team)
    
    # 預設狀態 (若未提交)
    risk_status = {"cash": "❓", "stock": "❓", "msg": "尚未提交"}
    if not dec:
        return risk_status

    # 1. 現金流預測
    est_out = (dec["production"]["P1"]*60 + dec["production"]["P2"]*90) + \
              (dec["buy_rm"]["R1"]*100 + dec["buy_rm"]["R2"]*150) + \
              (dec["ad"]["P1"] + dec["ad"]["P2"] + dec["rd"]["P1"] + dec["rd"]["P2"]) + \
              (dec["ops"]["buy_lines"]*500000)
    est_cash = state['cash'] - est_out + dec["finance"]["loan_add"] - dec["finance"]["loan_pay"]
    
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
    elif avail_p1 < 5000 or avail_p2 < 3000:
        risk_status["stock"] = "🟡 偏低"
    else:
        risk_status["stock"] = "🟢 充足"
        
    risk_status["msg"] = f"預估現金 ${est_cash/10000:.0f}萬"
    return risk_status

# --- A. 老師控制面板 (升級版) ---
def render_teacher_panel(db, container):
    season = db["season"]
    with container:
        st.info(f"👨‍🏫 戰情監控室｜第 {season} 季", icon="📡")
        
        # 1. 全班風險雷達 (Risk Radar) - 老師最愛的功能
        with st.expander("🚨 全班風險監控 (Risk Radar)", expanded=True):
            st.caption("即時掃描各組已提交的決策，判斷是否會出包。")
            
            risk_data = []
            for team in TEAMS_LIST:
                status = analyze_team_risk(db, team)
                submitted = team in db["decisions"].get(season, {})
                risk_data.append({
                    "組別": team,
                    "提交": "✅" if submitted else "❌",
                    "現金預警": status["cash"],
                    "庫存預警": status["stock"],
                    "摘要": status["msg"] if submitted else "等待中..."
                })
            
            df_risk = pd.DataFrame(risk_data)
            st.dataframe(df_risk, use_container_width=True, hide_index=True)
            
            # 快速統計
            not_sub = len([x for x in risk_data if x["提交"] == "❌"])
            if not_sub > 0:
                st.warning(f"還有 {not_sub} 組尚未提交！")
            else:
                st.success("全員已提交，隨時可結算！")

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
                if st.button("🚀 結算", type="primary", use_container_width=True, key="btn_run", disabled=(not_sub > 0)):
                    run_simulation(db)
                    st.success("結算完成！")
                    time.sleep(1)
                    st.rerun()
        
        # 3. 重置
        if st.button("🧨 重置系統", key="btn_reset_all"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()

# --- B. 學生狀態與畫面 (升級版) ---
def render_student_area(db, container):
    season = db["season"]
    
    with container:
        # 標題區
        col_header, col_progress = st.columns([1, 2])
        with col_header:
            st.header(f"學生端模擬")
        with col_progress:
            # 進度條
            done_cnt = len(db["decisions"].get(season, {}))
            st.progress(done_cnt/len(TEAMS_LIST), text=f"本季進度: {done_cnt}/{len(TEAMS_LIST)}")

        # 監控/操作視角選擇
        target_team = st.selectbox("👁️ 選擇要查看/操作的組別：", TEAMS_LIST, key="sel_target_team")
        
        # 初始化與讀取狀態
        if target_team not in db["teams"]:
            db["teams"][target_team] = init_team_state(target_team)
            save_db(db); st.rerun()
        state = db["teams"][target_team]
        
        # --- 學生操作區 ---
        st.markdown(f"#### 📝 {target_team} 決策面板")
        
        if db["teacher"]["status"] == "LOCKED":
            st.error("⛔ 本季已鎖定，等待結算中。")
            if target_team in db["decisions"].get(season, {}):
                st.info(f"已提交內容：{db['decisions'][season][target_team]}")
            return

        # 資源儀表板
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("現金", f"${state['cash']:,.0f}")
        m2.metric("原料 R1/R2", f"{state['inventory']['R1']} / {state['inventory']['R2']}")
        m3.metric("成品 P1/P2", f"{state['inventory']['P1']} / {state['inventory']['P2']}")
        m4.metric("產線數", state['capacity_lines'])

        with st.form(key=f"form_{target_team}"):
            k = target_team 
            
            # 分頁
            t1, t2, t3 = st.tabs(["行銷 (Marketing)", "生產 (Production)", "財務 (Finance)"])
            
            with t1:
                c1, c2 = st.columns(2)
                d_p1_p = c1.number_input("P1 價格", 100, 500, 200, key=f"{k}_p1p")
                d_p1_ad = c1.number_input("P1 廣告", 0, 1000000, 50000, key=f"{k}_p1ad")
                d_p2_p = c2.number_input("P2 價格", 200, 800, 350, key=f"{k}_p2p")
                d_p2_ad = c2.number_input("P2 廣告", 0, 1000000, 50000, key=f"{k}_p2ad")

            with t2:
                # 生產防呆邏輯
                st.caption("注意：生產量不可超過原料庫存，也不可超過產能上限。")
                max_cap = state['capacity_lines'] * 1000
                
                c1, c2 = st.columns(2)
                with c1:
                    max_p1 = min(max_cap, state['inventory']['R1'])
                    d_prod_p1 = st.number_input(f"P1 生產 (Max: {max_p1})", 0, 20000, 0, key=f"{k}_pp1")
                    # 即時警告
                    if d_prod_p1 > state['inventory']['R1']:
                        st.error(f"❌ 原料 R1 不足！現有 {state['inventory']['R1']}，無法生產 {d_prod_p1}")
                    
                    d_buy_r1 = st.number_input("R1 採購", 0, 50000, d_prod_p1, key=f"{k}_br1")

                with c2:
                    max_p2 = min(max_cap, state['inventory']['R2'])
                    d_prod_p2 = st.number_input(f"P2 生產 (Max: {max_p2})", 0, 20000, 0, key=f"{k}_pp2")
                    if d_prod_p2 > state['inventory']['R2']:
                        st.error(f"❌ 原料 R2 不足！現有 {state['inventory']['R2']}，無法生產 {d_prod_p2}")

                    d_buy_r2 = st.number_input("R2 採購", 0, 50000, d_prod_p2, key=f"{k}_br2")
                
                st.markdown("---")
                c3, c4 = st.columns(2)
                d_buy_line = c3.number_input("購買產線", 0, 5, 0, key=f"{k}_bl")
                d_rd_p1 = c4.number_input("RD P1", 0, 500000, 0, step=50000, key=f"{k}_rd1")
                d_rd_p2 = c4.number_input("RD P2", 0, 500000, 0, step=50000, key=f"{k}_rd2")

            with t3:
                c1, c2 = st.columns(2)
                d_loan = c1.number_input("借款", 0, 5000000, 0, step=100000, key=f"{k}_loan")
                d_pay = c2.number_input("還款", 0, 5000000, 0, step=100000, key=f"{k}_pay")

            # 總體檢查
            has_error = (d_prod_p1 > state['inventory']['R1']) or (d_prod_p2 > state['inventory']['R2'])
            
            # 預算試算
            est_out = (d_prod_p1*60 + d_prod_p2*90) + (d_buy_r1*100 + d_buy_r2*150) + \
                      (d_p1_ad + d_p2_ad + d_rd_p1 + d_rd_p2) + (d_buy_line*500000)
            est_cash = state['cash'] - est_out + d_loan - d_pay

            st.markdown("### 🧾 預算檢查")
            if est_cash < 0:
                st.error(f"⚠️ 現金赤字警告！預估餘額：${est_cash:,.0f}。請增加借款或減少支出。")
            else:
                st.success(f"✅ 資金充裕。預估餘額：${est_cash:,.0f}")

            # 提交按鈕
            btn_submit = st.form_submit_button("提交決策", type="primary", use_container_width=True, disabled=has_error)
            
            if btn_submit:
                dec_data = {
                    "price": {"P1": d_p1_p, "P2": d_p2_p},
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
                st.success("已提交！")
                time.sleep(0.5)
                st.rerun()
