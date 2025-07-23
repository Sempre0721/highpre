import requests

# Flask 服务地址
BASE_URL = "http://localhost:5839"

def test_cut_video_api():
    url = f"{BASE_URL}/cut_video"
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "start": 10.5,
        "end": 23.7,
        "path": "D:\MyProject\highpre\TestVideo",  # 替换为你自己的视频路径
        "name": "test.mp4"    # 替换为你自己的视频文件名
    }

    try:
        print("正在发送请求...")
        response = requests.post(url, json=payload, headers=headers)

        print(f"状态码: {response.status_code}")
        try:
            print("响应内容:")
            print(response.json())
        except requests.exceptions.JSONDecodeError:
            print("返回内容不是 JSON 格式：")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("连接失败，请确认 Flask 服务是否已启动。")
    except Exception as e:
        print(f"发生异常: {e}")

if __name__ == "__main__":
    test_cut_video_api()