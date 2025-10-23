# app.py (已修正版本 3 - 解決 Round 2 slider 崩潰問題)
# 執行方式: streamlit run app.py

import streamlit as st

# --- 1. 遊戲狀態初始化 ---
def init_game_state():
    return {
        'round': 1,
        'budget': 2000000,
        'morale': 55,       # 員工士氣 (滿分 100)
        'turnover': 20,     # 關鍵人才流動率 (%)
        'readiness': 30,    # 領導力儲備 (滿分 100)
        'rationale_1': '',
        'rationale_2': '',
        'rationale_3': ''
    }

# --- 2. 顯示儀表板 (KPIs) ---
def display_dashboard():
    st.header("📈 TechNova 儀表板")
    st.markdown("---")
    current_state = st.session_state.game_data
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏦 專案預算", f"${current_state['budget']:,.0f}")
    col2.metric("😊 員工士氣", f"{current_state['morale']}/100")
    col3.metric("🚪 人才流動率", f"{current_state['turnover']}%")
    col4.metric("🎓 領導力儲備", f"{current_state['readiness']}/100")
    st.markdown("---")

# --- 3. 處理回合提交的邏輯 ---

# === 第一回合邏輯 ===
def process_round_1(budget_A, budget_B, budget_C, budget_D, rationale):
    current_state = st.session_state.game_data
    total_spent = budget_A + budget_B + budget_C + budget_D
    
    if total_spent > current_state['budget']:
        st.error("錯誤：總支出已超過預算！請重新調整。")
        return 

    current_state['budget'] -= total_spent
    
    if budget_A > 0:
        current_state['turnover'] -= budget_A / 100000
        current_state['morale'] += (budget_A / 100000) * 0.5
    if budget_B > 0:
        current_state['readiness'] += budget_B / 50000
    if budget_C > 0:
        current_state['morale'] += budget_C / 40000
    if budget_D > 0:
        current_state['readiness'] += budget_D / 100000
        current_state['morale'] += budget_D / 50000
        
    current_state['rationale_1'] = rationale
    current_state['round'] = 2
    
    current_state['turnover'] = max(0, round(current_state['turnover'], 1))
    current_state['morale'] = min(100, int(current_state['morale']))
    current_state['readiness'] = min(100, int(current_state['readiness']))
    
    st.success("第一回合決策已提交！儀表板已更新。")
    st.balloons()


# === 第二回合邏輯 ===
def process_round_2(policy_choice, implementation_cost, rationale):
    current_state = st.session_state.game_data
    
    if implementation_cost > current_state['budget']:
        st.error("錯誤：導入預算已超過剩餘預算！請重新調整。")
        return

    current_state['budget'] -= implementation_cost
    impact = implementation_cost / 100000 

    if policy_choice == "A. 菁英驅動":
        current_state['turnover'] = max(0, current_state['turnover'] - (2 * impact))
        current_state['morale'] = max(0, current_state['morale'] - (5 * impact))
        current_state['readiness'] += (3 * impact)
    elif policy_choice == "B. 全員賦能 (OKR)":
        current_state['morale'] += (5 * impact)
        current_state['readiness'] += (4 * impact)
        current_state['turnover'] = max(0, current_state['turnover'] - (1 * impact))
    elif policy_choice == "C. 敏捷專案制":
        current_state['morale'] += (3 * impact)
        current_state['readiness'] += (3 * impact)
        current_state['turnover'] += (1 * impact)

    current_state['rationale_2'] = rationale
    current_state['round'] = 3
    
    current_state['turnover'] = max(0, round(current_state['turnover'], 1))
    current_state['morale'] = min(100, int(current_state['morale']))
    current_state['readiness'] = min(100, int(current_state['readiness']))
    
    st.success("第二回合決策已提交！儀表板已更新。")


# === 第三回合邏輯 ===
def process_round_3(crisis_choice, rationale):
    current_state = st.session_state.game_data

    if crisis_choice == "A. 絕不妥協 (Counter-Offer)":
        cost = current_state['budget'] * 0.5 
        current_state['budget'] -= int(cost)
        current_state['turnover'] = max(0, current_state['turnover'] - 5)
        current_state['morale'] = max(0, current_state['morale'] - 10)
    elif crisis_choice == "B. 訴諸文化 (Internal PR)":
        current_state['turnover'] += 3
        current_state['morale'] += 5
    elif crisis_choice == "C. 策略性放棄":
        current_state['turnover'] += 10
        current_state['readiness'] = max(0, current_state['readiness'] - 15)
        current_state['budget'] = int(current_state['budget'] * 0.2) 
        
    current_state['rationale_3'] = rationale
    current_state['round'] = 4
    
    current_state['turnover'] = max(0, round(current_state['turnover'], 1))
    current_state['morale'] = min(100, int(current_state['morale']))
    current_state['readiness'] = min(100, int(current_state['readiness']))
    
    st.success("最終決策已提交！競賽結束！")
    st.balloons()


