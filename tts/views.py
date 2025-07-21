from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import tempfile
import asyncio
import edge_tts
import pyttsx3
import io
from gtts import gTTS
import time # Added for retry mechanism

# 可用的Edge TTS语音列表
VOICE_OPTIONS = {
    'en-US-female': 'en-US-JennyNeural',
    'en-US-male': 'en-US-GuyNeural',
    'en-GB-female': 'en-GB-SoniaNeural',
    'en-GB-male': 'en-GB-RyanNeural',
    'zh-CN-female': 'zh-CN-XiaoxiaoNeural',
    'zh-CN-male': 'zh-CN-YunjianNeural',
}

# 可用的gTTS语言映射
GTTS_LANG_MAP = {
    'en-US-female': 'en',
    'en-US-male': 'en',
    'en-GB-female': 'en-uk',
    'en-GB-male': 'en-uk',
    'zh-CN-female': 'zh-cn',
    'zh-CN-male': 'zh-cn',
}

async def generate_audio(text, voice, speed=1.0):
    """使用Edge TTS生成音频文件"""
    # 调整语速参数
    if speed != 1.0:
        voice_with_speed = f"{voice}<prosody rate='{speed}'>"
        text_with_speed = f"{text}</prosody>"
    else:
        voice_with_speed = voice
        text_with_speed = text
        
    communicate = edge_tts.Communicate(text_with_speed, voice_with_speed)
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    # 生成音频文件
    await communicate.save(temp_filename)
    
    return temp_filename

def generate_audio_pyttsx3(text, voice_type):
    """使用pyttsx3生成音频文件"""
    engine = pyttsx3.init()
    
    # 设置语音属性
    voices = engine.getProperty('voices')
    
    # 打印可用的声音列表，用于调试
    print(f"可用的声音列表: {len(voices)}")
    for i, voice in enumerate(voices):
        print(f"Voice {i}: {voice.id} - {voice.name}")
    
    # 根据voice_type设置语音
    if voice_type.startswith('en-US'):
        # 尝试找到美式英语声音
        for voice in voices:
            if 'en_US' in voice.id.lower():
                engine.setProperty('voice', voice.id)
                print(f"选择美式英语声音: {voice.id}")
                break
    elif voice_type.startswith('en-GB'):
        # 尝试找到英式英语声音
        for voice in voices:
            if 'en_GB' in voice.id.lower():
                engine.setProperty('voice', voice.id)
                print(f"选择英式英语声音: {voice.id}")
                break
    elif voice_type.startswith('zh-CN'):
        # 尝试找到中文声音
        for voice in voices:
            if 'zh_CN' in voice.id.lower() or 'chinese' in voice.id.lower():
                engine.setProperty('voice', voice.id)
                print(f"选择中文声音: {voice.id}")
                break
    
    # 设置语速和音量
    engine.setProperty('rate', 150)  # 语速
    engine.setProperty('volume', 1.0)  # 音量
    
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        print(f"创建临时文件: {temp_filename}")
        
        # 生成音频文件
        engine.save_to_file(text, temp_filename)
        engine.runAndWait()
        
        # 验证文件是否生成成功
        if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
            print(f"音频文件生成成功: {temp_filename}, 大小: {os.path.getsize(temp_filename)} 字节")
            return temp_filename
        else:
            print(f"音频文件生成失败或为空: {temp_filename}")
            raise Exception("音频文件生成失败或为空")
    except Exception as e:
        print(f"生成音频文件时出错: {str(e)}")
        raise e

