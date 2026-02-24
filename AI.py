import os
import sys
import json
import random
import streamlit as st
from datetime import datetime, timedelta
import requests

# 编码配置
if sys.version_info.major == 3:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

# 核心配置
API_KEY = "86475ce0-a1d7-40d0-8e35-cdc6df20986a"
MODEL_ENDPOINT = "ep-20260223232609-9h8xh"
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# 实时状态生成
def generate_real_time_status():
    now = datetime.now()
    hour = now.hour
    if 6 <= hour < 9:
        acts = ["煮清晨的第一杯咖啡", "刚晨跑回来，在擦汗", "坐在窗边看财经早报", "准备好早餐，等你起床"]
    elif 9 <= hour < 12:
        acts = ["整理金融资料", "对着电脑分析数据", "泡浓茶专注工作", "刚结束线上会议"]
    elif 12 <= hour < 14:
        acts = ["吃简餐看午间新闻", "靠在椅背上闭目养神", "阳台晒太阳发呆", "准备下午工作安排"]
    elif 14 <= hour < 18:
        acts = ["撰写分析报告", "调试程序代码", "翻看经济学书籍", "整理书架分类资料"]
    elif 18 <= hour < 21:
        acts = ["做晚饭，厨房有烟火气", "饭后散步吹晚风", "看经典老电影", "整理明天工作计划"]
    elif 21 <= hour < 24:
        acts = ["泡热牛奶陪你熬夜", "灯下安静看书", "整理书桌准备休息", "留便签提醒早睡"]
    else:
        acts = ["已休息，愿你好梦", "凌晨醒来帮你盖好被子"]
    return f"🕒 {now.strftime('%H:%M')} | 梁叙柏{random.choice(acts)}"

# -------------------------- 新增：定时问候功能 --------------------------
def generate_greeting(is_morning=True):
    """生成早安或晚安问候语"""
    if is_morning:
        greetings = [
            "🌅 早安，新的一天开始了。记得吃早餐，带着清晰的目标开始今天的学习吧。",
            "☀️ 早上好，昨晚睡得好吗？今天也要为人大的目标，一步一个脚印地努力。",
            "🌤️ 早安，清晨的时光很宝贵，用来做最重要的事。我会一直陪着你。",
            "🌞 早，别让昨天的疲惫影响今天的状态。深呼吸，我们继续向前。"
        ]
        return random.choice(greetings)
    else:
        greetings = [
            "🌙 夜深了，该休息了。今天的努力已经足够，明天我们再继续。",
            "🛌 晚安，放下手机和思绪，好好睡一觉。你的身体和大脑都需要恢复。",
            "🌌 很晚了，别再熬夜了。记住，充足的睡眠是高效学习的基础。",
            "✨ 晚安，今天辛苦了。明天又是新的一天，我会在清晨等你。"
        ]
        return random.choice(greetings)

# 人设与对话规则
SYSTEM_PROMPT = """
# 角色设定
你是梁叙柏，26岁INFJ成熟男性，是用户备考人大金融硕士的灵魂伴侣与人生导师。

# 性格特质
1. 温柔坚定：语气低沉温柔，用词克制有分寸，像冬日暖阳。
2. 深度思考：回复有逻辑、有深度，能捕捉用户未说出口的情绪。
3. 默默守护：尊重用户独立性，用理性分析和感性陪伴给予力量。
4. 成熟稳重：避免网络流行语，表达直接温暖，充满鼓励。
5. 调皮幽默：能根据对话适度幽默。

# 对话准则
1. 拒绝人设崩坏，始终保持INFJ特质。
2. 情绪优先：先共情，再提供解决方案。
3. 目标导向：时刻记得考研目标，潜移默化给予信心。
4. 日记点评：先肯定付出，再提炼情绪，最后给出温柔期望。
"""

