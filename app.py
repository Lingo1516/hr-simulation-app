# app.py (最終修正版 - V3)
# 根據用戶建議，增加「撤銷上一回合 (Undo)」功能
# 將「重置」按鈕區分為「撤銷 (Undo)」和「遊戲重置 (Reset)」

import streamlit as st
import copy # 引入 copy 模組，用於深度複製狀態

# --- 1. 遊戲狀態初始化 ---
def init_game_state():
    """返回一個乾淨的初始遊戲狀態字典"""
    return {
        'round': 1,
        'budget': 2000000,
        'morale': 55,       # 員工士氣 (滿分 100)
        'turnover': 20,     # 關鍵人才流動率 (%)
        'readiness': 30,    # 領導力儲備 (滿分 100)
        
        # 用來儲存學生的質化報告
        'rationale_1': '',
        'rationale_2': '',
        'rationale_3': ''
    }

def init_team_data():
    """初始化一個團隊的完整數據，包含'當前狀態'和'歷史紀錄'"""
    return {
        'current': init_game_state(),
        'history': [] # 用一個列表來儲存歷史狀態
    }

# --- 2. 顯示儀表板 (KPIs) ---
def display_dashboard():
    st.header("📈 TechNova 儀表板")
    st.markdown("---")
    
    # 從 session_state 讀取當前團隊的 "current" 數據
    current_state = st.session_state.game_data['current']

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏦 專案預算", f"${current_state['budget']:,.0f}")
    col2.metric("😊 員工士氣", f"{current_state['morale']}/100")
    col3.metric("🚪 人才流動率", f"{current_state['turnover']}%")
    col4.metric("🎓 領導力儲備", f"{current_state['readiness']}/100")
    st.markdown("---")

# --- 3. 處理回合提交的邏輯 ---

def save_history():
    """在處理決策前，儲存當前狀態到歷史紀錄中"""
    current_team_data = st.session_state.game_data
    # 使用 deepcopy 確保儲存的是一個獨立的複本
    current_team_data['history'].append(copy.deepcopy(current_team_data['current']))

# === 第一回合邏輯 ===
def process_round_1(budget_A, budget_B, budget_C, budget_D, rationale):
    save_history() # *** 新增：儲存 R1 開始前的狀態 ***
    current_state = st.session_state.game_data['current']
    
    total_spent = budget_A + budget_B + budget_C + budget_D
    
    if total_spent > current_state['budget']:
        st.error("錯誤：總支出已超過預算！請重新調整。")
        st.session_state.game_data['history'].pop() # 如果出錯，移除剛剛存的歷史
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
    save_history() # *** 新增：儲存 R2 開始前的狀態 ***
    current_state = st.session_state.game_data['current']
    
    if implementation_cost > current_state['budget']:
        st.error("錯誤：導入預算已超過剩餘預算！請重新調整。")
        st.session_state.game_data['history'].pop() # 如果出錯，移除剛剛存的歷史
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
    save_history() # *** 新增：儲存 R3 開始前的狀態 ***
    current_state = st.session_state.game_data['current']

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

# --- 為每個團隊建立獨立的 session_state (*** 結構已修改 ***) ---
if 'teams' not in st.session_state:
    st.session_state.teams = {}

if selected_team not in st.session_state.teams:
    st.session_state.teams[selected_team] = init_team_data() # 使用新的初始化函數

# game_data 現在指向包含 'current' 和 'history' 的完整團隊數據
st.session_state.game_data = st.session_state.teams[selected_team]


# --- 顯示儀表板 ---
display_dashboard()

# --- 遊戲主循環：根據回合顯示不同內容 ---
current_round = st.session_state.game_data['current']['round']

# === 第一回合 ===
if current_round == 1:
    st.header("第一回合：穩住陣腳 - 預算分配")
    st.markdown(f"您的總預算為 **${st.session_state.game_data['current']['budget']:,.0f}**。請分配資源以解決眼前的問題。")
    
    st.subheader("A. 立即加薪計畫")
    st.markdown("效果：快速降低流動率、小幅提升士iq。成本：高。")
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
        
        is_over_budget = (total_spent > st.session_state.game_data['current']['budget'])
        if is_over_budget:
            st.error("錯誤：總支出已超過預算！請重新調整。")

        st.markdown("---")
        st.subheader("【策略報告】")
        rationale_1 = st.text_area("請說明您如此分配預算的『策略依據』是什麼？(500字)", height=150)
        
        submitted_1 = st.form_submit_button("提交第一回合決策", disabled=is_over_budget)

    if submitted_1:
        process_round_1(budget_A, budget_B, budget_C, budget_D, rationale_1)
        st.rerun() 

