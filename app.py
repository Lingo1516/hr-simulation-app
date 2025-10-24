# -*- coding: utf-8 -*-
# app.py (Nova Manufacturing Sim - V2-Framework-V4.4 - Integrated Structure)
#
# V4.4 更新：
# 1. 以用戶提供的參考程式碼為基礎架構 (login, teacher/student views)。
# 2. 整合 V4.2 的詳細模擬功能 (init_state, decision_form, calculation, dashboards)。
# 3. 決策狀態使用參考程式碼的檔案同步機制 (decisions[season][team_key])。
# 4. 核心模擬狀態 (BS, IS, inventory etc.) 仍使用 st.session_state.teams。

import streamlit as st
import pandas as pd
import copy
import pickle
import os
import numbers # V4.3
from datetime import datetime # V4.4

# ---------- Streamlit rerun 兼容墊片 ----------
if not hasattr(st, "rerun"):
    def _compat_rerun(): st.experimental_rerun()
    st.rerun = _compat_rerun

# ---------- 基本設定 ----------
DECISIONS_FILE = "decisions_state.pkl"
TEAM_LIST = [f"第 {i} 組" for i in range(1, 11)]
PASSWORDS = {
    "admin": "admin123", # 老師密碼
    "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660",
    "第 7 組": "ice112", "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526",
}
GLOBAL_PARAMS = { # 遊戲參數 (同 V4.2)
    'factory_cost': 5000000,'factory_maintenance': 100000,'factory_capacity': 8,
    'line_p1_cost': 1000000,'line_p1_maintenance': 20000,'line_p1_capacity': 1000,
    'raw_material_cost_R1': 100,'p1_labor_cost': 50,'p1_material_needed_R1': 1,'p1_depreciation_per_line': 10000,
    'line_p2_cost': 1200000,'line_p2_maintenance': 25000,'line_p2_capacity': 800,
    'raw_material_cost_R2': 150,'p2_labor_cost': 70,'p2_material_needed_R2': 1,'p2_depreciation_per_line': 12000,
    'bank_loan_interest_rate_per_season': 0.02,'emergency_loan_interest_rate': 0.05,'tax_rate': 0.20,
    'rd_costs_to_level_up': {2: 500000, 3: 1500000, 4: 3500000, 5: 6500000}
}
DEFAULT_PRICE_P1 = 300; DEFAULT_AD_P1 = 50000; DEFAULT_PRICE_P2 = 450; DEFAULT_AD_P2 = 50000

# ---------- 工具 (來自 V4.2 和參考程式碼) ----------
def force_numeric(value, default=0):
    if isinstance(value, numbers.Number): return value
    elif isinstance(value, str):
         try: return float(value.replace(",", "")) # 嘗試移除逗號
         except ValueError: return default
    else: return default

def save_decisions(decisions_dict): # 使用參考程式碼的邏輯
    if not isinstance(decisions_dict, dict): st.error("儲存決策錯誤：傳入的不是字典！"); decisions_dict = {}
    try:
        with open(DECISIONS_FILE, 'wb') as f: pickle.dump(decisions_dict, f)
    except Exception as e: st.error(f"儲存決策檔案 {DECISIONS_FILE} 時出錯: {e}")

def load_decisions(): # 使用參考程式碼的邏輯 + V4.2 強化
    decisions = {}
    if os.path.exists(DECISIONS_FILE):
        try:
            with open(DECISIONS_FILE, 'rb') as f:
                loaded_data = pickle.load(f)
                if isinstance(loaded_data, dict): decisions = loaded_data
                else: st.warning(f"決策檔案 {DECISIONS_FILE} 內容格式不符 (非字典)，將重置。"); clear_decisions()
        except FileNotFoundError: st.warning(f"嘗試讀取決策檔案 {DECISIONS_FILE} 時找不到檔案。")
        except EOFError: st.warning(f"決策檔案 {DECISIONS_FILE} 為空或損壞，將重置。"); clear_decisions()
        except pickle.UnpicklingError: st.warning(f"決策檔案 {DECISIONS_FILE} 格式錯誤，將重置。"); clear_decisions()
        except Exception as e: st.error(f"讀取決策檔案 {DECISIONS_FILE} 時發生未知錯誤: {e}"); clear_decisions()
    return decisions

