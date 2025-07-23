from flask import Flask, render_template, request, jsonify
import ollama
import subprocess
import os

app = Flask(__name__)

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
    path = data.get('path')
    name = data.get('name')

    # 参数校验
    if None in [start, end, path, name]:
        return jsonify({
            'code': 400,
            'message': '缺少必要参数'
        }), 400

    input_path = os.path.join(path, name)
    output_path = os.path.join(path, 'output.mp4')

    # 检查输入文件是否存在
    if not os.path.isfile(input_path):
        return jsonify({
            'code': 404,
            'message': f'视频文件不存在: {input_path}'
        }), 404

    # 构建 ffmpeg 命令
    duration = end - start
    command = [
        'ffmpeg',
        '-i', input_path,
        '-ss', str(start),
        '-t', str(duration),
        '-c', 'copy',
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

        return jsonify({
            'code': 0,
            'message': '视频剪切成功',
            'data': {
                'output': output_path
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'执行剪切时发生异常: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5839)