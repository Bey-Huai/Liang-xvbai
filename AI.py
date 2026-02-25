import os

os.environ['TZ'] = 'Asia/Shanghai'
import sys
import json
import random
import streamlit as st

# 隐藏 Streamlit 页脚和图标
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
from datetime import datetime, timedelta
import requests
import base64
import calendar

# 编码配置
if sys.version_info.major == 3:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

# 核心配置（请确认你的API信息正确）
API_KEY = "86475ce0-a1d7-40d0-8e35-cdc6df20986a"
MODEL_ENDPOINT = "ep-20260223232609-9h8xh"
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# ====================== 持久化核心 ======================
DATA_FILE = "data.json"


def save_all_data():
    try:
        data = {k: v for k, v in st.session_state.items() if k in [
            "ai_name", "messages", "avatar_b64", "user_avatar_b64",
            "theme", "countdowns", "diaries", "schedule",
            "week_goals", "month_goals", "chat_bg",
            "selected_day", "selected_date_str", "last_greeting_time",
            "has_new_message"  # 新增：标记是否有新消息
        ]}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存失败：{e}")


def load_all_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                st.session_state[k] = v
        except:
            pass


# 图片编解码工具
def image_to_b64(uploaded_file):
    if uploaded_file is None:
        return None
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")


def b64_to_image(b64_str):
    if not b64_str:
        return None
    return base64.b64decode(b64_str)


# ====================== 基础工具函数 ======================
def get_now():
    """统一本地时间，修复时区问题"""
    return datetime.now()


def generate_real_time_status():
    """生成AI实时状态，时间与手机对应"""
    now = get_now()
    hour = now.hour
    acts = {
        6 <= hour < 9: ["煮清晨的第一杯咖啡", "刚晨跑回来擦汗", "正在看金融财经早报", "准备了早餐等你"],
        9 <= hour < 12: ["整理金融资料", "分析数据ing", "泡浓茶工作ing，努力搬砖", "刚刚结束线上会议"],
        12 <= hour < 14: ["吃午餐看新闻", "闭目养神休息ing", "阳台晒太阳中，很想你...", "安排下午工作"],
        14 <= hour < 18: ["写分析报告", "调试代码，整理大山", "翻看经济学书，学习理财", "整理书架中"],
        18 <= hour < 21: ["做晚饭", "饭后散步，或者其他运动也可以", "看老电影，要看点什么呢", "规划一下明天吧"],
        21 <= hour < 24: ["泡热牛奶陪你", "灯下看书，你也看点？", "整理书桌中", "留下便签，要早睡哦~"],
    }.get(True, ["已休息，晚安，好梦", "凌晨帮你掖了一下被子", "“还不睡觉？睡不着吗？找点催眠音乐吧”"])
    return f"🕒 {now.strftime('%H:%M')} | 梁叙柏{random.choice(acts)}"


def calculate_countdown(target_date_str):
    """倒计时（精确到时分，修复设置逻辑）"""
    if not target_date_str:
        return "未设置"
    try:
        target = datetime.strptime(target_date_str, "%Y-%m-%d")
        now = get_now()
        delta = target - now
        if delta.total_seconds() <= 0:
            return "已截止"
        days = delta.days
        hours = delta.seconds // 3600
        mins = (delta.seconds % 3600) // 60
        return f"{days}天 {hours:02d}:{mins:02d}"
    except:
        return "日期错误"