# --- 4. 主應用程式 (Main App) ---
st.set_page_config(layout="wide")
st.title("🚀 TechNova 擴張挑戰賽 (策略性HR模擬器)")
st.write("您是 TechNova 的人資策略團隊，請在三回合內，運用有限預算，達成公司擴張目標！")

# --- 團隊選擇 ---
team_list = [f"第 {i} 組" for i in range(1, 11)]
selected_team = st.selectbox("請選擇您的隊伍：", team_list)

# --- 為每個團隊建立獨立的 session_state ---
if 'teams' not in st.session_state:
    st.session_state.teams = {}

if selected_team not in st.session_state.teams:
    st.session_state.teams[selected_team] = init_game_state()

st.session_state.game_data = st.session_state.teams[selected_team]


# --- 顯示儀表板 ---
display_dashboard()

# --- 遊戲主循環：根據回合顯示不同內容 ---
current_round = st.session_state.game_data['round']
current_budget = st.session_state.game_data['budget'] # 取得當前預算

# === 第一回合 ===
if current_round == 1:
    st.header("第一回合：穩住陣腳 - 預算分配")
    st.markdown(f"您的總預算為 **${current_budget:,.0f}**。請分配資源以解決眼前的問題。")
    
    st.subheader("A. 立即加薪計畫")
    st.markdown("效果：快速降低流動率、小幅提升士氣。成本：高。")
    budget_A = st.slider("A 預算", 0, 2000000, value=0, step=50000, key=f"{selected_team}_r1_a")

    st.subheader("B. 外部主管培訓")
    st.markdown("效果：解決領導力斷層，但見效慢。成本：中。")
    budget_B = st.slider("B 預算", 0, 2000000, value=0, step=50000, key=f"{selected_team}_r1_b")

    st.subheader("C. 改善辦公環境與福利")
    st.markdown("效果：顯著提升士氣。成本：中。")
    budget_C = st.slider("C 預算", 0, 2000000, value=0, step=50000, key=f"{selected_team}_r1_c")
    
    st.subheader("D. 建立內部導師制度")
    st.markdown("效果：長期提升領導力與士氣。成本：低。")
    budget_D = st.slider("D 預算", 0, 2000000, value=0, step=50000, key=f"{selected_team}_r1_d")
    
    total_spent = budget_A + budget_B + budget_C + budget_D
    
    with st.form("round_1_form"):
        st.subheader("---")
        st.metric("本回合總支出", f"${total_spent:,.0f}")
        
        is_over_budget = (total_spent > current_budget)
        if is_over_budget:
            st.error("錯誤：總支出已超過預算！請重新調整。")

        st.markdown("---")
        st.subheader("【策略報告】")
        rationale_1 = st.text_area("請說明您如此分配預算的『策略依據』是什麼？(500字)", height=150)
        
        submitted_1 = st.form_submit_button("提交第一回合決策", disabled=is_over_budget)

    if submitted_1:
        process_round_1(budget_A, budget_B, budget_C, budget_D, rationale_1)
        st.rerun() 

