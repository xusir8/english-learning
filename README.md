# Minimax TTS 文本转语音工具

这是一个使用Minimax API进行文本转语音(TTS)的Python脚本，可以将文本转换为高质量的语音文件。

## 功能特点

- 支持单个文本转换为语音
- 支持从文本文件批量生成语音文件
- 可自定义语音类型、语速和输出格式
- 自动创建输出目录
- 处理文件名安全问题

## 安装依赖

```bash
pip install requests
```

## 使用方法

### 单个文本转换

```bash
python minimax_tts.py --text "Hello world" --output hello.mp3
```

### 从文件批量转换

```bash
python minimax_tts.py --file words.txt --output audio_output
```

其中`words.txt`是一个文本文件，每行包含一个要转换的文本。

### 参数说明

- `--text`: 要转换的单个文本
- `--file`: 包含多行文本的输入文件
- `--output`: 输出文件或目录
- `--voice`: 声音ID，默认为`English_Gentle-voiced_man`
- `--speed`: 语速，默认为0.8
- `--format`: 输出格式，默认为mp3

### 可用的声音ID

- `English_Gentle-voiced_man`: 英语温和男声
- 其他声音ID可参考Minimax API文档

## 示例

```bash
# 使用默认参数转换单个文本
python minimax_tts.py --text "Hello world" --output hello.mp3

# 使用不同的声音和语速
python minimax_tts.py --text "Hello world" --output hello.mp3 --voice "English_Gentle-voiced_man" --speed 1.0

# 从文件批量转换
python minimax_tts.py --file words.txt --output audio_output
```

## 注意事项

- 需要有效的Minimax API密钥
- 网络连接正常
- 文本内容应符合Minimax API的要求 