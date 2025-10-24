# -*- coding: utf-8 -*-
# Nova Manufacturing Sim - V4.3.2 (Student selects team from dropdown)
# 特色：
# - 學生：用下拉選擇組別 + 輸入該組密碼
# - 老師：只輸入老師密碼
# - 老師端可看到各組是否提交、查看細節、按鈕結算到下一季
# - 使用 st.rerun（含舊版相容墊片）

import streamlit as st
import pickle, os, numbers

# ---------- Streamlit rerun 兼容墊片 ----------
if not hasattr(st, "rerun"):
    def _compat_rerun():
        st.experimental_rerun()
    st.rerun = _compat_rerun

# ---------- 基本設定 ----------
DECISIONS_FILE = "decisions_state.pkl"
TEAM_LIST = [f"第 {i} 組" for i in range(1, 11)]
PASSWORDS = {
    "admin": "admin123",
    "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660",
    "第 7 組": "ice112", "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526",
}

# ---------- 工具 ----------
def force_numeric(v, d=0):
    if isinstance(v, numbers.Number): return v
    if isinstance(v, str):
        try: return float(v.replace(",", ""))
        except: return d
    return d

def save_decisions(d):
    try:
        with open(DECISIONS_FILE, "wb") as f: pickle.dump(d, f)
    except Exception as e:
        st.error(f"存檔失敗：{e}")

def load_decisions():
    if not os.path.exists(DECISIONS_FILE): return {}
    try:
        with open(DECISIONS_FILE, "rb") as f:
            data = pickle.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def clear_decisions():
    if os.path.exists(DECISIONS_FILE):
        try: os.remove(DECISIONS_FILE)
        except: pass

# ---------- Session 初始 ----------
st.set_page_config(layout="wide")
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "role" not in st.session_state: st.session_state.role = None         # "teacher" / "student"
if "team_key" not in st.session_state: st.session_state.team_key = None
if "game_season" not in st.session_state: st.session_state.game_season = 1

# ---------- 登入 ----------
def login_view():
    st.title("🏭 Nova Manufacturing Sim — 登入")

    role = st.radio("選擇身分", ["學生", "老師"], horizontal=True)

    if role == "老師":
        teacher_pw = st.text_input("老師密碼", type="password")
        if st.button("登入（老師端）"):
            if teacher_pw == PASSWORDS.get("admin"):
                st.session_state.logged_in = True
                st.session_state.role = "teacher"
                st.success("老師登入成功")
                st.rerun()
            else:
                st.error("老師密碼錯誤，請再試一次。")

    else:  # 學生
        team = st.selectbox("選擇你的組別", TEAM_LIST, index=0)
        student_pw = st.text_input("該組密碼（老師提供）", type="password")
        if st.button("登入（學生端）"):
            if PASSWORDS.get(team) == student_pw:
                st.session_state.logged_in = True
                st.session_state.role = "student"
                st.session_state.team_key = team
                st.success(f"{team} 登入成功")
                st.rerun()
            else:
                st.error("密碼錯誤，請向老師確認。")

# ---------- 學生端 ----------
def student_view(team_key):
    st.header(f"🎓 學生端 — {team_key}")
    st.caption(f"目前季別：第 {st.session_state.game_season} 季")

    decisions = load_decisions()
    already = decisions.get(st.session_state.game_season, {}).get(team_key)

    if already:
        st.success(f"你已提交本季決策（{already.get('timestamp','')}）")
        with st.expander("查看已提交內容"):
            st.write(already.get("data", {}))

    with st.form(f"decision_form_{team_key}", clear_on_submit=False):
        st.subheader("📝 本季決策")
        col1, col2 = st.columns(2)
        with col1:
            price = st.number_input("產品價格", 100, 1000, 300, 10)
            ad    = st.number_input("廣告費用", 0, 200000, 50000, 10000)
        with col2:
            produce = st.number_input("本季生產量", 0, 200000, 0, 100)
            buy_rm  = st.number_input("購買原料（單位）", 0, 200000, 0, 100)

        submitted = st.form_submit_button("✅ 提交")
        if submitted:
            from datetime import datetime
            all_dec = load_decisions()
            season = st.session_state.game_season
            if season not in all_dec: all_dec[season] = {}
            all_dec[season][team_key] = {
                "submitted": True,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {"price": int(price), "ad": int(ad), "produce": int(produce), "buy_rm": int(buy_rm)}
            }
            save_decisions(all_dec)
            st.success("已提交！老師端會即時看到你的組別已完成。")
            st.rerun()

# ---------- 老師端 ----------
def teacher_view():
    st.header("👨‍🏫 老師端控制台")
    st.caption(f"目前季別：第 {st.session_state.game_season} 季")

    all_dec = load_decisions()
    season = st.session_state.game_season
    season_dec = all_dec.get(season, {})

    # 提交總覽
    st.subheader("📮 提交狀態")
    submitted = [t for t in TEAM_LIST if t in season_dec]
    st.write(f"已提交：{len(submitted)} / {len(TEAM_LIST)}")

    import pandas as pd
    rows = []
    for t in TEAM_LIST:
        info = season_dec.get(t)
        rows.append({
            "組別": t,
            "是否提交": "✅" if info else "—",
            "提交時間": (info or {}).get("timestamp", "")
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # 查看詳細
    who = st.selectbox("查看某一組的決策內容", TEAM_LIST)
    info = season_dec.get(who)
    if info:
        st.write(info.get("data", {}))
    else:
        st.info("該組尚未提交。")

    st.divider()
    if st.button("📈 結算本季 → 進入下一季"):
        # 這裡可以串接你的結算邏輯；目前用清空提交 + 季度+1 的簡化流程
        clear_decisions()
        st.session_state.game_season += 1
        st.success(f"已結算，進入第 {st.session_state.game_season} 季")
        st.rerun()

# ---------- 頂部工具列 ----------
def header_bar():
    left, right = st.columns([3,1])
    with left:
        st.caption(f"學期進度：第 {st.session_state.game_season} 季")
    with right:
        if st.button("登出"):
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.team_key = None
            st.success("已登出")
            st.rerun()

# ---------- 入口 ----------
def main():
    if not st.session_state.logged_in:
        login_view()
    else:
        header_bar()
        if st.session_state.role == "teacher":
            teacher_view()
        elif st.session_state.role == "student":
            student_view(st.session_state.team_key)
        else:
            st.error("未知身分，請重新登入。")

if __name__ == "__main__":
    main()