# === 第二回合 (*** 這裡已修正 ***) ===
elif current_round == 2:
    st.header("第二回合：績效制度革新")
    st.markdown("第一階段的行動已產生效果。CEO 要求你們在『績效管理』上做出重大抉擇。")
    
    with st.form("round_2_form"):
        policy_choice = st.radio("選擇你的核心績效策略：", 
                                 ["A. 菁英驅動", "B. 全員賦能 (OKR)", "C. 敏捷專案制"])
        
        st.markdown("""
        * **A. 菁英驅動：** 強制排名 (Rank & Yank)。高額獎勵 A 級，淘汰 C 級。(效果：領導力提升、流動率降低，但士氣重創)
        * **B. 全員賦能 (OKR)：** 強調輔導和持續反饋。(效果：士氣、領導力提升，流動率小幅下降)
        * **C. 敏捷專案制：** 以團隊為單位評估。(效果：士氣、領導力提升，但初期混亂導致流動率微升)
        """)
        
        st.markdown("---")
        
        # --- BUG FIX START ---
        # 檢查預算是否足夠
        step_r2 = 25000
        if current_budget < step_r2:
            st.warning(f"您的剩餘預算 (${current_budget:,.0f}) 不足 {step_r2:,.0f}，無法投入制度導入預算。")
            implementation_cost = 0 # 自動設為 0
        else:
            # 預算充足，正常顯示滑桿
            implementation_cost = st.slider("請投入『制度導入預算』(用於顧問、訓練、系統)", 
                                            0, 
                                            current_budget, 
                                            value=0, 
                                            step=step_r2)
        # --- BUG FIX END ---
            
        st.markdown("---")
        st.subheader("【策略報告】")
        rationale_2 = st.text_area("說明你選擇此政策的理由，以及它如何支持公司『擴張』的總體目標。(500字)", height=150)
        
        submitted_2 = st.form_submit_button("提交第二回合決策")
        
    if submitted_2:
        # 這裡的檢查依然有效
        if implementation_cost > current_budget:
             st.error("錯誤：導入預算已超過剩餘預算！請重新調整。")
        else:
            process_round_2(policy_choice, implementation_cost, rationale_2)
            st.rerun()

# === 第三回合 ===
elif current_round == 3:
    st.header("第三回合：危機處理")
    st.error("【緊急事件】你的競爭對手 'CyberCorp' 宣布在同城市設立研發中心，並開始高薪挖角你的 10 名核心 AI 工程師！他們士氣低落，正在考慮跳槽。")
    st.markdown(f"你只剩下 **${current_budget:,.0f}** 預算。必須立即反應！")
    
    with st.form("round_3_form"):
        crisis_choice = st.radio("選擇你的危機應對策略：", 
                                 ["A. 絕不妥協 (Counter-Offer)", 
                                  "B. 訴諸文化 (Internal PR)", 
                                  "C. 策略性放棄"])
        
        st.markdown("""
        * **A. S絕不妥協：** 動用剩餘預算的 50% 作為「緊急留才獎金」。(效果：留住人才，但花費巨大且重傷其他員工士氣)
        * **B. 訴諸文化：** CEO 出面強調願景和 IPO 潛力。(效果：不花錢，但可能還是會走 30% 的人，留下的更團結)
        * **C. 策略性放棄：** 讓他們走。將 80% 剩餘預算投入「緊急招聘」。(效果：10 人全走，領導力大失血，但加速補充新血)
        """)

        st.markdown("---")
        st.subheader("【最終報告】")
        rationale_3 = st.text_area("說明你此決策的考量，以及你預期此舉對公司造成的『短期』與『長期』影響。(500字)", height=150)
        
        submitted_3 = st.form_submit_button("提交最終決策")
        
    if submitted_3:
        process_round_3(crisis_choice, rationale_3)
        st.rerun()

# === 遊戲結束 ===
elif current_round == 4:
    st.header(f"🏁 競賽結束 - {selected_team} 的最終成績單")
    st.markdown("感謝你們的努力！以下是你們的最終儀表板狀態。請準備口頭報告。")
    
    final_score = (st.session_state.game_data['morale'] * 1.5) + \
                  (st.session_state.game_data['readiness'] * 2) - \
                  (st.session_state.game_data['turnover'] * 3) + \
                  (st.session_state.game_data['budget'] / 10000)
    
    st.subheader(f"綜合策略指數: {int(final_score)}")
    
    st.markdown("---")
    st.subheader("您的策略報告回顧：")
    
    with st.expander("第一回合報告"):
        st.write(st.session_state.game_data['rationale_1'])
    with st.expander("第二回合報告"):
        st.write(st.session_state.game_data['rationale_2'])
    with st.expander("第三回合報告"):
        st.write(st.session_state.game_data['rationale_3'])


# --- 5. 重置按鈕 (方便測試) ---
st.sidebar.title("管理員面板")
if st.sidebar.button(f"重置 {selected_team} 的進度"):
    st.session_state.teams[selected_team] = init_game_state()
    st.rerun()

if st.sidebar.button("!!! 重置所有團隊進度 !!!"):
    st.session_state.teams = {}
    st.rerun()