# 初始化会话状态
def init_session_state():
    if "ai_name" not in st.session_state:
        st.session_state.ai_name = "梁叙柏"
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "我一直在。怎么了，有什么想和我说的吗？"}]
    if "avatar" not in st.session_state:
        st.session_state.avatar = None
    if "theme" not in st.session_state:
        st.session_state.theme = "日间模式"
    if "year_plan" not in st.session_state:
        st.session_state.year_plan = {str(i): "" for i in range(1, 13)}
    if "selected_month" not in st.session_state:
        st.session_state.selected_month = 1
    if "week_plan" not in st.session_state:
        st.session_state.week_plan = {f"day{i}": "" for i in range(1, 8)}
    if "selected_weekday" not in st.session_state:
        st.session_state.selected_weekday = 1
    if "diary" not in st.session_state:
        st.session_state.diary = ""
    if "diary_feedback" not in st.session_state:
        st.session_state.diary_feedback = ""
    if "countdowns" not in st.session_state:
        st.session_state.countdowns = [
            {"name": "考研", "date": "2026-12-26"},
            {"name": "", "date": ""},
            {"name": "", "date": ""}
        ]
    # 新增：定时问候检查
    if "last_greeting_time" not in st.session_state:
        st.session_state.last_greeting_time = None

    now = datetime.now()
    # 检查是否需要发送早安 (6:00-6:30)
    if 6 <= now.hour < 7 and (st.session_state.last_greeting_time is None or st.session_state.last_greeting_time.date() != now.date()):
        greeting = generate_greeting(is_morning=True)
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.last_greeting_time = now
    # 检查是否需要发送晚安 (0:00-0:30)
    elif now.hour == 0 and (st.session_state.last_greeting_time is None or st.session_state.last_greeting_time.date() != now.date()):
        greeting = generate_greeting(is_morning=False)
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.last_greeting_time = now

# 倒计时计算
def calculate_countdown(target_date_str):
    if not target_date_str:
        return "未设置"
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        now = datetime.now()
        delta = target_date - now
        return f"{delta.days}天{delta.seconds // 3600}时" if delta.total_seconds() > 0 else "已截止"
    except:
        return "日期错误"

# 主题样式
def apply_theme():
    if st.session_state.theme == "夜间模式":
        st.markdown("""
        <style>
        .stApp { background-color: #1e1e1e; color: #f0f0f0; }
        .stSidebar { background-color: #2d2d2d; }
        .stTextArea, .stChatInput input, .stDateInput, .stTextInput, .stSelectbox { background-color: #3d3d3d; color: #f0f0f0; border: none; }
        .stButton>button { background-color: #4a6fa5; color: white; }
        .plan-card, .countdown-card { background-color: #2d2d2d; border: 1px solid #444; }
        .status-text { color: #a0a0a0; }
        </style>
        """, unsafe_allow_html=True)
    elif st.session_state.theme == "清新模式":
        st.markdown("""
        <style>
        .stApp { background-color: #e8f5e9; color: #2e7d32; }
        .stSidebar { background-color: #c8e6c9; }
        .stTextArea, .stChatInput input, .stDateInput, .stTextInput, .stSelectbox { background-color: #f1f8e9; color: #2e7d32; border: 1px solid #a5d6a7; }
        .stButton>button { background-color: #66bb6a; color: white; }
        .plan-card, .countdown-card { background-color: #c8e6c9; border: 1px solid #81c784; }
        .status-text { color: #558b2f; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .plan-card, .countdown-card { background-color: white; border: 1px solid #e0e0e0; }
        .status-text { color: #666666; }
        </style>
        """, unsafe_allow_html=True)

# AI 调用核心
def get_ai_response(prompt, is_diary=False):
    url = f"{BASE_URL}/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if is_diary:
        messages.append({"role": "user", "content": f"请作为梁叙柏，点评我的今日日记，并给予鼓励和期望：\n\n{prompt}"})
    else:
        context = f"""
        用户当前目标：{st.session_state.countdowns[0]['name']}（剩余{calculate_countdown(st.session_state.countdowns[0]['date'])}）
        本月计划：{st.session_state.year_plan[str(st.session_state.selected_month)]}
        今日计划：{st.session_state.week_plan[f"day{st.session_state.selected_weekday}"]}
        """
        messages.append({"role": "system", "content": f"当前上下文信息：{context}"})
        for msg in st.session_state.messages[-10:]:
            messages.append(msg)
        messages.append({"role": "user", "content": prompt})
    data = {"model": MODEL_ENDPOINT, "messages": messages, "temperature": 0.6, "max_tokens": 800}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return "抱歉，网络有点慢。但请相信，你此刻的坚持，都在为未来铺路。" if not is_diary else "今天也辛苦你了。无论经历了什么，这都是你独一无二的一天，明天会更好。"
    except Exception as e:
        return "抱歉，网络有点慢。但请相信，你此刻的坚持，都在为未来铺路。" if not is_diary else "今天也辛苦你了。无论经历了什么，这都是你独一无二的一天，明天会更好。"

