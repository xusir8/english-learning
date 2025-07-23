
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import argparse
import os
import base64
import json
import urllib.parse
from typing import Optional

class MinimaxTTS:
    def __init__(self):
        # 默认值，仅在配置文件不存在时使用
        self.group_id = ""
        self.api_key = ""
        
        # 尝试从配置文件加载
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.local', 'minimaxi.json')
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.group_id = config.get('group_id', '')
                    self.api_key = config.get('api_key', '')
                    print(f"已从配置文件加载API凭据")
            else:
                print(f"警告: 配置文件 {config_file} 不存在，请创建该文件并添加group_id和api_key")
        except Exception as e:
            print(f"加载配置文件时出错: {str(e)}")
        
        if not self.group_id or not self.api_key:
            print("错误: group_id或api_key未设置，请检查配置文件")
        
        self.url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={self.group_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_audio(self, 
                      text: str, 
                      output_file: str, 
                      voice_id: str = "English_Gentle-voiced_man", 
                      speed: float = 0.8,
                      format: str = "wav") -> bool:
        """
        生成音频文件
        
        参数:
            text: 要转换为语音的文本
            output_file: 输出文件路径
            voice_id: 声音ID，默认为英语男声
            speed: 语速，默认为0.8
            format: 输出格式，默认为wav
            
        返回:
            bool: 是否成功生成音频
        """
        payload = {
            "model": "speech-02-hd",
            "text": text,
            "timber_weights": [
                {
                    "voice_id": voice_id,
                    "weight": 1
                }
            ],
            "voice_setting": {
                "voice_id": "",
                "speed": speed,
                "pitch": 0,
                "vol": 1,
                "emotion": "neutral",
                "latex_read": False
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": format,
                "channel": 1
            },
            "language_boost": "English"
        }
        
        try:
            print(f"正在为文本 '{text}' 生成音频...")
            
            # 设置超时时间
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "data" in data and "audio" in data["data"]:
                        # 获取音频数据（十六进制字符串）
                        audio_hex = data["data"]["audio"]
                        
                        # 处理可能的URL编码
                        if '%' in audio_hex:
                            audio_hex = urllib.parse.unquote(audio_hex)
                        
                        try:
                            # 将十六进制字符串转换为字节
                            audio_data = bytes.fromhex(audio_hex)
                            
                            # 确保输出目录存在
                            output_dir = os.path.dirname(output_file)
                            if output_dir and not os.path.exists(output_dir):
                                os.makedirs(output_dir)
                            
                            # 写入音频文件
                            with open(output_file, "wb") as f:
                                f.write(audio_data)
                            
                            print(f"音频已保存到: {output_file}")
                            return True
                        except Exception as e:
                            print(f"处理音频数据时出错: {str(e)}")
                            return False
                    else:
                        error_msg = "API返回数据中没有音频内容"
                        if "error" in data:
                            error_msg += f": {data['error']}"
                        print(error_msg)
                        return False
                except Exception as e:
                    print(f"处理API响应时出错: {str(e)}")
                    return False
            elif response.status_code == 429:
                print(f"API请求频率限制，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                raise Exception("API请求频率限制，请稍后重试")
            elif response.status_code == 401 or response.status_code == 403:
                print(f"API认证失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                raise Exception("API认证失败，请检查API密钥")
            else:
                print(f"API请求失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                raise Exception(f"API请求失败: {response.text}")
            
            return False
        except requests.exceptions.Timeout:
            print(f"API请求超时")
            raise Exception("API请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            print(f"API连接错误")
            raise Exception("API连接错误，请检查网络")
        except Exception as e:
            print(f"生成音频时出错: {str(e)}")
            raise
    
    def generate_audio_from_file(self, 
                               input_file: str, 
                               output_dir: str, 
                               voice_id: str = "English_Gentle-voiced_man",
                               speed: float = 0.8,
                               format: str = "wav") -> int:
        """
        从文件中读取文本并生成音频文件
        
        参数:
            input_file: 输入文本文件路径
            output_dir: 输出目录
            voice_id: 声音ID
            speed: 语速
            format: 输出格式
            
        返回:
            int: 成功生成的音频文件数量
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 创建输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            success_count = 0
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:  # 跳过空行
                    continue
                
                # 创建输出文件名 - 使用安全的文件名
                safe_name = ''.join(c if c.isalnum() or c in '_- ' else '_' for c in line)
                safe_name = safe_name.replace(' ', '_')[:20]
                output_file = os.path.join(output_dir, f"{i+1}_{safe_name}.{format}")
                
                # 生成音频
                if self.generate_audio(line, output_file, voice_id, speed, format):
                    success_count += 1
            
            return success_count
        except Exception as e:
            print(f"从文件生成音频时出错: {str(e)}")
            return 0

def create_filename_from_text(text: str) -> str:
    """
    根据文本内容创建安全的文件名
    
    参数:
        text: 文本内容
        
    返回:
        str: 安全的文件名
    """
    # 移除特殊字符，保留字母、数字、空格、下划线和连字符
    safe_name = ''.join(c if c.isalnum() or c in '_- ' else '_' for c in text)
    # 将空格替换为下划线
    safe_name = safe_name.replace(' ', '_')
    # 限制文件名长度，避免过长
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    return safe_name

def main():
    parser = argparse.ArgumentParser(description='将文本转换为语音')
    parser.add_argument('--text', type=str, help='要转换的文本')
    parser.add_argument('--file', type=str, help='包含多行文本的输入文件')
    parser.add_argument('--output', type=str, required=True, help='输出文件或目录')
    parser.add_argument('--voice', type=str, default='English_Gentle-voiced_man', help='声音ID')
    parser.add_argument('--speed', type=float, default=0.8, help='语速')
    parser.add_argument('--format', type=str, default='wav', help='输出格式')
    
    args = parser.parse_args()
    
    if not args.text and not args.file:
        parser.error("必须提供 --text 或 --file 参数")
    
    tts = MinimaxTTS()
    
    if args.text:
        # 单个文本转换
        output_path = args.output
        
        # 检查输出路径是否是目录
        if os.path.isdir(output_path) or output_path.endswith('/') or output_path.endswith('\\'):
            # 确保目录存在
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            
            # 根据文本内容生成文件名
            filename = create_filename_from_text(args.text) + ".wav"
            output_path = os.path.join(output_path, filename)
        
        tts.generate_audio(args.text, output_path, args.voice, args.speed, args.format)
    elif args.file:
        # 从文件批量转换
        count = tts.generate_audio_from_file(args.file, args.output, args.voice, args.speed, args.format)
        print(f"成功生成 {count} 个音频文件")

if __name__ == "__main__":
    main() 