def clear_decisions(): # 使用參考程式碼的邏輯
    try:
        if os.path.exists(DECISIONS_FILE): os.remove(DECISIONS_FILE)
    except Exception as e: st.error(f"刪除決策檔案 {DECISIONS_FILE} 時出錯: {e}")

# ---------- 核心模擬邏輯 (來自 V4.2) ----------
def init_team_state(team_key):
    # (此函數與 V4.2 版本完全相同)
    initial_cash = 10000000; initial_factories = 1; initial_lines_p1 = 1; initial_lines_p2 = 1
    initial_inv_r1 = 2000; initial_inv_r2 = 2000; initial_inv_p1 = 500; initial_inv_p2 = 500
    cogs_p1 = (...); cogs_p2 = (...)
    inv_value = (...); fixed_assets = (...); total_assets = (...); initial_equity = total_assets
    return { # ... (返回字典結構同 V4.2) ...
    }

def balance_bs(bs_data):
    # (此函數與 V4.2 版本完全相同)
    if not isinstance(bs_data, dict): bs_data = {}
    cash = force_numeric(bs_data.get('cash', 0)); inv_val = force_numeric(bs_data.get('inventory_value', 0))
    fixed_val = force_numeric(bs_data.get('fixed_assets_value', 0)); acc_depr = force_numeric(bs_data.get('accumulated_depreciation', 0))
    loan = force_numeric(bs_data.get('bank_loan', 0)); equity = force_numeric(bs_data.get('shareholder_equity', 0))
    bs_data['total_assets'] = cash + inv_val + fixed_val - acc_depr
    bs_data['total_liabilities_and_equity'] = loan + equity
    if abs(bs_data['total_assets'] - bs_data['total_liabilities_and_equity']) > 1:
        diff = bs_data['total_assets'] - bs_data['total_liabilities_and_equity']
        bs_data['shareholder_equity'] = equity + diff
        bs_data['total_liabilities_and_equity'] = bs_data['total_assets']
    for key in [...]: bs_data[key] = force_numeric(bs_data.get(key, 0)) # 確保都是數字
    return bs_data

def display_dashboard(team_key, team_data): # 使用 V4.2 簡化版
    if not isinstance(team_data, dict): team_data = init_team_state(team_key)
    st.header(f"📈 {team_data.get('team_name', team_key)} ({team_key}) 儀表板 (第 {st.session_state.game_season} 季)")
    bs = team_data.get('BS', {}); is_data = team_data.get('IS', {}); mr = team_data.get('MR', {})
    st.subheader("📊 市場報告 (上季)"); st.write(mr)
    st.subheader("💰 損益表 (上季)")
    net_income = is_data.get('net_income', 0); st.metric("💹 稅後淨利", f"${force_numeric(net_income):,.0f}")
    with st.expander("查看詳細損益表 (原始數據)"): st.write(is_data)
    st.subheader("🏦 資產負債表 (當前)")
    total_assets = bs.get('total_assets', 0); st.metric("🏦 總資產", f"${force_numeric(total_assets):,.0f}")
    with st.expander("查看詳細資產負債表 (原始數據)"): st.write(bs)
    st.subheader("🏭 內部資產 (非財報)") # ... (內容同 V4.2) ...

def display_decision_form(team_key): # 使用 V4.2 詳細版
    team_data = st.session_state.teams.get(team_key)
    if not isinstance(team_data, dict): st.error(...) ; return
    mr_data = team_data.get('MR', {}); bs_data = team_data.get('BS', {})

    with st.form(f"decision_form_{team_key}", clear_on_submit=False): # V4.4 clear_on_submit=False
        st.header(f"📝 {team_data.get('team_name', team_key)} ({team_key}) - 第 {st.session_state.game_season} 季決策單")
        tab_p1, tab_p2, tab_prod, tab_fin = st.tabs(["P1 產品決策", "P2 產品決策", "生產與資本決策", "財務決策"])
        # ... (各 Tab 內容同 V4.2, 含風險提示和 force_numeric) ...
        submitted = st.form_submit_button("✅ 提交本季決策")
        if submitted:
            # (檢查邏輯同 V4.2)
            if ...: st.error(...) ; return
            if ...: st.error(...) ; return
            if ...: st.error(...) ; return

            decision_data_raw = { ... } # 收集表單原始數據
            decision_data = {k: force_numeric(v, 0) for k, v in decision_data_raw.items()} # V4.4 強制轉換

            # V4.4 使用參考程式碼的儲存結構
            all_dec = load_decisions()
            season = st.session_state.game_season
            if season not in all_dec: all_dec[season] = {}
            all_dec[season][team_key] = {
                "submitted": True,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": decision_data # 儲存轉換後的數字
            }
            save_decisions(all_dec)
            st.success(f"{team_data.get('team_name', team_key)} ({team_key}) 第 {st.session_state.game_season} 季決策已提交！等待老師結算...")
            st.rerun()

