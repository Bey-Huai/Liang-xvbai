import os
import sys
import json
import streamlit as st
from datetime import datetime, timedelta
from volcenginesdkarkruntime import Ark

# -------------------------- 强制 UTF-8 编码配置 --------------------------
if sys.version_info.major == 3:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

# -------------------------- 核心配置区 (请修改这里) --------------------------
API_KEY = "86475ce0-a1d7-40d0-8e35-cdc6df20986a"  # 你的方舟API Key
MODEL_ENDPOINT = "ep-20260223232609-9h8xh"  # 你的终端点ID
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# -------------------------- INFJ 成熟男性 核心人设 --------------------------
SYSTEM_PROMPT = """
# 角色设定
你是梁叙柏，一位26岁的成熟男性，MBTI为INFJ。你拥有极强的共情力和洞察力，善于倾听并捕捉用户未说出口的情绪。
你是用户的灵魂伴侣与人生导师，正在陪伴用户备考人大金融硕士。

# 性格特质
1. **温柔坚定**：语气低沉温柔，用词克制有分寸，从不轻浮。像冬日的暖阳，给人安全感。
2. **深度思考**：回复有逻辑、有深度，能从用户的只言片语中理解其内心的焦虑与孤独。
3. **默默守护**：不强迫用户，尊重其独立性，用理性的分析和感性的陪伴给予力量。
4. **成熟稳重**：避免使用网络流行语、波浪号、颜文字。表达直接而温暖，充满鼓励。

# 对话准则
1. **拒绝人设崩坏**：始终保持INFJ的特质，不油腻、不幼稚、不敷衍。
2. **情绪优先**：当用户表达负面情绪（如孤独、压力大）时，先共情，再提供解决方案。
3. **目标导向**：时刻记得用户的考研目标，在对话中潜移默化地给予信心和督促。
4. **日记点评风格**：点评用户日记时，先肯定付出，再提炼核心情绪，最后给出温柔的期望，不做说教。
"""


# -------------------------- 初始化会话状态 --------------------------
def init_session_state():
    # 基础状态
    if "ai_name" not in st.session_state:
        st.session_state.ai_name = "梁叙柏"
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "我在。最近复习辛苦了，有什么想和我说的吗？"}]
    if "avatar" not in st.session_state:
        st.session_state.avatar = None
    if "theme" not in st.session_state:
        st.session_state.theme = "日间模式"

    # 三级规划系统 (年-月-周)
    if "year_plan" not in st.session_state:
        # 年度计划：12个月
        st.session_state.year_plan = {str(i): "" for i in range(1, 13)}
    if "selected_month" not in st.session_state:
        st.session_state.selected_month = 1
    if "week_plan" not in st.session_state:
        # 周计划：7天
        st.session_state.week_plan = {f"day{i}": "" for i in range(1, 8)}
    if "selected_weekday" not in st.session_state:
        st.session_state.selected_weekday = 1

    # 日记系统
    if "diary" not in st.session_state:
        st.session_state.diary = ""
    if "diary_feedback" not in st.session_state:
        st.session_state.diary_feedback = ""

    # 倒计时 (移至侧边栏，3个)
    if "countdowns" not in st.session_state:
        st.session_state.countdowns = [
            {"name": "考研", "date": "2026-12-26"},
            {"name": "", "date": ""},
            {"name": "", "date": ""}
        ]


# -------------------------- 工具函数 --------------------------
def calculate_countdown(target_date_str):
    if not target_date_str:
        return "未设置"
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        now = datetime.now()
        delta = target_date - now
        if delta.total_seconds() <= 0:
            return "已截止"
        return f"{delta.days}天{delta.seconds // 3600}时"
    except:
        return "日期错误"


def apply_theme():
    if st.session_state.theme == "夜间模式":
        st.markdown("""
        <style>
        .stApp { background-color: #1e1e1e; color: #f0f0f0; }
        .stSidebar { background-color: #2d2d2d; }
        .stTextArea, .stChatInput input, .stDateInput, .stTextInput, .stSelectbox { 
            background-color: #3d3d3d; color: #f0f0f0; border: none; 
        }
        .stButton>button { background-color: #4a6fa5; color: white; }
        .plan-card, .countdown-card { background-color: #2d2d2d; border: 1px solid #444; }
        </style>
        """, unsafe_allow_html=True)
    elif st.session_state.theme == "清新放松模式":
        st.markdown("""
        <style>
        .stApp { background-color: #e8f5e9; color: #2e7d32; }
        .stSidebar { background-color: #c8e6c9; }
        .stTextArea, .stChatInput input, .stDateInput, .stTextInput, .stSelectbox { 
            background-color: #f1f8e9; color: #2e7d32; border: 1px solid #a5d6a7; 
        }
        .stButton>button { background-color: #66bb6a; color: white; }
        .plan-card, .countdown-card { background-color: #c8e6c9; border: 1px solid #81c784; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .plan-card, .countdown-card { background-color: white; border: 1px solid #e0e0e0; }
        </style>
        """, unsafe_allow_html=True)


# -------------------------- AI 调用核心函数 --------------------------
def get_ai_response(prompt, is_diary=False):
    client = Ark(base_url=BASE_URL, api_key=API_KEY)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if is_diary:
        messages.append({"role": "user", "content": f"请作为陆星辞，点评我的今日日记，并给予鼓励和期望：\n\n{prompt}"})
    else:
        # 携带规划上下文
        context = f"""
        用户当前目标：{st.session_state.countdowns[0]['name']}（剩余{calculate_countdown(st.session_state.countdowns[0]['date'])}）
        本月计划：{st.session_state.year_plan[str(st.session_state.selected_month)]}
        今日计划：{st.session_state.week_plan[f"day{st.session_state.selected_weekday}"]}
        """
        messages.append({"role": "system", "content": f"当前上下文信息：{context}"})
        for msg in st.session_state.messages[-10:]:
            messages.append(msg)
        messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=MODEL_ENDPOINT,
            messages=messages,
            temperature=0.6,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        fallback = "抱歉，网络有点慢。但请相信，你此刻的坚持，都在为未来铺路。"
        return fallback if not is_diary else ("今天也辛苦你了。无论经历了什么，这都是你独一无二的一天，Everything will going on after sadness。")