def generate_audio_gtts(text, voice_type, speed=1.0):
    """使用Google TTS生成音频文件"""
    # 获取对应的语言代码
    lang = GTTS_LANG_MAP.get(voice_type, 'en')
    
    try:
        # 检查文本是否为空
        if not text or text.strip() == '':
            raise ValueError("文本内容不能为空")
            
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        print(f"创建临时文件: {temp_filename}")
        
        # 生成音频文件
        # gTTS不直接支持速度调整，但可以设置slow参数
        slow = False
        if speed < 0.8:
            slow = True
        
        # 添加重试机制
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                tts = gTTS(text=text, lang=lang, slow=slow)
                tts.save(temp_filename)
                
                # 验证文件是否生成成功并且大小合理
                if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 100:  # 确保文件大小至少100字节
                    print(f"音频文件生成成功: {temp_filename}, 大小: {os.path.getsize(temp_filename)} 字节")
                    success = True
                else:
                    print(f"音频文件生成失败或大小异常: {temp_filename}, 大小: {os.path.getsize(temp_filename)} 字节")
                    retry_count += 1
                    time.sleep(0.5)  # 等待500毫秒后重试
            except Exception as e:
                print(f"gTTS生成音频失败 (尝试 {retry_count+1}/{max_retries}): {str(e)}")
                retry_count += 1
                if retry_count >= max_retries:
                    os.unlink(temp_filename)
                    raise Exception(f"gTTS生成音频失败，已重试{max_retries}次: {str(e)}")
                time.sleep(0.5)  # 等待500毫秒后重试
        
        if success:
            return temp_filename
        else:
            os.unlink(temp_filename)
            raise Exception("音频文件生成失败，已达到最大重试次数")
    except Exception as e:
        print(f"生成音频文件时出错: {str(e)}")
        raise e

@csrf_exempt
def text_to_speech(request):
    """将文本转换为语音"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            voice_key = data.get('voice', 'en-US-female')
            engine = data.get('engine', 'edge-tts')  # 默认使用edge-tts
            speed = float(data.get('speed', 1.0))    # 获取速度参数，默认为1.0
            
            print(f"收到TTS请求: text={text}, voice={voice_key}, engine={engine}, speed={speed}")
            
            # 检查文本是否为空
            if not text or text.strip() == '':
                return JsonResponse({'success': False, 'message': '文本内容不能为空'}, status=400)
            
            audio_path = None
            try:
                if engine == 'edge-tts':
                    # 获取对应的语音
                    voice = VOICE_OPTIONS.get(voice_key, VOICE_OPTIONS['en-US-female'])
                    
                    # 异步生成音频
                    audio_path = asyncio.run(generate_audio(text, voice, speed))
                    content_type = 'audio/mpeg'
                elif engine == 'chat-tts':
                    # 使用Google TTS生成音频
                    audio_path = generate_audio_gtts(text, voice_key, speed)
                    content_type = 'audio/mpeg'
                else:
                    return JsonResponse({'success': False, 'message': '不支持的引擎类型'}, status=400)
            except Exception as e:
                print(f"生成音频时出错: {str(e)}")
                return JsonResponse({'success': False, 'message': f'生成音频时出错: {str(e)}'}, status=500)
            
            # 读取音频文件
            try:
                if not audio_path or not os.path.exists(audio_path):
                    raise Exception("音频文件不存在")
                    
                with open(audio_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                
                # 检查音频数据
                if len(audio_data) == 0:
                    raise Exception("音频数据为空")
                
                print(f"音频文件读取成功: {audio_path}, 大小: {len(audio_data)} 字节")
                
                # 删除临时文件
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    print(f"删除临时文件失败: {str(e)}")
                
                # 返回音频数据
                response = HttpResponse(audio_data, content_type=content_type)
                response['Content-Disposition'] = 'attachment; filename="speech.mp3"'
                return response
            except Exception as e:
                print(f"读取或处理音频文件时出错: {str(e)}")
                # 尝试删除临时文件
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.unlink(audio_path)
                    except:
                        pass
                return JsonResponse({'success': False, 'message': f'读取或处理音频文件时出错: {str(e)}'}, status=500)
            
        except json.JSONDecodeError:
            print("JSON解析错误")
            return JsonResponse({'success': False, 'message': 'JSON解析错误'}, status=400)
        except Exception as e:
            print(f"处理TTS请求时出错: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': '只支持POST请求'}, status=405)

def get_voice_options(request):
    """获取可用的语音选项"""
    return JsonResponse({
        'success': True,
        'voices': {k: {'name': v, 'description': k.replace('-', ' ')} for k, v in VOICE_OPTIONS.items()}
    })
