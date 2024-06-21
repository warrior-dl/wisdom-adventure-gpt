import os
import appbuilder
import myKeys
import numpy as np
import librosa
import requests
import wave
import uuid
import soundfile as sf
from loguru import logger

class Voice:
    def __init__(self):
        os.environ["APPBUILDER_TOKEN"] =  myKeys.APPBUILDER_TOKEN
        self.tts = appbuilder.TTS()
        ## 创建temp文件夹
        if not os.path.exists("temp"):
            os.mkdir("temp")

    def get_tts(self, text) -> tuple[str, float]:
        if text == "" or text is None:
            return None, None
        logger.info("voice get tts: {}", text)
        inp = appbuilder.Message(content={"text": text})
        try:
            out = self.tts.run(message=inp, person=4, audio_type="wav")
            temp_file = str(uuid.uuid4()) + ".wav"
            wav_path =  os.path.join("temp", temp_file)
            with open(wav_path, "wb") as f:
                f.write(out.content["audio_binary"])
            # 获取wav文件音频时长
            with wave.open(wav_path, 'rb') as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
            # 加0.5秒停顿
            return wav_path, duration + 0.5
        except Exception as e:
            logger.error("tts error: {}", e)
            return None, None
    
    def get_asr(self, audio):
        asr = appbuilder.ASR()
        # 生成临时文件名
        temp_file = str(uuid.uuid4()) + ".wav"
        wavfile = os.path.join("temp", temp_file)
        self.resample_rate(audio, wavfile)
        # 读取音频文件
        raw_audio = open(wavfile, "rb").read()
        os.remove(wavfile)
        # 准备数据
        content_data = {"audio_format": "wav", "raw_audio": raw_audio, "rate": 16000}
        msg = appbuilder.Message(content_data)
        # 识别语音
        out = asr.run(msg)
        logger.info("asr restult:{}", out.content)
        return out.content

    def resample_rate(self, path, new_path, new_sample_rate = 16000):
        signal, sr = librosa.load(path, sr=None)
        new_signal = librosa.resample(signal, orig_sr=sr, target_sr=new_sample_rate) 
        sf.write(new_path, new_signal, new_sample_rate)
