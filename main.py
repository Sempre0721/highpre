from flask import Flask, render_template, request, jsonify
import ollama
import subprocess
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 配置文件夹
INPUT_FOLDER = 'videos/input'
OUTPUT_FOLDER = 'videos/output'
app.config['INPUT_FOLDER'] = INPUT_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 确保文件夹存在
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 首页路由
@app.route('/')
def home():
    return render_template('index.html')

# 预留的 Ollama 接口
@app.route('/chatollama', methods=['POST'])
def chat_with_ollama():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model', 'huihui_ai/qwen2.5-1m-abliterated:latest') 

    if not prompt:
        return jsonify({
            'code': 1001,
            'message': '缺少 prompt 参数'
        }), 400

    try:
        # 生成回复
        response = ollama.generate(model=model, prompt=prompt)

        return jsonify({
            'code': 0,
            'message': '成功获取模型回复',
            'data': {
                'response': response['response'].strip()
            }
        })

    except Exception as e:
        return jsonify({
            'code': 1002,
            'message': f'调用 Ollama 失败: {str(e)}'
        }), 500

@app.route('/cut_video', methods=['POST'])
def cut_video():
    data = request.get_json()
    start = data.get('start')
    end = data.get('end')
    path = data.get('path')  # 本地视频路径
    name = data.get('name')

    # 参数校验
    if None in [start, end, path, name]:
        return jsonify({
            'code': 400,
            'message': '缺少必要参数'
        }), 400

    # 构建完整输入路径（假设视频在 INPUT_FOLDER 中）
    input_path = os.path.join(app.config['INPUT_FOLDER'], name)
    output_filename = f"cut_{name}"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    # 检查输入文件是否存在
    if not os.path.isfile(input_path):
        return jsonify({
            'code': 404,
            'message': f'视频文件不存在: {input_path}'
        }), 404

    # 构建 ffmpeg 命令，使用 H.264 编码确保浏览器兼容性
    duration = float(end) - float(start)
    command = [
        'ffmpeg',
        '-i', input_path,
        '-ss', str(start),
        '-t', str(duration),
        '-c:v', 'libx264',      # 使用 H.264 视频编码
        '-c:a', 'aac',          # 使用 AAC 音频编码
        '-strict', 'experimental',
        '-preset', 'fast',      # 编码速度预设
        '-crf', '23',           # 视频质量 (18-28 是合理范围)
        '-pix_fmt', 'yuv420p',  # 像素格式，确保兼容性
        '-movflags', '+faststart',  # 优化 Web 播放
        output_path
    ]

    try:
        # 执行命令
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            return jsonify({
                'code': 500,
                'message': '视频剪切失败',
                'error': result.stderr
            }), 500

        # 确保输出路径使用正斜杠，以便在 Web 中正确显示
        web_output_path = output_path.replace('\\', '/')
        
        return jsonify({
            'code': 0,
            'message': '视频剪切成功',
            'data': {
                'output': '/' + web_output_path  # 添加前缀以便在网页中访问
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'执行剪切时发生异常: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5839)