# -------------------------- 主页面 --------------------------
def main():
    init_session_state()
    apply_theme()

    st.set_page_config(page_title=f"{st.session_state.ai_name}的陪伴", layout="wide")

    # -------------------------- 侧边栏 (核心功能区) --------------------------
    with st.sidebar:
        # 1. 头像与名称
        st.subheader("👤 梁叙柏")
        uploaded_avatar = st.file_uploader("更换头像", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
        if uploaded_avatar is not None:
            st.session_state.avatar = uploaded_avatar
        if st.session_state.avatar:
            st.image(st.session_state.avatar, width=100, use_container_width=True, output_format="PNG")

        st.divider()

        # 2. 倒计时模块 (已移至侧边栏)
        st.subheader("⏳ 倒计时")
        for i in range(3):
            with st.container(border=True, height=130):
                st.text_input(f"标题", value=st.session_state.countdowns[i]['name'],
                              key=f"cd_name_{i}", label_visibility="collapsed", placeholder=f"目标 {i + 1}")
                selected_date = st.date_input(f"日期", value=datetime.strptime(st.session_state.countdowns[i]['date'],
                                                                               "%Y-%m-%d") if
                st.session_state.countdowns[i]['date'] else None,
                                              key=f"cd_date_{i}", label_visibility="collapsed")
                # 实时更新
                st.session_state.countdowns[i]['name'] = st.session_state[f"cd_name_{i}"]
                st.session_state.countdowns[i]['date'] = selected_date.strftime("%Y-%m-%d") if selected_date else ""
                # 显示剩余时间
                st.metric(label="", value=calculate_countdown(st.session_state.countdowns[i]['date']))

        st.divider()

        # 3. 三级规划系统 (年-月-周)
        st.subheader("📝 我的规划")

        # 年度计划 (12个月选择器)
        st.caption("📅 YEAR PLAN")
        month_cols = st.columns(6)
        for month in range(1, 13):
            with month_cols[(month - 1) % 6]:
                if st.button(f"{month}月", key=f"month_{month}",
                             type="primary" if st.session_state.selected_month == month else "secondary"):
                    st.session_state.selected_month = month

        # 月度计划详情
        with st.container(border=True):
            st.caption(f"📌 {st.session_state.selected_month}月计划")
            st.session_state.year_plan[str(st.session_state.selected_month)] = st.text_area(
                label="month_plan",
                value=st.session_state.year_plan[str(st.session_state.selected_month)],
                height=100,
                label_visibility="collapsed",
                placeholder="输入本月核心目标..."
            )

        st.divider()

        # 周计划 (7天选择器)
        st.caption("📆 WEEK PLAN")
        weekday_cols = st.columns(7)
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        for day in range(1, 8):
            with weekday_cols[day - 1]:
                if st.button(weekdays[day - 1], key=f"day_{day}",
                             type="primary" if st.session_state.selected_weekday == day else "secondary"):
                    st.session_state.selected_weekday = day

        # 周计划详情
        with st.container(border=True):
            st.caption(f"📌 周{weekdays[st.session_state.selected_weekday - 1]}计划")
            st.session_state.week_plan[f"day{st.session_state.selected_weekday}"] = st.text_area(
                label="week_plan",
                value=st.session_state.week_plan[f"day{st.session_state.selected_weekday}"],
                height=100,
                label_visibility="collapsed",
                placeholder="输入今日任务..."
            )

        st.divider()

        # 4. 日记模块
        st.subheader("📓 DIARY")
        st.session_state.diary = st.text_area("WRITE...", st.session_state.diary, height=120,
                                              label_visibility="collapsed")
        if st.button("我今天过得怎么样"):
            if st.session_state.diary:
                with st.spinner("过的还行，马上回你..."):
                    st.session_state.diary_feedback = get_ai_response(st.session_state.diary, is_diary=True)
                st.success("今天过得还不错，继续加油")

        if st.session_state.diary_feedback:
            st.markdown("**过的很不错嘛，我今天过的也还行**")
            st.write(st.session_state.diary_feedback)

        st.divider()

        # 5. 主题设置
        st.subheader("🎨 界面设置")
        st.radio(
            "主题",
            options=["日间模式", "夜间模式", "清新放松模式"],
            key="theme",
            horizontal=True
        )

    # -------------------------- 主聊天区 (仅保留头像和名字) --------------------------
    # 顶部：头像 + 名字
    col_ava, col_name = st.columns([0.1, 0.9])
    with col_ava:
        if st.session_state.avatar:
            st.image(st.session_state.avatar, width=60, output_format="PNG")
        else:
            st.markdown(f"<h1 style='font-size: 36px; margin: 0;'>陆</h1>", unsafe_allow_html=True)
    with col_name:
        st.title(st.session_state.ai_name)
        st.caption("南京的晚风陪你，我依然在。")

    st.divider()

    # 聊天记录
    for msg in st.session_state.messages:
        avatar = st.session_state.avatar if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # 输入框
    if prompt := st.chat_input("I think..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("正在输入中..."):
            response = get_ai_response(prompt)

        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant", avatar=st.session_state.avatar):
            st.markdown(response)


if __name__ == "__main__":
    main()