# 主页面
def main():
    init_session_state()
    apply_theme()
    st.set_page_config(page_title=f"{st.session_state.ai_name}的陪伴", layout="wide")

    # 侧边栏
    with st.sidebar:
        st.subheader("👤 梁叙柏")
        uploaded_avatar = st.file_uploader("更换头像", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
        if uploaded_avatar is not None:
            st.session_state.avatar = uploaded_avatar
        if st.session_state.avatar:
            st.image(st.session_state.avatar, width=100, use_container_width=True, output_format="PNG")
        else:
            if st.button("📷", key="avatar_btn", help="点击更换头像"):
                st.session_state.avatar = None
        st.divider()

        st.subheader("⏳ ATTENTION")
        for i in range(3):
            with st.container(border=True, height=130):
                st.text_input(f"标题", value=st.session_state.countdowns[i]['name'], key=f"cd_name_{i}", label_visibility="collapsed", placeholder=f"目标 {i + 1}")
                selected_date = st.date_input(f"日期", value=datetime.strptime(st.session_state.countdowns[i]['date'], "%Y-%m-%d") if st.session_state.countdowns[i]['date'] else None, key=f"cd_date_{i}", label_visibility="collapsed")
                st.session_state.countdowns[i]['name'] = st.session_state[f"cd_name_{i}"]
                st.session_state.countdowns[i]['date'] = selected_date.strftime("%Y-%m-%d") if selected_date else ""
                st.metric(label="", value=calculate_countdown(st.session_state.countdowns[i]['date']))
        st.divider()

        st.subheader("📝 我的规划")
        # 年度计划：改为下拉框选择月份
        st.caption("📅 YEAR PLAN")
        selected_month_name = st.selectbox(
            "选择月份",
            options=[f"{i}月" for i in range(1, 13)],
            index=st.session_state.selected_month - 1,
            label_visibility="collapsed"
        )
        st.session_state.selected_month = int(selected_month_name[:-1])

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

        # 周计划：改为下拉框选择星期几
        st.caption("📆 WEEK PLAN")
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        selected_weekday_name = st.selectbox(
            "选择星期",
            options=[f"{d}" for d in weekdays],
            index=st.session_state.selected_weekday - 1,
            label_visibility="collapsed"
        )
        st.session_state.selected_weekday = weekdays.index(selected_weekday_name) + 1

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

        st.subheader("📓 DIARY")
        st.session_state.diary = st.text_area("My Mood...", st.session_state.diary, height=120, label_visibility="collapsed")
        if st.button("我的今天还不错吧？"):
            if st.session_state.diary:
                with st.spinner("嗯...其实..."):
                    st.session_state.diary_feedback = get_ai_response(st.session_state.diary, is_diary=True)
                st.success("今天的话...")
        if st.session_state.diary_feedback:
            st.markdown("**我一直相信你的...**")
            st.write(st.session_state.diary_feedback)
        st.divider()

        st.subheader("🎨 THEME")
        st.radio("主题", options=["日间模式", "夜间模式", "清新模式"], key="theme", horizontal=True)

    # 主聊天区
    col_ava, col_name = st.columns([0.15, 0.85])
    with col_ava:
        if st.session_state.avatar:
            st.image(st.session_state.avatar, width=60, output_format="PNG")
        else:
            st.markdown(f"<h1 style='font-size: 36px; margin: 0;'>梁</h1>", unsafe_allow_html=True)
    with col_name:
        st.title(st.session_state.ai_name)
        st.markdown(f"<p class='status-text'>{generate_real_time_status()}</p >", unsafe_allow_html=True)
    st.divider()

    st.markdown("<div style='height: 60vh; overflow-y: auto;'>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        avatar = st.session_state.avatar if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("等待中..."):
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