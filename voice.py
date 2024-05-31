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

    def get_tts(self, text):
        inp = appbuilder.Message(content={"text": text})
        out = self.tts.run(message=inp, person=4)
        return out.content["audio_binary"]
    
    def get_asr(self, audio):
        asr = appbuilder.ASR()
        # 生成临时文件名
        temp_file = str(uuid.uuid4()) + ".wav"
        wavfile = os.path.join(os.getcwd(), "temp", temp_file)
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
