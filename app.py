# ==========================================
# 6. UI 渲染：學生操作區 (V9.6 智能提示版)
# ==========================================
def render_student_area(db, container):
    season = db["season"]
    with container:
        # --- 標題與進度 ---
        c_head, c_prog = st.columns([1, 2])
        with c_head:
            st.header("學生端模擬")
        with c_prog:
            done_cnt = len(db["decisions"].get(season, {}))
            st.progress(done_cnt/len(TEAMS_LIST), text=f"本季進度: {done_cnt}/{len(TEAMS_LIST)}")

        # --- 視角選擇 ---
        target_team = st.selectbox("👁️ 選擇操作組別 (God Mode)：", TEAMS_LIST, key="sel_target_team")
        
        # 初始化
        if target_team not in db["teams"]:
            db["teams"][target_team] = init_team_state(target_team)
            save_db(db); st.rerun()
        state = db["teams"][target_team]
        
        # --- 市場情報看板 (同 V9.5) ---
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

        with st.expander("📊 市場行情快報 (Market Intelligence)", expanded=True):
            st.info(f"💡 P1 行情: {ref_p1_msg} | 💡 P2 行情: {ref_p2_msg}")

        # --- 資源儀表板 ---
        st.markdown(f"#### 📝 {target_team} 決策面板")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("現金水位", f"${state['cash']:,.0f}")
        m2.metric("原料庫存 (R1/R2)", f"{state['inventory']['R1']} / {state['inventory']['R2']}")
        m3.metric("成品庫存 (P1/P2)", f"{state['inventory']['P1']} / {state['inventory']['P2']}")
        m4.metric("產線數", f"{state['capacity_lines']} 條")

        if db["teacher"]["status"] == "LOCKED":
            st.error("⛔ 本季已鎖定，等待老師結算。"); return

        # --- 決策表單 (Tab) ---
        with st.form(key=f"form_{target_team}"):
            k = target_team
            t1, t2, t3 = st.tabs(["1. 行銷 (Marketing)", "2. 生產 (Production)", "3. 財務 (Finance)"])
            
            # === Tab 1: 行銷決策 ===
            with t1:
                st.markdown("##### 🎯 價格與推廣策略")
                c1, c2 = st.columns(2)
                
                # P1 區塊
                with c1:
                    st.markdown("**產品 P1 (大眾型)**")
                    d_p1_p = st.number_input(
                        "P1 價格", 100, 500, PARAMS['price_ref']['P1'], key=f"{k}_p1p",
                        help="【定價策略】\n影響：價格越低，銷量越高。\n注意：P1 為價格敏感商品，高於市場行情會導致訂單大幅流失。"
                    )
                    d_p1_ad = st.number_input(
                        "P1 廣告預算", 0, 2000000, 50000, step=10000, key=f"{k}_p1ad",
                        help="【廣告策略】\n影響：增加產品曝光度與吸引力。\n注意：費用為當季全額支出，若無庫存可賣，廣告費將付諸流水。"
                    )
                    st.caption(f"ℹ️ P1 預估毛利空間: ${d_p1_p - 160} / 個 (未扣行銷)")

                # P2 區塊
                with c2:
                    st.markdown("**產品 P2 (高端型)**")
                    d_p2_p = st.number_input(
                        "P2 價格", 200, 800, PARAMS['price_ref']['P2'], key=f"{k}_p2p",
                        help="【定價策略】\n影響：價格彈性較低，客戶較重視品質。\n注意：可嘗試維持高價以獲取較高毛利。"
                    )
                    d_p2_ad = st.number_input(
                        "P2 廣告預算", 0, 2000000, 50000, step=10000, key=f"{k}_p2ad",
                        help="【廣告策略】\n注意：高端客戶受廣告與品牌形象影響較深，建議適度投入。"
                    )
                    st.caption(f"ℹ️ P2 預估毛利空間: ${d_p2_p - 240} / 個 (未扣行銷)")

            # === Tab 2: 生產決策 ===
            with t2:
                st.markdown("##### 🏭 生產排程與供應鏈")
                
                # 動態計算剩餘產能
                current_cap = state['capacity_lines'] * 1000
                st.info(f"🏭 工廠總產能上限： **{current_cap:,}** 單位 (P1 + P2 共用)")
                
                c1, c2 = st.columns(2)
                
                with c1:
                    st.markdown("**P1 生產線**")
                    # 計算 P1 上限
                    max_p1 = min(current_cap, state['inventory']['R1'])
                    
                    d_prod_p1 = st.number_input(
                        f"P1 生產量", 0, 20000, 0, key=f"{k}_pp1",
                        help=f"【生產限制】\n1. 不可超過原料 R1庫存 ({state['inventory']['R1']})\n2. 不可超過總產能 ({current_cap})"
                    )
                    # 即時成本計算
                    p1_cost = d_prod_p1 * 60
                    st.caption(f"💸 預估加工費: ${p1_cost:,}")
                    
                    if d_prod_p1 > state['inventory']['R1']:
                        st.error(f"❌ 原料不足！庫存僅 {state['inventory']['R1']}")
                    
                    d_buy_r1 = st.number_input(
                        "R1 原料採購", 0, 50000, d_prod_p1, key=f"{k}_br1",
                        help="【採購】\n單價 $100。\n注意：本季採購之原料，本季即可投入生產。"
                    )
                    st.caption(f"🚚 預估採購費: ${d_buy_r1 * 100:,}")

                with c2:
                    st.markdown("**P2 生產線**")
                    # 計算 P2 上限 (需考慮 P1 已經用掉的產能嗎？簡單版先各別提示)
                    remaining_cap_for_display = max(0, current_cap - d_prod_p1)
                    
                    d_prod_p2 = st.number_input(
                        f"P2 生產量", 0, 20000, 0, key=f"{k}_pp2",
                        help=f"【生產限制】\n1. 不可超過原料 R2庫存 ({state['inventory']['R2']})\n2. 需與 P1 共用產能。"
                    )
                    p2_cost = d_prod_p2 * 90
                    st.caption(f"💸 預估加工費: ${p2_cost:,}")
                    
                    if d_prod_p2 > state['inventory']['R2']:
                        st.error(f"❌ 原料不足！庫存僅 {state['inventory']['R2']}")
                    
                    # 總產能超標警告
                    if (d_prod_p1 + d_prod_p2) > current_cap:
                        st.error(f"❌ 產能超載！總需求 {d_prod_p1+d_prod_p2} > 上限 {current_cap}")

                    d_buy_r2 = st.number_input(
                        "R2 原料採購", 0, 50000, d_prod_p2, key=f"{k}_br2",
                        help="【採購】\n單價 $150。\n注意：本季採購之原料，本季即可投入生產。"
                    )
                    st.caption(f"🚚 預估採購費: ${d_buy_r2 * 150:,}")

                st.divider()
                c3, c4 = st.columns(2)
                d_buy_line = c3.number_input(
                    "購買新生產線", 0, 5, 0, key=f"{k}_bl",
                    help="【資本支出】\n單價 $500,000。\n注意：本季購買，下季才能開始生產 (建置期 1 季)。"
                )
                
                # RD 區塊
                d_rd_p1 = c4.number_input("RD P1 投入", 0, 500000, 0, step=50000, key=f"{k}_rd1", help="每投入資金可提升下季產品吸引力。")
                d_rd_p2 = c4.number_input("RD P2 投入", 0, 500000, 0, step=50000, key=f"{k}_rd2", help="每投入資金可提升下季產品吸引力。")

            # === Tab 3: 財務決策 ===
            with t3:
                st.markdown("##### 💰 資金調度")
                st.info(f"目前的銀行貸款總額： **${state['loan']:,}** (季利率 2%)")
                
                c1, c2 = st.columns(2)
                d_loan = c1.number_input(
                    "新增借款 (+)", 0, 5000000, 0, step=100000, key=f"{k}_loan",
                    help="【融資】\n增加手頭現金，避免破產。\n代價：會增加未來的利息支出。"
                )
                d_pay = c2.number_input(
                    "償還貸款 (-)", 0, 5000000, 0, step=100000, key=f"{k}_pay",
                    help="【還款】\n減少負債與利息支出。\n注意：請確保償還後現金仍為正數。"
                )

            # === 預算試算與防呆檢查 ===
            cost_prod = (d_prod_p1 * 60) + (d_prod_p2 * 90)
            cost_mat  = (d_buy_r1 * 100) + (d_buy_r2 * 150)
            cost_exp  = d_p1_ad + d_p2_ad + d_rd_p1 + d_rd_p2
            cost_capex = d_buy_line * 500_000
            total_out = cost_prod + cost_mat + cost_exp + cost_capex
            
            est_cash = state['cash'] - total_out + d_loan - d_pay
            
            # 錯誤旗標
            err_p1 = d_prod_p1 > state['inventory']['R1']
            err_p2 = d_prod_p2 > state['inventory']['R2']
            err_cap = (d_prod_p1 + d_prod_p2) > current_cap
            has_error = err_p1 or err_p2 or err_cap
            
            st.markdown("---")
            st.markdown(f"**🧾 本季預算試算** (總支出: ${total_out:,.0f})")
            
            if est_cash < 0:
                st.error(f"⚠️ **現金赤字警告！** 預估餘額 **${est_cash:,.0f}** \n請增加借款或刪減非必要支出 (廣告/擴廠)，否則將觸發高利貸懲罰。")
            else:
                st.success(f"✅ **資金充裕**。預估期末餘額 **${est_cash:,.0f}**")

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
