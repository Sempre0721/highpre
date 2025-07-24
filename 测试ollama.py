import requests

BASE_URL = "http://localhost:5839"

def test_chat_api():
    url = f"{BASE_URL}/chatollama"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": "你好,请分析某电影讲了什么"
    }

    try:
        print("正在发送请求...")
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"状态码: {response.status_code}")
        print("响应内容:")
        print(response.json())
        
    except requests.exceptions.ConnectionError:
        print("连接失败，请确认 Flask 服务是否已启动。")
    except Exception as e:
        print(f"发生异常: {e}")

if __name__ == "__main__":
    test_chat_api()
