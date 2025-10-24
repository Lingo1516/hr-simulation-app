# -*- coding: utf-8 -*-
# Nova Manufacturing Sim - V4.3.1 (Teacher/Student Secure Version)
# Author: ChatGPT修正版 2025-10
# 改進重點：
# 1. 全面改用 st.rerun()
# 2. 加入 rerun 相容墊片
# 3. 老師與學生皆需密碼登入
# 4. 老師端可查看各組提交狀況

import streamlit as st
import pickle
import os
import numbers

# === Streamlit rerun 兼容性墊片 ===
if not hasattr(st, "rerun"):
    def _compat_rerun():
        st.experimental_rerun()
    st.rerun = _compat_rerun

# === 全域設定 ===
DECISIONS_FILE = "decisions_state.pkl"
PASSWORDS = {
    "admin": "admin123",
    "第 1 組": "sky902", "第 2 組": "rock331", "第 3 組": "lion774",
    "第 4 組": "moon159", "第 5 組": "tree482", "第 6 組": "fire660",
    "第 7 組": "ice112", "第 8 組": "sun735", "第 9 組": "king048", "第 10 組": "aqua526"
}
team_list = [f"第 {i} 組" for i in range(1, 11)]

# === 通用函式 ===
def force_numeric(value, default=0):
    if isinstance(value, numbers.Number): return value
    if isinstance(value, str) and value.replace('.', '', 1).isdigit():
        try: return float(value)
        except: return default
    return default

def save_decisions_to_file(decisions_dict):
    try:
        with open(DECISIONS_FILE, 'wb') as f:
            pickle.dump(decisions_dict, f)
    except Exception as e:
        st.error(f"儲存決策檔案出錯: {e}")

def load_decisions_from_file():
    if os.path.exists(DECISIONS_FILE):
        try:
            with open(DECISIONS_FILE, 'rb') as f:
                return pickle.load(f)
        except:
            return {}
    return {}

def delete_decisions_file():
    if os.path.exists(DECISIONS_FILE):
        os.remove(DECISIONS_FILE)

# === 初始化 ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "team_key" not in st.session_state:
    st.session_state.team_key = None
if "game_season" not in st.session_state:
    st.session_state.game_season = 1

# === 登入畫面 ===
def login_view():
    st.title("🏭 Nova Manufacturing Sim 登入系統")

    role = st.radio("請選擇身份", ["學生", "老師"])
    username = st.text_input("帳號 (組別/教師代號)")
    password = st.text_input("密碼", type="password")

    if st.button("登入"):
        if role == "老師":
            if username == "admin" and password == PASSWORDS.get("admin"):
                st.session_state.logged_in = True
                st.session_state.role = "teacher"
                st.success("老師登入成功")
                st.rerun()
            else:
                st.error("老師帳號或密碼錯誤。")
        else:
            if username in PASSWORDS and PASSWORDS[username] == password:
                st.session_state.logged_in = True
                st.session_state.role = "student"
                st.session_state.team_key = username
                st.success(f"{username} 登入成功！")
                st.rerun()
            else:
                st.error("組別或密碼錯誤。")

# === 學生端畫面 ===
def student_view(team_key):
    st.header(f"👩‍🎓 學生端 - {team_key}")
    st.subheader(f"目前為第 {st.session_state.game_season} 季")

    decisions = load_decisions_from_file()
    if team_key in decisions:
        st.success("✅ 已提交決策")
        st.write(decisions[team_key])
    else:
        st.warning("尚未提交決策")

    with st.form("decision_form"):
        price = st.number_input("設定產品價格", 100, 1000, 300, 10)
        ad = st.number_input("設定廣告費用", 0, 200000, 50000, 10000)
        submit = st.form_submit_button("提交決策")
        if submit:
            decisions[team_key] = {"price": price, "ad": ad}
            save_decisions_to_file(decisions)
            st.success("決策已提交！")
            st.rerun()

# === 老師端畫面 ===
def teacher_view():
    st.header("👨‍🏫 老師端控制台")
    st.subheader(f"目前為第 {st.session_state.game_season} 季")

    decisions = load_decisions_from_file()
    if not decisions:
        st.info("目前尚無任何組別提交決策。")
    else:
        st.success(f"已提交組數：{len(decisions)} / 10")
        for team in team_list:
            if team in decisions:
                st.markdown(f"✅ **{team} 已提交**")
            else:
                st.markdown(f"❌ {team} 尚未提交")

        with st.expander("📄 查看各組詳細決策"):
            st.write(decisions)

    if st.button("📈 進行結算（下一季）"):
        delete_decisions_file()
        st.session_state.game_season += 1
        st.success(f"已結算，進入第 {st.session_state.game_season} 季")
        st.rerun()

# === 主畫面 ===
def main():
    if not st.session_state.logged_in:
        login_view()
    else:
        if st.session_state.role == "teacher":
            teacher_view()
        elif st.session_state.role == "student":
            student_view(st.session_state.team_key)

        st.sidebar.button("登出", on_click=lambda: logout())

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.team_key = None
    st.success("已登出")
    st.rerun()

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    main()
