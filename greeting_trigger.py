import requests
import time

# 替换成你的 Streamlit 应用 URL
APP_URL = "https://liang-xvbai-nmwnveofnh6hxjvtx8fwcq.streamlit.app/"

def trigger_greeting():
    try:
        # 访问应用，触发 init_session_state 中的时间检查逻辑
        response = requests.get(APP_URL, timeout=10)
        if response.status_code == 200:
            print("问候触发成功")
        else:
            print(f"触发失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"触发异常: {e}")

if __name__ == "__main__":
    trigger_greeting()