def run_season_calculation(): # 使用 V4.2 穩定版
    """V4.2 結算引擎，強制類型檢查 + 穩定性"""
    # *** V4.4 修改：從 load_decisions() 獲取【當前賽季】的決策 ***
    teams = st.session_state.teams
    season = st.session_state.game_season # 當前賽季
    all_decisions_all_seasons = load_decisions()
    current_season_decisions_raw = all_decisions_all_seasons.get(season, {}) # 獲取本季所有隊伍提交的原始數據

    final_decisions = {} # <--- 這裡要存的是【決策數據 data】，而不是整個提交信息
    DEFAULT_PRICE_P1 = 300; DEFAULT_AD_P1 = 50000; DEFAULT_PRICE_P2 = 450; DEFAULT_AD_P2 = 50000

    for team_key in team_list:
        if team_key not in teams: st.session_state.teams[team_key] = init_team_state(team_key)
        team_data = teams.get(team_key)
        if not isinstance(team_data, dict): st.error(...) ; continue

        submitted_info = current_season_decisions_raw.get(team_key)
        decision_data = {} # 預設為空

        if isinstance(submitted_info, dict) and submitted_info.get("submitted"):
            decision_data = submitted_info.get("data", {}) # 獲取 data 部分
            if not isinstance(decision_data, dict): # 再次防禦
                 st.error(f"隊伍 {team_key} 的決策數據 data 損壞，將使用預設。")
                 decision_data = {}
            else:
                 final_decisions[team_key] = decision_data # 存儲 data 部分
        else: # 未提交或數據損壞
            if not submitted_info: # 處理未提交
                 st.warning(f"警告：{team_data.get('team_name', team_key)} ({team_key}) 未提交決策，將使用預設。")
            # --- 套用預設懲罰 (同 V4.2) ---
            mr_data = team_data.get('MR', {});
            if not isinstance(mr_data, dict): mr_data = {}
            decision_data = {
                'price_p1': mr_data.get('price_p1', DEFAULT_PRICE_P1), # ... 其他 ...
            }
            final_decisions[team_key] = decision_data # 存儲預設 data

    # *** 後續結算邏輯使用 final_decisions (這個只包含 data 的字典) ***
    # === 階段 1: 結算支出、生產、研發 ===
    # (此階段邏輯與 V4.2 相同, 使用 final_decisions)
    for team_key, decision in final_decisions.items(): # ...
    # === 階段 2: 市場結算 ===
    # (此階段邏輯與 V4.2 相同, 使用 final_decisions)
    # --- P1 市場 ---
    market_p1_data = {}; total_score_p1 = 0
    for key, d in final_decisions.items(): # ...
    # --- P2 市場 ---
    market_p2_data = {}; total_score_p2 = 0
    for key, d in final_decisions.items(): # ...
    # === 階段 3: 財務報表結算 ===
    # (此階段邏輯與 V4.2 相同, 使用 final_decisions)
    for team_key, team_data in teams.items(): # ...
        bs = balance_bs(team_data.get('BS', {}))
        # === 階段 4: 緊急貸款 ===
        if bs.get('cash', 0) < 0: # ...
            bs = balance_bs(bs)
        team_data['BS'] = bs if isinstance(bs, dict) else {}; team_data['IS'] = is_data if isinstance(is_data, dict) else {}
    # === 階段 5: 推進遊戲 (*** V4.4 修改：只清檔案 ***) ===
    st.session_state.game_season += 1
    # *** 不再需要清空 st.session_state.decisions ***
    clear_decisions() # 只刪除檔案
    st.success(f"第 {st.session_state.game_season - 1} 季結算完畢！已進入第 {st.session_state.game_season} 季。")

def calculate_company_value(bs_data):
    # (此函數與 V4.2 版本完全相同)
    value = force_numeric(bs_data.get('cash', 0)) + ...
    return value

