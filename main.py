# main.py
import json
import os
import logging
import shutil
import subprocess
from flask import Flask, render_template, request, jsonify, send_from_directory
import ollama
from openai import OpenAI

# 加载配置文件
def load_config():
    """加载配置文件"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("配置文件 config.json 未找到")
    except json.JSONDecodeError:
        raise ValueError("配置文件 config.json 格式错误")

# 加载配置
config = load_config()

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def clear_output_folder():
    """清空输出文件夹"""
    output_folder = config['folders']['output']
    if os.path.exists(output_folder):
        for filename in os.listdir(output_folder):
            file_path = os.path.join(output_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f'删除文件失败 {file_path}: {e}')

app = Flask(__name__)

# 配置文件夹
INPUT_FOLDER = config['folders']['input']
OUTPUT_FOLDER = config['folders']['output']
app.config['INPUT_FOLDER'] = INPUT_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 确保文件夹存在
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 添加静态文件路由以访问输出视频
@app.route('/videos/output/<path:filename>')
def serve_output_video(filename):
    """提供输出视频文件访问"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

# 首页路由
@app.route('/')
def home():
    return render_template('index.html')

# 结果页面路由
@app.route('/result')
def result():
    return render_template('result.html')

# Ollama 接口
@app.route('/ollama', methods=['POST'])
def chat_with_ollama():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model', config['models']['ollama']['default_model'])
    temperature = data.get('temperature', 0.7)
    seed = data.get('seed', 42)
    max_tokens = data.get('maxTokens', 1024)

    if not prompt:
        return jsonify({
            'code': 1001,
            'message': '缺少 prompt 参数'
        }), 400

    try:
        # 生成回复
        response = ollama.generate(
            model=model,
            prompt=prompt,
            options={
                'temperature': temperature,
                'seed': seed,
                'num_predict': max_tokens
            }
        )

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

# 调用讯飞星火大模型
@app.route('/xfyun', methods=['POST'])
def chat_with_xfyun():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model', config['models']['xfyun']['default_model'])
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('maxTokens', 1024)

    if not prompt:
        return jsonify({
            'code': 1001,
            'message': '缺少 prompt 参数'
        }), 400

    try:
        # 初始化讯飞星火客户端
        client = OpenAI(
            api_key=config['models']['xfyun']['api_key'],
            base_url=config['models']['xfyun']['base_url']
        )
        
        # 生成回复
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        return jsonify({
            'code': 0,
            'message': '成功获取模型回复',
            'data': {
                'response': completion.choices[0].message.content.strip()
            }
        })

    except Exception as e:
        return jsonify({
            'code': 1002,
            'message': f'调用讯飞星火 API 失败: {str(e)}'
        }), 500

# 调用腾讯云大模型
@app.route('/tencent', methods=['POST'])
def chat_with_tencent():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model', config['models']['tencent']['default_model'])
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('maxTokens', 1024)

    if not prompt:
        return jsonify({
            'code': 1001,
            'message': '缺少 prompt 参数'
        }), 400

    try:
        # 初始化腾讯云客户端
        client = OpenAI(
            api_key=config['models']['tencent']['api_key'],
            base_url=config['models']['tencent']['base_url']
        )
        
        # 生成回复
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        return jsonify({
            'code': 0,
            'message': '成功获取模型回复',
            'data': {
                'response': completion.choices[0].message.content.strip()
            }
        })

    except Exception as e:
        return jsonify({
            'code': 1002,
            'message': f'调用腾讯云 API 失败: {str(e)}'
        }), 500

@app.route('/cut_video', methods=['POST'])
def cut_video():
    data = request.get_json()
    start = data.get('start')
    end = data.get('end')
    path = data.get('path')  # 本地视频路径
    name = data.get('name')
    ffmpeg_params = data.get('ffmpegParams', {})  # 获取 FFmpeg 参数

    # 参数校验
    if None in [start, end, path, name]:
        return jsonify({
            'code': 400,
            'message': '缺少必要参数'
        }), 400

    # 清空输出文件夹
    clear_output_folder()

    # 构建完整输入路径（假设视频在 INPUT_FOLDER 中）
    input_path = os.path.join(app.config['INPUT_FOLDER'], name)
    output_filename = f"cut_{name}"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    # 记录路径信息用于调试
    logger.debug(f"Input path: {input_path}")
    logger.debug(f"Output path: {output_path}")
    logger.debug(f"Input file exists: {os.path.exists(input_path)}")

    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        return jsonify({
            'code': 404,
            'message': f'视频文件不存在: {input_path}'
        }), 404

    # 构建 ffmpeg 命令，使用用户设置的参数
    duration = float(end) - float(start)
    command = [
        'ffmpeg',
        '-i', input_path,
        '-ss', str(start),
        '-t', str(duration)
    ]
    
    # 添加视频编码器参数
    video_codec = ffmpeg_params.get('videoCodec', config['ffmpeg']['default_params']['videoCodec'])
    command.extend(['-c:v', video_codec])
    
    # 添加音频编码器参数
    audio_codec = ffmpeg_params.get('audioCodec', config['ffmpeg']['default_params']['audioCodec'])
    command.extend(['-c:a', audio_codec])
    
    # 添加其他参数
    if video_codec == 'libx264':
        command.extend(['-strict', 'experimental'])
    
    # 添加预设参数
    preset = ffmpeg_params.get('preset', config['ffmpeg']['default_params']['preset'])
    command.extend(['-preset', preset])
    
    # 添加CRF参数
    crf = ffmpeg_params.get('crf', config['ffmpeg']['default_params']['crf'])
    command.extend(['-crf', str(crf)])
    
    # 添加像素格式参数
    pix_fmt = ffmpeg_params.get('pixFmt', config['ffmpeg']['default_params']['pixFmt'])
    command.extend(['-pix_fmt', pix_fmt])
    
    # 添加movflags参数
    mov_flags = ffmpeg_params.get('movFlags', config['ffmpeg']['default_params']['movFlags'])
    command.extend(['-movflags', mov_flags])
    
    # 添加其他自定义参数
    other_params = ffmpeg_params.get('otherParams', '')
    if other_params:
        command.extend(other_params.split())
    
    # 输出文件路径
    command.append(output_path)

    try:
        # 记录要执行的命令
        logger.debug(f"Executing command: {' '.join(command)}")
        
        # 执行命令
        result = subprocess.run(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            cwd=os.getcwd()  # 确保在正确的目录下执行
        )

        # 记录执行结果
        logger.debug(f"Return code: {result.returncode}")
        logger.debug(f"Stdout: {result.stdout}")
        logger.debug(f"Stderr: {result.stderr}")

        if result.returncode != 0:
            return jsonify({
                'code': 500,
                'message': '视频剪切失败',
                'error': result.stderr,
                'command': ' '.join(command)
            }), 500

        # 检查输出文件是否真的创建了
        if not os.path.exists(output_path):
            return jsonify({
                'code': 500,
                'message': '视频剪切完成但输出文件未创建',
                'output_path': output_path,
                'command': ' '.join(command)
            }), 500

        # 确保输出路径使用正斜杠，以便在 Web 中正确显示
        web_output_path = output_path.replace('\\', '/')
        
        return jsonify({
            'code': 0,
            'message': '视频剪切成功',
            'data': {
                'output': f'/videos/output/{output_filename}'  # 更新为正确的访问路径
            }
        })

    except Exception as e:
        logger.error(f"Exception during video cutting: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'执行剪切时发生异常: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(
        host=config['server']['host'],
        port=config['server']['port'],
        debug=config['server']['debug']
    )