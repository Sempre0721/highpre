# test_video_to_base64.py
import requests
import json
import base64
import os

# 配置
SERVER_URL = "http://127.0.0.1:5839"
VIDEO_NAME = "test.mp4"  # 替换为您要测试的视频文件名

def test_video_to_base64():
    """
    测试视频转Base64接口
    """
    print("开始测试视频转Base64接口...")
    
    # 检查视频文件是否存在
    input_folder = "videos/input"
    video_path = os.path.join(input_folder, VIDEO_NAME)
    
    if not os.path.exists(video_path):
        print(f"错误: 视频文件 {video_path} 不存在")
        print("请确保视频文件存在于 videos/input 目录中")
        return
    
    # 准备请求数据
    payload = {
        "video_name": VIDEO_NAME
    }
    
    # 发送请求
    try:
        response = requests.post(
            f"{SERVER_URL}/video_to_base64",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )
        
        # 解析响应
        if response.status_code == 200:
            result = response.json()
            
            if result['code'] == 0:
                print("✅ 视频转Base64成功!")
                print(f"文件大小: {result['data']['file_size']} 字节")
                
                # 保存Base64数据到文件
                base64_filename = f"{os.path.splitext(VIDEO_NAME)[0]}_base64.txt"
                with open(base64_filename, 'w', encoding='utf-8') as f:
                    f.write(result['data']['video_base64'])
                
                print(f"Base64数据已保存到: {base64_filename}")
                
                # 验证解码
                decoded_data = base64.b64decode(result['data']['video_base64'])
                print(f"解码后数据大小: {len(decoded_data)} 字节")
                
                # 保存解码后的文件用于验证
                decoded_filename = f"{os.path.splitext(VIDEO_NAME)[0]}_decoded{os.path.splitext(VIDEO_NAME)[1]}"
                with open(decoded_filename, 'wb') as f:
                    f.write(decoded_data)
                
                print(f"解码后的文件已保存到: {decoded_filename}")
                print("验证: 文件大小匹配" if len(decoded_data) == result['data']['file_size'] else "验证: 文件大小不匹配")
                
            else:
                print(f"❌ 转换失败: {result['message']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")

def test_with_different_videos():
    """
    测试多个视频文件
    """
    input_folder = "videos/input"
    
    if not os.path.exists(input_folder):
        print(f"输入文件夹 {input_folder} 不存在")
        return
    
    video_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'))]
    
    if not video_files:
        print("未找到视频文件，请在 videos/input 目录中放置视频文件")
        return
    
    print(f"找到 {len(video_files)} 个视频文件:")
    for i, video_file in enumerate(video_files, 1):
        print(f"{i}. {video_file}")
    
    for video_file in video_files:
        print(f"\n--- 测试文件: {video_file} ---")
        payload = {
            "video_name": video_file
        }
        
        try:
            response = requests.post(
                f"{SERVER_URL}/video_to_base64",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['code'] == 0:
                    print(f"✅ {video_file} 转换成功")
                    print(f"   Base64长度: {len(result['data']['video_base64'])}")
                    print(f"   文件大小: {result['data']['file_size']} 字节")
                else:
                    print(f"❌ {video_file} 转换失败: {result['message']}")
            else:
                print(f"❌ {video_file} HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {video_file} 测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    print("视频转Base64测试脚本")
    print("=" * 50)
    
    # 创建必要的文件夹
    os.makedirs("videos/input", exist_ok=True)
    os.makedirs("videos/output", exist_ok=True)
    
    print("请选择测试模式:")
    print("1. 测试单个指定视频文件")
    print("2. 测试所有视频文件")
    
    choice = input("请输入选择 (1 或 2): ").strip()
    
    if choice == "1":
        test_video_to_base64()
    elif choice == "2":
        test_with_different_videos()
    else:
        print("无效选择，执行默认测试")
        test_video_to_base64()