def display_admin_dashboard(): # 使用 V4.2 詳細版 + 參考程式碼的提交檢查
    """顯示老師的控制台畫面"""
    st.header(f"👨‍🏫 管理員控制台 (第 {st.session_state.game_season} 季)")
    # --- 學生密碼總覽 (V4.0 簡化) ---
    with st.expander("🔑 學生密碼總覽"):
        st.warning("請勿將此畫面展示給學生。")
        st.write(PASSWORDS) # 直接打印字典
        st.caption("如需修改密碼，請直接修改 app.py ...")
    # --- 修改團隊數據 (V2.5) ---
    with st.expander("🔧 修改團隊數據 (Edit Team Data)"): # ... (內容同 V4.2) ...
    # --- A. 排行榜 (V4.2) ---
    st.subheader("遊戲排行榜 (依公司總價值)") # ... (內容同 V4.2) ...
    # --- B. 監控面板 (*** V4.4 使用參考程式碼邏輯 ***) ---
    st.subheader("📮 本季決策提交狀態")
    all_dec = load_decisions() # 讀取檔案
    season = st.session_state.game_season
    season_dec = all_dec.get(season, {}) # 獲取本季提交數據

    submitted_count = 0
    rows = []
    for t in TEAM_LIST:
        info = season_dec.get(t) # 檢查該隊伍是否在本季提交字典中
        is_submitted = isinstance(info, dict) and info.get("submitted")
        rows.append({
            "組別": t,
            "是否提交": "✅" if is_submitted else "—",
            "提交時間": info.get("timestamp", "") if is_submitted else "" # V4.4 修正
        })
        if is_submitted: submitted_count += 1

    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    st.info(f"提交進度: {submitted_count} / {len(TEAM_LIST)}")

    # 查看詳細 (參考程式碼邏輯)
    who = st.selectbox("查看某一組的決策內容", TEAM_LIST)
    info = season_dec.get(who)
    if isinstance(info, dict) and info.get("submitted"):
        st.write(info.get("data", {}))
    else:
        st.info("該組尚未提交或數據異常。")

    # V4.4 移除單獨的刷新按鈕，因為 DataFrame 會自動更新

    # --- C. 控制按鈕 (V3.7) ---
    st.subheader("遊戲控制")
    if st.button("➡️ 結算本季"):
        # V4.4 可以在這裡加一個確認，如果 submitted_count != len(TEAM_LIST)
        if submitted_count != len(TEAM_LIST):
             st.warning("警告：並非所有隊伍都已提交，未提交者將使用預設決策。")
        with st.spinner("正在執行市場結算..."): run_season_calculation()
        st.rerun()
    if st.button("♻️ !!! 重置整個遊戲 !!!"):
        st.session_state.game_season = 1; st.session_state.teams = {}; st.session_state.logged_in_user = None
        clear_decisions() # V4.4
        st.success("遊戲已重置回第 1 季"); st.rerun()
    # V4.4 登出按鈕移到 header_bar
    # if st.button("登出"): st.session_state.logged_in_user = None; st.rerun()

# ---------- 頂部工具列 (來自參考程式碼) ----------
def header_bar():
    left, right = st.columns([3,1])
    with left:
        # V4.4 顯示登入者
        user = st.session_state.get("logged_in_user", "未知用戶")
        role = st.session_state.get("role", "未知角色")
        team_name = ""
        if role == "student" and user in st.session_state.get("teams", {}):
            team_name = f" ({st.session_state.teams[user].get('team_name', user)})"
        st.caption(f"已登入：{user}{team_name} | 當前季別：第 {st.session_state.game_season} 季")
    with right:
        if st.button("登出"):
            st.session_state.logged_in = False
            st.session_state.role = None
            # V4.4 不重置 team_key，登入時會覆蓋
            st.success("已登出")
            st.rerun()

