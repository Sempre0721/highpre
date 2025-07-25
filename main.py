# main.py
import json
import os
import logging
import shutil
import subprocess
import base64
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
import ollama
from openai import OpenAI
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
#from tencentcloud.ivld import ivld_client, models
import base64

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

# 初始化数据库
def init_database():
    """初始化数据库"""
    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            operation_type TEXT NOT NULL,
            input_data TEXT,
            output_data TEXT,
            status TEXT DEFAULT 'success',
            duration REAL,
            file_name TEXT,
            description TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# 记录操作历史
def record_history(operation_type, input_data, output_data, status, duration, file_name, description):
    """记录操作历史"""
    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO operation_history 
        (operation_type, input_data, output_data, status, duration, file_name, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        operation_type,
        json.dumps(input_data, ensure_ascii=False) if input_data else None,
        json.dumps(output_data, ensure_ascii=False) if output_data else None,
        status,
        duration,
        file_name,
        description
    ))
    
    conn.commit()
    conn.close()

# 加载配置
config = load_config()

# 初始化数据库
init_database()

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

# 历史记录页面路由
@app.route('/history')
def history():
    return render_template('history.html')

# 获取历史记录API
@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        conn = sqlite3.connect('history.db')
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        cursor = conn.cursor()
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page
        
        # 查询总数
        cursor.execute('SELECT COUNT(*) FROM operation_history')
        total = cursor.fetchone()[0]
        
        # 查询历史记录
        cursor.execute('''
            SELECT * FROM operation_history 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        records = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        history_data = []
        for record in records:
            history_data.append({
                'id': record['id'],
                'timestamp': record['timestamp'],
                'operation_type': record['operation_type'],
                'input_data': json.loads(record['input_data']) if record['input_data'] else None,
                'output_data': json.loads(record['output_data']) if record['output_data'] else None,
                'status': record['status'],
                'duration': record['duration'],
                'file_name': record['file_name'],
                'description': record['description']
            })
        
        return jsonify({
            'code': 0,
            'message': '获取历史记录成功',
            'data': {
                'records': history_data,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}")
        return jsonify({
            'code': 1001,
            'message': f'获取历史记录失败: {str(e)}'
        }), 500

# Ollama 接口
@app.route('/ollama', methods=['POST'])
def chat_with_ollama():
    start_time = datetime.now()
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
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='ai_analysis',
            input_data=data,
            output_data={'response': response['response'].strip()},
            status='success',
            duration=duration,
            file_name=None,
            description=f'Ollama AI分析 - 模型: {model}'
        )

        return jsonify({
            'code': 0,
            'message': '成功获取模型回复',
            'data': {
                'response': response['response'].strip()
            }
        })

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='ai_analysis',
            input_data=data,
            output_data={'error': str(e)},
            status='failed',
            duration=duration,
            file_name=None,
            description=f'Ollama AI分析失败 - 模型: {model}'
        )
        
        return jsonify({
            'code': 1002,
            'message': f'调用 Ollama 失败: {str(e)}'
        }), 500

# 调用讯飞星火大模型
@app.route('/xfyun', methods=['POST'])
def chat_with_xfyun():
    start_time = datetime.now()
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
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='ai_analysis',
            input_data=data,
            output_data={'response': completion.choices[0].message.content.strip()},
            status='success',
            duration=duration,
            file_name=None,
            description=f'讯飞星火AI分析 - 模型: {model}'
        )

        return jsonify({
            'code': 0,
            'message': '成功获取模型回复',
            'data': {
                'response': completion.choices[0].message.content.strip()
            }
        })

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='ai_analysis',
            input_data=data,
            output_data={'error': str(e)},
            status='failed',
            duration=duration,
            file_name=None,
            description=f'讯飞星火AI分析失败 - 模型: {model}'
        )
        
        return jsonify({
            'code': 1002,
            'message': f'调用讯飞星火 API 失败: {str(e)}'
        }), 500

# 调用腾讯云大模型
@app.route('/tencent', methods=['POST'])
def chat_with_tencent():
    start_time = datetime.now()
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
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='ai_analysis',
            input_data=data,
            output_data={'response': completion.choices[0].message.content.strip()},
            status='success',
            duration=duration,
            file_name=None,
            description=f'腾讯云AI分析 - 模型: {model}'
        )

        return jsonify({
            'code': 0,
            'message': '成功获取模型回复',
            'data': {
                'response': completion.choices[0].message.content.strip()
            }
        })

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='ai_analysis',
            input_data=data,
            output_data={'error': str(e)},
            status='failed',
            duration=duration,
            file_name=None,
            description=f'腾讯云AI分析失败 - 模型: {model}'
        )
        
        return jsonify({
            'code': 1002,
            'message': f'调用腾讯云 API 失败: {str(e)}'
        }), 500

# 调用腾讯云智能媒体服务分析视频
@app.route('/tencent_video_analysis', methods=['POST'])
def tencent_video_analysis():
    start_time = datetime.now()
    data = request.get_json()
    video_name = data.get('video_name')
    
    if not video_name:
        return jsonify({
            'code': 1001,
            'message': '缺少 video_name 参数'
        }), 400

    try:
        # 构建完整输入路径
        input_path = os.path.join(app.config['INPUT_FOLDER'], video_name)
        
        # 检查输入文件是否存在
        if not os.path.exists(input_path):
            return jsonify({
                'code': 404,
                'message': f'视频文件不存在: {input_path}'
            }), 404

        # 初始化腾讯云认证信息
        cred = credential.Credential(
            config['models']['tencent']['secret_id'],
            config['models']['tencent']['secret_key']
        )
        
        # 配置HTTP profile
        httpProfile = HttpProfile()
        httpProfile.endpoint = config['models']['tencent']['ivld_endpoint']
        
        # 配置client profile
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        
        # 初始化客户端
        client = ivld_client.IvldClient(cred, config['models']['tencent']['region'], clientProfile)
        
        # 创建请求
        req = models.CreateMediaProcessTaskRequest()
        params = {
            "MediaProcessTask": {
                "Type": "AnalyseMedia",
                "InputInfo": {
                    "Type": "URL",
                    "Url": f"http://localhost:{config['server']['port']}/videos/input/{video_name}"  # 需要公网可访问的URL
                }
            }
        }
        req.from_json_string(json.dumps(params))
        
        # 发送请求
        resp = client.CreateMediaProcessTask(req)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='tencent_video_analysis',
            input_data=data,
            output_data={'task_id': resp.TaskId},
            status='success',
            duration=duration,
            file_name=video_name,
            description=f'腾讯云视频分析任务提交 - 文件: {video_name}'
        )
        
        return jsonify({
            'code': 0,
            'message': '成功提交视频分析任务',
            'data': {
                'task_id': resp.TaskId
            }
        })

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='tencent_video_analysis',
            input_data=data,
            output_data={'error': str(e)},
            status='failed',
            duration=duration,
            file_name=video_name,
            description=f'腾讯云视频分析任务提交失败 - 文件: {video_name}'
        )
        
        logger.error(f"调用腾讯云视频分析失败: {str(e)}")
        return jsonify({
            'code': 1002,
            'message': f'调用腾讯云视频分析失败: {str(e)}'
        }), 500

# 获取腾讯云视频分析结果
@app.route('/tencent_video_analysis_result', methods=['POST'])
def get_tencent_video_analysis_result():
    start_time = datetime.now()
    data = request.get_json()
    task_id = data.get('task_id')
    
    if not task_id:
        return jsonify({
            'code': 1001,
            'message': '缺少 task_id 参数'
        }), 400

    try:
        # 初始化腾讯云认证信息
        cred = credential.Credential(
            config['models']['tencent']['secret_id'],
            config['models']['tencent']['secret_key']
        )
        
        # 配置HTTP profile
        httpProfile = HttpProfile()
        httpProfile.endpoint = config['models']['tencent']['ivld_endpoint']
        
        # 配置client profile
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        
        # 初始化客户端
        client = ivld_client.IvldClient(cred, config['models']['tencent']['region'], clientProfile)
        
        # 创建请求
        req = models.DescribeMediaProcessTaskRequest()
        params = {
            "TaskId": task_id
        }
        req.from_json_string(json.dumps(params))
        
        # 发送请求
        resp = client.DescribeMediaProcessTask(req)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='tencent_video_analysis_result',
            input_data=data,
            output_data={'status': resp.Task.Status, 'result': resp.Task.Result if hasattr(resp.Task, 'Result') else None},
            status='success',
            duration=duration,
            file_name=None,
            description=f'腾讯云视频分析结果查询 - 任务ID: {task_id}'
        )
        
        return jsonify({
            'code': 0,
            'message': '成功获取视频分析结果',
            'data': {
                'status': resp.Task.Status,
                'result': resp.Task.Result if hasattr(resp.Task, 'Result') else None
            }
        })

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='tencent_video_analysis_result',
            input_data=data,
            output_data={'error': str(e)},
            status='failed',
            duration=duration,
            file_name=None,
            description=f'腾讯云视频分析结果查询失败 - 任务ID: {task_id}'
        )
        
        logger.error(f"获取腾讯云视频分析结果失败: {str(e)}")
        return jsonify({
            'code': 1002,
            'message': f'获取腾讯云视频分析结果失败: {str(e)}'
        }), 500

@app.route('/cut_video', methods=['POST'])
def cut_video():
    start_time = datetime.now()
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
    duration_val = float(end) - float(start)
    command = [
        'ffmpeg',
        '-i', input_path,
        '-ss', str(start),
        '-t', str(duration_val)
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
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 记录历史
            record_history(
                operation_type='cut_video',
                input_data=data,
                output_data={'error': result.stderr, 'command': ' '.join(command)},
                status='failed',
                duration=duration,
                file_name=name,
                description=f'视频剪切失败 - 文件: {name}'
            )
            
            return jsonify({
                'code': 500,
                'message': '视频剪切失败',
                'error': result.stderr,
                'command': ' '.join(command)
            }), 500

        # 检查输出文件是否真的创建了
        if not os.path.exists(output_path):
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 记录历史
            record_history(
                operation_type='cut_video',
                input_data=data,
                output_data={'error': '输出文件未创建', 'output_path': output_path, 'command': ' '.join(command)},
                status='failed',
                duration=duration,
                file_name=name,
                description=f'视频剪切完成但输出文件未创建 - 文件: {name}'
            )
            
            return jsonify({
                'code': 500,
                'message': '视频剪切完成但输出文件未创建',
                'output_path': output_path,
                'command': ' '.join(command)
            }), 500

        # 确保输出路径使用正斜杠，以便在 Web 中正确显示
        web_output_path = output_path.replace('\\', '/')
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='cut_video',
            input_data=data,
            output_data={'output': f'/videos/output/{output_filename}'},
            status='success',
            duration=duration,
            file_name=name,
            description=f'视频剪切成功 - 文件: {name}'
        )
        
        return jsonify({
            'code': 0,
            'message': '视频剪切成功',
            'data': {
                'output': f'/videos/output/{output_filename}'  # 更新为正确的访问路径
            }
        })

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 记录历史
        record_history(
            operation_type='cut_video',
            input_data=data,
            output_data={'error': str(e)},
            status='failed',
            duration=duration,
            file_name=name,
            description=f'视频剪切异常 - 文件: {name}'
        )
        
        logger.error(f"Exception during video cutting: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'执行剪切时发生异常: {str(e)}'
        }), 500

# 添加静态文件路由以访问输入视频
@app.route('/videos/input/<path:filename>')
def serve_input_video(filename):
    """提供输入视频文件访问"""
    return send_from_directory(app.config['INPUT_FOLDER'], filename)

app.route('/video_to_base64', methods=['POST'])
def video_to_base64():
    """
    接收视频文件名，返回其 Base64 编码
    """
    data = request.get_json()
    video_name = data.get('video_name')

    if not video_name:
        return jsonify({
            'code': 1,
            'message': '缺少 video_name 参数'
        }), 400

    video_path = os.path.join(app.config['INPUT_FOLDER'], video_name)

    if not os.path.exists(video_path):
        return jsonify({
            'code': 2,
            'message': f'视频文件 {video_name} 不存在'
        }), 404

    try:
        print(f"正在读取视频文件: {video_path}")
        with open(video_path, "rb") as video_file:
            encoded_str = base64.b64encode(video_file.read()).decode('utf-8')
        print(f"视频文件 {video_name} 转换完成，Base64长度: {len(encoded_str)}")

        return jsonify({
            'code': 0,
            'message': '成功',
            'data': {
                'video_base64': encoded_str,
                'file_size': os.path.getsize(video_path)
            }
        })
    except Exception as e:
        print(f"处理视频文件时出错: {str(e)}")
        return jsonify({
            'code': 3,
            'message': f'转换失败: {str(e)}'
        }), 500
    
if __name__ == '__main__':
    app.run(
        host=config['server']['host'],
        port=config['server']['port'],
        debug=config['server']['debug']
    )