# === 第二回合 ===
elif current_round == 2:
    st.header("第二回合：績效制度革新")
    st.markdown("第一階段的行動已產生效果。CEO 要求你們在『績效管理』上做出重大抉擇。")
    
    with st.form("round_2_form"):
        policy_choice = st.radio("選擇你的核心績效策略：", 
                                 ["A. 菁英驅動", "B. 全員賦能 (OKR)", "C. 敏捷專案制"])
        st.markdown("""... (說明文字) ...""")
        
        implementation_cost = st.slider("請投入『制度導入預算』(用於顧問、訓練、系統)", 
                                        0, 
                                        st.session_state.game_data['current']['budget'], 
                                        value=0, 
                                        step=25000,
                                        key=f"{selected_team}_r2_cost")
        
        st.markdown("---")
        st.subheader("【策略報告】")
        rationale_2 = st.text_area("說明你選擇此政策的理由...(500字)", height=150)
        
        submitted_2 = st.form_submit_button("提交第二回合決策")
        
    if submitted_2:
        if implementation_cost > st.session_state.game_data['current']['budget']:
             st.error("錯誤：導入預算已超過剩餘預算！請重新調整。")
        else:
            process_round_2(policy_choice, implementation_cost, rationale_2)
            st.rerun()

# === 第三回合 ===
elif current_round == 3:
    st.header("第三回合：危機處理")
    st.error("【緊急事件】你的競爭對手 'CyberCorp' ...")
    st.markdown(f"你只剩下 **${st.session_state.game_data['current']['budget']:,.0f}** 預算。必須立即反應！")
    
    with st.form("round_3_form"):
        crisis_choice = st.radio("選擇你的危機應對策略：", 
                                 ["A. 絕不妥協 (Counter-Offer)", 
                                  "B. 訴諸文化 (Internal PR)", 
                                  "C. 策略性放棄"],
                                 key=f"{selected_team}_r3_choice")
        
        st.markdown("""... (說明文字) ...""")
        st.markdown("---")
        st.subheader("【最終報告】")
        rationale_3 = st.text_area("說明你此決策的考量...(500字)", height=150)
        
        submitted_3 = st.form_submit_button("提交最終決策")
        
    if submitted_3:
        process_round_3(crisis_choice, rationale_3)
        st.rerun()

# === 遊戲結束 ===
elif current_round == 4:
    st.header(f"🏁 競賽結束 - {selected_team} 的最終成績單")
    st.markdown("感謝你們的努力！以下是你們的最終儀表板狀態。請準備口頭報告。")
    
    current_state = st.session_state.game_data['current']
    final_score = (current_state['morale'] * 1.5) + \
                  (current_state['readiness'] * 2) - \
                  (current_state['turnover'] * 3) + \
                  (current_state['budget'] / 10000)
    
    st.subheader(f"綜合策略指數: {int(final_score)}")
    
    st.markdown("---")
    st.subheader("您的策略報告回顧：")
    
    with st.expander("第一回合報告"):
        st.write(current_state['rationale_1'])
    with st.expander("第二回合報告"):
        st.write(current_state['rationale_2'])
    with st.expander("第三回合報告"):
        st.write(current_state['rationale_3'])


# --- 5. 重置按鈕 (*** 這裡已修改 ***) ---
st.sidebar.title("👨‍🏫 管理員面板")

# *** 新增：按鈕 1 - 撤銷上一回合 ***
if st.sidebar.button("🔙 撤銷上一回合 (Undo)"):
    current_team_data = st.session_state.game_data
    if not current_team_data['history']:
        st.sidebar.error("沒有上一步可供撤銷！")
    else:
        # 從 history 列表中 'pop' 出最後一個狀態，並覆蓋 'current'
        previous_state = current_team_data['history'].pop()
        current_team_data['current'] = previous_state
        st.sidebar.success("已恢復至上一回合。")
        st.rerun()

# *** 修改：按鈕 2 - 重置遊戲 ***
if st.sidebar.button(f"♻️ 重置 {selected_team} 的遊戲 (Reset)"):
    # 重置為全新的初始狀態
    st.session_state.teams[selected_team] = init_team_data()
    st.sidebar.success(f"{selected_team} 的進度已重置。")
    st.rerun()

# *** 按鈕 3 - 重置所有 ***
if st.sidebar.button("!!! (重置所有團隊進度) !!!"):
    st.session_state.teams = {}
    st.sidebar.success("所有團隊進度均已重置。")
    st.rerun()