# ---------- 登入介面 (來自參考程式碼 + V4.4 修改) ----------
def login_view():
    st.title("🏭 Nova Manufacturing Sim — 登入")
    # V4.4 使用參考程式碼的帳號密碼登入
    username = st.text_input("請輸入您的隊伍名稱 (例如 第 1 組) 或 管理員帳號 (admin)")
    password = st.text_input("請輸入密碼：", type="password")

    if st.button("登入"):
        # 檢查是否為老師
        if username == "admin" and password == PASSWORDS.get("admin"):
            st.session_state.logged_in = True
            st.session_state.role = "teacher"
            st.success("老師登入成功")
            st.rerun()
        # 檢查是否為學生隊伍
        elif username in PASSWORDS and password == PASSWORDS.get(username):
            st.session_state.logged_in = True
            st.session_state.role = "student"
            st.session_state.team_key = username # 記錄登入的組別
            # 確保隊伍已初始化
            if username not in st.session_state.get("teams", {}):
                 st.session_state.setdefault("teams", {})[username] = init_team_state(username)
            st.success(f"{username} 登入成功")
            st.rerun()
        # 密碼或帳號錯誤
        else:
            st.error("帳號或密碼錯誤！請檢查輸入是否正確（例如 '第 1 組' 中間有空格）。")

# ---------- 學生介面 (來自參考程式碼 + V4.4 整合) ----------
def student_view(team_key):
    # V4.4 確保 team_data 存在
    if team_key not in st.session_state.get("teams", {}):
        st.session_state.setdefault("teams", {})[team_key] = init_team_state(team_key)
    current_team_data = st.session_state.teams[team_key]

    # --- B1. 學生側邊欄 ---
    st.sidebar.header(f"🎓 {current_team_data.get('team_name', team_key)} ({team_key})")
    new_team_name = st.sidebar.text_input("修改您的隊伍名稱：", value=current_team_data.get('team_name', team_key))
    if new_team_name != current_team_data.get('team_name', team_key):
        if not new_team_name.strip(): st.sidebar.error("隊伍名稱不能為空！")
        else: st.session_state.teams[team_key]['team_name'] = new_team_name; st.sidebar.success("隊伍名稱已更新！"); st.rerun()

    # --- B2. 學生主畫面 ---
    display_dashboard(team_key, current_team_data) # 顯示儀表板
    st.markdown("---")

    # 檢查是否已提交 (使用參考程式碼的邏輯)
    all_dec = load_decisions()
    season = st.session_state.game_season
    season_dec = all_dec.get(season, {})
    submitted_info = season_dec.get(team_key)
    already_submitted = isinstance(submitted_info, dict) and submitted_info.get("submitted")

    if already_submitted:
        st.info(f"您已提交第 {st.session_state.game_season} 季的決策 ({submitted_info.get('timestamp','')})，請等待老師結算...")
        with st.expander("查看已提交內容"):
            st.write(submitted_info.get("data", {}))
        # V4.4 可以選擇加入撤銷按鈕
        # if st.button("撤銷提交"):
        #     all_dec = load_decisions()
        #     if season in all_dec and team_key in all_dec[season]:
        #         del all_dec[season][team_key]
        #         if not all_dec[season]: # 如果是最後一個提交者，刪除該季
        #             del all_dec[season]
        #         save_decisions(all_dec)
        #         st.success("已撤銷提交，您可以重新填寫。")
        #         st.rerun()
    else:
        display_decision_form(team_key) # 顯示詳細決策表單

# ---------- 入口 (來自參考程式碼 + V4.4 修正) ----------
def main():
    # V4.4 使用 logged_in 作為主要判斷
    if not st.session_state.get("logged_in", False):
        login_view()
    else:
        header_bar()
        role = st.session_state.get("role")
        if role == "teacher":
            display_admin_dashboard() # 顯示老師詳細控制台
        elif role == "student":
            team_key = st.session_state.get("team_key")
            if team_key:
                 student_view(team_key) # 顯示學生詳細畫面
            else:
                 st.error("學生身份錯誤，缺少組別信息，請重新登入。")
                 st.session_state.logged_in = False; st.rerun() # 強制登出
        else:
            st.error("未知身分，請重新登入。")
            st.session_state.logged_in = False; st.rerun() # 強制登出

if __name__ == "__main__":
    # V4.4 初始化 session_state
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if "role" not in st.session_state: st.session_state.role = None
    if "team_key" not in st.session_state: st.session_state.team_key = None
    if "game_season" not in st.session_state: st.session_state.game_season = 1
    # V4.4 不在初始化時讀取 decisions
    # if "decisions" not in st.session_state: st.session_state.decisions = load_decisions()
    if "teams" not in st.session_state: st.session_state.teams = {}

    main()