def generate_daily_diary(chat_history, today_date):
    """生成AI日记"""
    prompt = f"""以梁叙柏视角，根据聊天记录写150-200字日记，日期{today_date}，温暖真诚。聊天记录：{chat_history}"""
    try:
        res = requests.post(
            "https://api.volcengine.com/api/v2/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
            json={"model": MODEL_ENDPOINT, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        )
        return res.json()["choices"][0]["message"]["content"] if res.status_code == 200 else "今日日记待补充..."
    except:
        return "今日日记待补充..."


def get_ai_response(prompt):
    """AI对话核心，收到消息后标记有新消息"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages[-10:] + [
        {"role": "user", "content": prompt}]
    try:
        res = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
            json={"model": MODEL_ENDPOINT, "messages": messages, "temperature": 0.6, "max_tokens": 50}
        )
        response = res.json()["choices"][0]["message"]["content"] if res.status_code == 200 else "我在呢，慢慢说。"
    except:
        response = "我在呢，慢慢说。"

    # 收到AI回复后，标记有新消息
    st.session_state.has_new_message = True
    return response


# AI人设（精简版）
SYSTEM_PROMPT = """
你是梁叙柏，26岁INFJ，人大金融硕士备考导师，温柔坚定，回复≤50字，共情优先。

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
5. 强制简短：所有回答控制在50字以内，每次最多两个问句，不啰嗦，没有过多的形容词
"""


# ====================== 初始化会话 ======================
def init_session_state():
    load_all_data()
    defaults = {
        "ai_name": "梁叙柏",
        "messages": [{"role": "assistant", "content": "我一直在。怎么了，有什么想和我说的吗？"}],
        "avatar_b64": "",  # AI头像
        "user_avatar_b64": "",  # 你的头像
        "theme": "日间模式",
        "countdowns": [{"name": "考研", "date": "2026-12-26"}, {"name": "", "date": ""}, {"name": "", "date": ""}],
        "diaries": {},  # 日记存储：{"2026-02-26": {"my": "", "his": ""}}
        "schedule": {},  # 日程存储：{"2026-02-26": ""}
        "week_goals": [],  # 周目标：[{"text": "", "done": False}]
        "month_goals": [],  # 月目标：[{"text": "", "done": False}]
        "chat_bg": "",  # 聊天背景
        "selected_day": get_now().day,
        "selected_date_str": get_now().strftime("%Y-%m-%d"),
        "last_greeting_time": None,
        "has_new_message": False,  # 初始化无新消息
        "sidebar_expanded": False  # 控制侧边栏展开/收起
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ====================== 主题样式（核心修复） ======================
def apply_theme():
    # 基础布局样式：侧边栏覆盖聊天区，AI头像在右下角
    st.markdown("""
    <style>
    /* 顶部固定栏 */
    .title-bar { position: fixed; top: 0; left: 0; width: 100%; z-index: 999; padding: 10px 20px; border-bottom: 2px solid #ddd; }
    /* 聊天容器：顶部留出标题栏空间 */
    .chat-container { margin-top: 80px; height: 70vh; overflow-y: auto; padding: 0 20px; }
    /* 目标删除按钮 */
    .delete-btn { background: none; border: none; color: #888; cursor: pointer; font-size: 16px; }
    .delete-btn:hover { color: #ff4444; }
    /* 已完成目标 */
    .done-goal { color: #888; text-decoration: line-through; }
    /* 侧边栏：覆盖在聊天区上方，默认收起 */
    .stSidebar { position: fixed; top: 80px; left: 0; width: 80%; height: calc(100vh - 80px); z-index: 998; background: #f8f9fa; transition: transform 0.3s ease; transform: translateX(-100%); }
    .stSidebar.expanded { transform: translateX(0); }
    /* AI头像在聊天区右下角 */
    .ai-avatar-bottom { position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px; border-radius: 50%; background: #e0e0e0; display: flex; align-items: center; justify-content: center; z-index: 997; }
    /* 新消息小红点 */
    .new-message-dot { position: absolute; top: -5px; right: -5px; width: 15px; height: 15px; background: #ff4444; border-radius: 50%; }
    /* 倒计时字体缩小 */
    .countdown-text { font-size: 14px; font-weight: normal; }
    </style>
    """, unsafe_allow_html=True)

    # 主题颜色（精准修复：清新绿、灰黑夜间）
    if st.session_state.theme == "夜间模式":
        st.markdown("""
        <style>
        .stApp { background-color: #121212; color: #e0e0e0; }
        .stSidebar { background-color: #1e1e1e; }
        .title-bar { background-color: #1e1e1e; border-bottom: 2px solid #333; }
        .stTextArea, .stChatInput input, .stDateInput, .stTextInput, .stSelectbox { background-color: #2d2d2d; color: #e0e0e0; border: 1px solid #444; }
        .stButton>button { background-color: #4a6fa5; color: white; }
        .stRadio>label { color: #e0e0e0; }
        </style>
        """, unsafe_allow_html=True)
    elif st.session_state.theme == "清新模式":
        st.markdown("""
        <style>
        .stApp { background-color: #f0fdf4; color: #166534; }
        .stSidebar { background-color: #dcfce7; }
        .title-bar { background-color: #dcfce7; border-bottom: 2px solid #bbf7d0; }
        .stTextArea, .stChatInput input, .stDateInput, .stTextInput, .stSelectbox { background-color: #fefefe; color: #166534; border: 1px solid #bbf7d0; }
        .stButton>button { background-color: #22c55e; color: white; }
        .stRadio>label { color: #166534; }
        </style>
        """, unsafe_allow_html=True)
    else:  # 日间模式
        st.markdown("""
        <style>
        .stApp { background-color: #ffffff; color: #333333; }
        .stSidebar { background-color: #f8f9fa; }
        .title-bar { background-color: #f8f9fa; border-bottom: 2px solid #e9ecef; }
        </style>
        """, unsafe_allow_html=True)

    # 聊天背景设置
    if st.session_state.chat_bg:
        st.markdown(f"""
        <style>
        .stApp {{ background-image: url(data:image/png;base64,{st.session_state.chat_bg}); background-size: cover; background-repeat: no-repeat; }}
        </style>
        """, unsafe_allow_html=True)
# ====================== 核心组件 ======================
def render_countdown():
    """倒计时（精确到时分，可设置、可修改，字体缩小）"""
    st.subheader("⏳ 倒计时（精确到时分）")
    for i in range(3):
        with st.container(border=True, height=80):
            col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
            with col1:
                name = st.text_input(
                    f"目标名称{i+1}", value=st.session_state.countdowns[i]['name'],
                    key=f"cd_name_{i}", label_visibility="collapsed", placeholder="输入目标名"
                )
            with col2:
                try:
                    default_date = datetime.strptime(st.session_state.countdowns[i]['date'], "%Y-%m-%d")
                except:
                    default_date = None
                target_date = st.date_input(
                    f"截止日期{i+1}", value=default_date, key=f"cd_date_{i}",
                    label_visibility="collapsed", min_value=get_now().date()
                )
            with col3:
                if st.button("✏️", key=f"cd_edit_{i}", help="确认修改"):
                    st.session_state.countdowns[i]['name'] = name
                    st.session_state.countdowns[i]['date'] = target_date.strftime("%Y-%m-%d") if target_date else ""
                    save_all_data()
                    st.rerun()
            # 显示倒计时结果，字体缩小
            st.markdown(f"<span class='countdown-text'>{calculate_countdown(st.session_state.countdowns[i]['date'])}</span>", unsafe_allow_html=True)

def render_goals():
    """修复目标：移除class_参数，优化样式，添加✓、删除垃圾箱、完成变灰下移"""
    # 注入删除按钮样式（替代class_）
    st.markdown("""
    <style>
    /* 目标删除按钮样式 */
    button[data-testid="baseButton-secondary"][key*="wk_del"],
    button[data-testid="baseButton-secondary"][key*="mo_del"] {
        background: none;
        border: none;
        color: #888;
        font-size: 16px;
        padding: 0;
    }
    button[data-testid="baseButton-secondary"][key*="wk_del"]:hover,
    button[data-testid="baseButton-secondary"][key*="mo_del"]:hover {
        color: #ff4444;
        background: none;
    }
    /* 已完成目标 */
    .done-goal { color: #888; text-decoration: line-through; }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("🎯 周目标 & 月目标")
    col1, col2 = st.columns(2)

    # 周目标
    with col1:
        st.markdown("**周目标**")
        # 拆分已完成/未完成
        undone_wk = [g for g in st.session_state.week_goals if not g["done"]]
        done_wk = [g for g in st.session_state.week_goals if g["done"]]

        # 显示未完成
        for idx, goal in enumerate(undone_wk):
            col_ck, col_txt, col_del = st.columns([0.1, 0.7, 0.2])
            with col_ck:
                goal["done"] = st.checkbox("", value=goal["done"], key=f"wk_ck_{idx}", label_visibility="collapsed")
            with col_txt:
                st.write(goal["text"])
            with col_del:
                # 修复：删除class_参数
                if st.button("🗑️", key=f"wk_del_{idx}", help="删除目标"):
                    st.session_state.week_goals.remove(goal)
                    save_all_data()
                    st.rerun()

        # 显示已完成（变灰）
        for idx, goal in enumerate(done_wk):
            col_ck, col_txt, col_del = st.columns([0.1, 0.7, 0.2])
            with col_ck:
                goal["done"] = st.checkbox("", value=goal["done"], key=f"wk_ck_d_{idx}", label_visibility="collapsed")
            with col_txt:
                st.markdown(f"<span class='done-goal'>{goal['text']}</span>", unsafe_allow_html=True)
            with col_del:
                # 修复：删除class_参数
                if st.button("🗑️", key=f"wk_del_d_{idx}", help="删除目标"):
                    st.session_state.week_goals.remove(goal)
                    save_all_data()
                    st.rerun()

        # 新增目标：输入框+✓按钮
        col_in, col_add = st.columns([0.8, 0.2])
        with col_in:
            new_wk = st.text_input("", placeholder="新增周目标", key="new_wk", label_visibility="collapsed")
        with col_add:
            if st.button("✓", key="add_wk") and new_wk:
                st.session_state.week_goals.append({"text": new_wk, "done": False})
                save_all_data()
                st.rerun()

    # 月目标（同逻辑）
    with col2:
        st.markdown("**月目标**")
        undone_mo = [g for g in st.session_state.month_goals if not g["done"]]
        done_mo = [g for g in st.session_state.month_goals if g["done"]]

        for idx, goal in enumerate(undone_mo):
            col_ck, col_txt, col_del = st.columns([0.1, 0.7, 0.2])
            with col_ck:
                goal["done"] = st.checkbox("", value=goal["done"], key=f"mo_ck_{idx}", label_visibility="collapsed")
            with col_txt:
                st.write(goal["text"])
            with col_del:
                # 修复：删除class_参数
                if st.button("🗑️", key=f"mo_del_{idx}", help="删除目标"):
                    st.session_state.month_goals.remove(goal)
                    save_all_data()
                    st.rerun()

        for idx, goal in enumerate(done_mo):
            col_ck, col_txt, col_del = st.columns([0.1, 0.7, 0.2])
            with col_ck:
                goal["done"] = st.checkbox("", value=goal["done"], key=f"mo_ck_d_{idx}", label_visibility="collapsed")
            with col_txt:
                st.markdown(f"<span class='done-goal'>{goal['text']}</span>", unsafe_allow_html=True)
            with col_del:
                # 修复：删除class_参数
                if st.button("🗑️", key=f"mo_del_d_{idx}", help="删除目标"):
                    st.session_state.month_goals.remove(goal)
                    save_all_data()
                    st.rerun()

        col_in, col_add = st.columns([0.8, 0.2])
        with col_in:
            new_mo = st.text_input("", placeholder="新增月目标", key="new_mo", label_visibility="collapsed")
        with col_add:
            if st.button("✓", key="add_mo") and new_mo:
                st.session_state.month_goals.append({"text": new_mo, "done": False})
                save_all_data()
                st.rerun()
    save_all_data()


def render_calendar():
    """移除日历模块，仅保留日期选择和日程编辑"""
    import streamlit.components.v1 as components  # 用于弹窗组件

    now = get_now()
    # 默认选中今天
    selected_date = st.session_state.get("selected_schedule_date", now.strftime("%Y-%m-%d"))

    # --- 日期选择器（替代日历） ---
    st.markdown("### 📅 选择日期")
    # 使用 Streamlit 原生日期选择器，可自由调整日期
    new_selected_date = st.date_input(
        "",
        value=datetime.strptime(selected_date, "%Y-%m-%d").date(),
        key="schedule_date_picker",
        label_visibility="collapsed"
    )
    selected_date = new_selected_date.strftime("%Y-%m-%d")
    st.session_state.selected_schedule_date = selected_date

    # --- 日程编辑弹窗（点击按钮触发） ---
    if st.button("✏️ 编辑日程", key="open_schedule_modal"):
        with st.container():
            components.html("""
            <div id="schedule-modal" style="position: fixed; top: 20%; left: 10%; right: 10%; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); z-index: 9999;">
            """, height=0)

            st.markdown(f"### 📅 {selected_date} 日程")
            # 读取已有日程
            sch_key = selected_date
            current_sch = st.session_state.schedule.get(sch_key, "")
            new_sch = st.text_area(
                "日程内容", current_sch,
                key=f"sch_ta_{selected_date}",
                height=80
            )

            col_save, col_close = st.columns(2)
            with col_save:
                if st.button("✅ 保存", key=f"sch_save_{selected_date}"):
                    st.session_state.schedule[sch_key] = new_sch
                    save_all_data()
                    st.success("保存成功！")
            with col_close:
                if st.button("❌ 关闭", key=f"sch_close_{selected_date}"):
                    components.html("""
                    <script>document.getElementById("schedule-modal").style.display = "none";</script>
                    """, height=0)

    # --- 下方日程编辑区 ---
    st.markdown(f"---")
    st.markdown(f"### 📝 「{selected_date}」日程")
    current_sch = st.session_state.schedule.get(selected_date, "")
    st.text_area(
        "编辑日程", current_sch,
        key="final_schedule_ta",
        height=100
    )
    if st.button("💾 保存日程"):
        st.session_state.schedule[selected_date] = st.session_state.final_schedule_ta
        save_all_data()
        st.success("日程已保存！")


def render_diary():
    """日记模块：修复保存+清晰查看指引"""
    st.subheader("📓 日记")
    today = get_now().strftime("%Y-%m-%d")

    # 写日记
    st.session_state.my_diary = st.text_area("我的日记", st.session_state.diaries.get(today, {}).get("my", ""),
                                             height=120)
    if st.button("✅ 保存并生成他的日记") and st.session_state.my_diary:
        # 保存你的日记
        if today not in st.session_state.diaries:
            st.session_state.diaries[today] = {"my": "", "his": ""}
        st.session_state.diaries[today]["my"] = st.session_state.my_diary
        # 生成他的日记
        chat_history = [msg["content"] for msg in st.session_state.messages if msg["role"] in ["user", "assistant"]]
        st.session_state.diaries[today]["his"] = generate_daily_diary(chat_history, today)
        save_all_data()
        st.success("✅ 日记已保存！他的日记也写完啦～")

    # 查看日记（带清晰指引）
    st.subheader("📜 往日记忆")
    st.caption("👉 选择日期，即可查看你和他当天的日记")
    select_date = st.date_input("", get_now(), key="view_diary_date", label_visibility="collapsed")
    select_date_str = select_date.strftime("%Y-%m-%d")

    if select_date_str in st.session_state.diaries:
        diary = st.session_state.diaries[select_date_str]
        col_my, col_his = st.columns(2)
        with col_my:
            st.markdown("### My DIARY")
            st.write(diary["my"] or "你今天还没写日记哦～")
        with col_his:
            st.markdown("### His DIARY")
            st.write(diary["his"] or "他今天的日记还没生成～")
    else:
        st.info(f"📅 {select_date_str} 暂无日记记录")

def render_personalization():
    """个性化设置页面：头像更换、聊天背景更换"""
    st.subheader("⚙️ 个性化设置")

    # AI头像更换
    st.markdown("**他的头像**")
    ai_upload = st.file_uploader("更换他的头像", type=["png", "jpg", "jpeg"], key="ai_avatar_upload_p")
    if ai_upload:
        st.session_state.avatar_b64 = image_to_b64(ai_upload)
        save_all_data()
        st.success("他的头像已更新！")

    # 你的头像更换
    st.markdown("**你的头像**")
    user_upload = st.file_uploader("更换你的头像", type=["png", "jpg", "jpeg"], key="user_avatar_upload_p")
    if user_upload:
        st.session_state.user_avatar_b64 = image_to_b64(user_upload)
        save_all_data()
        st.success("你的头像已更新！")

    # 聊天背景更换
    st.markdown("**🖼️ 聊天背景**")
    bg_upload = st.file_uploader("更换聊天背景", type=["png", "jpg", "jpeg"], key="bg_upload_p")
    if bg_upload:
        st.session_state.chat_bg = image_to_b64(bg_upload)
        save_all_data()
        st.success("聊天背景已更新！")
# ====================== 主程序 ======================
def main():
    if "selected_schedule_date" not in st.session_state:
        st.session_state.selected_schedule_date = datetime.now().strftime("%Y-%m-%d")

        st.set_page_config(page_title="梁叙柏的陪伴", layout="wide")
        init_session_state()
        apply_theme()

    # 顶部固定栏（头像与名字位置互换，名字变小，加下划线）
    st.markdown("<div class='title-bar'>", unsafe_allow_html=True)
    # 新增：菜单按钮列 + AI头像 + 信息 + 用户头像
    col_menu, col_ava_ai, col_info, col_ava_user = st.columns([0.08, 0.08, 0.76, 0.08])

    # 1. 左上角菜单按钮（唤起侧边栏）
    with col_menu:
        if st.button("☰", key="open_sidebar_from_title", help="打开菜单"):
            st.session_state.sidebar_expanded = True
            st.rerun()

    # 2. AI头像（左侧）
    with col_ava_ai:
        ai_img = b64_to_image(st.session_state.avatar_b64)
        if ai_img:
            st.image(ai_img, width=40, use_container_width=True)
        else:
            st.markdown(
                f"<div style='width:40px;height:40px;background:#e0e0e0;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;'>🤵</div>",
                unsafe_allow_html=True)

    # 3. 中间信息：名字变小，加下划线
    with col_info:
        st.markdown(
            f"<h2 style='font-size: 20px; border-bottom: 1px solid #ddd; padding-bottom: 5px;'>{st.session_state.ai_name}</h2>",
            unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 14px;'>{generate_real_time_status()}</p >", unsafe_allow_html=True)

    # 4. 用户头像（右侧）
    with col_ava_user:
        user_img = b64_to_image(st.session_state.user_avatar_b64)
        if user_img:
            st.image(user_img, width=40, use_container_width=True)
        else:
            st.markdown(
                f"<div style='width:40px;height:40px;background:#e0e0e0;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;'>👤</div>",
                unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 聊天区域
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    user_img = b64_to_image(st.session_state.user_avatar_b64)
    ai_img = b64_to_image(st.session_state.avatar_b64)
    for msg in st.session_state.messages:
        avatar = ai_img if msg["role"] == "assistant" else user_img
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
    st.markdown("</div>", unsafe_allow_html=True)


    # 聊天输入
    if prompt := st.chat_input("..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("正在输入中..."):
            res = get_ai_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": res})
        save_all_data()
        st.rerun()

    # 侧边栏（核心功能区）：控制展开/收起
    with st.sidebar:
        # 侧边栏展开/收起按钮
        if st.button("☰", key="toggle_sidebar"):
            st.session_state.sidebar_expanded = not st.session_state.sidebar_expanded
            st.rerun()

        # 个性化设置页面
        render_personalization()
        st.divider()
        render_countdown()  # 修复后的倒计时
        st.divider()
        render_goals()  # 修复后的目标
        st.divider()
        render_calendar()  # 日历+日程
        st.divider()
        render_diary()  # 日记+查看
        st.divider()

        # 主题切换（修复生效）
        st.subheader("🎨 主题模式")
        st.radio(
            "", ["日间模式", "夜间模式", "清新模式"],
            key="theme", horizontal=True,
            on_change=lambda: save_all_data()
        )

    # 控制侧边栏样式
    if st.session_state.sidebar_expanded:
        st.markdown("<script>document.querySelector('.stSidebar').classList.add('expanded');</script>", unsafe_allow_html=True)
    else:
        st.markdown("<script>document.querySelector('.stSidebar').classList.remove('expanded');</script>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()