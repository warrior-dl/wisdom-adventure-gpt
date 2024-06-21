import json
import shutil
import os
import time
from gradio_client import Client

client = Client("https://be44533cee8d9d146b.gradio.live/")
my_seed = 1080
def load_event_list(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_tts_audio(text, seed, save_file):
    tmp_path = client.predict(
            text_file=text,
            num_seeds=0,
            seed=seed,
            speed=2,
            oral=1,
            laugh=0,
            bk=4,
            min_length=100,
            batch_size=3,
            temperature=0.1,
            top_P=0.7,
            top_K=20,
            roleid="1",
            refine_text=True,
            pt_file={"name":"/tmp/gradio/seed_1080_restored_emb.pt", "path":"/tmp/gradio/seed_1080_restored_emb.pt"},
            api_name="/generate_tts_audio"
    )
    ## 将tmp_path复制到save_file，调用文件系统

    shutil.copyfile(tmp_path, save_file)

event_list = load_event_list("data/event_list.json")
event_evaluate = []

for i in range(len(event_list)):
    event = event_list[i]
    content = event["eventContent"]
    id = event["id"]
    print("id:", id)
    ## 如果data/TTS中已经存在id-开头的文件，则跳过
    if not os.path.exists(f"data/TTS/{id}-content.wav"):
        try :
            generate_tts_audio(content, my_seed, f"data/TTS/{id}-content.wav")
        except Exception as e:
            print("generate tts failed: ", e)
            time.sleep(3)
    
    eventOptions = event["eventOptions"]
    for option in eventOptions:
        optionId = option["optionId"]
        result = option["result"]
        if not os.path.exists(f"data/TTS/{id}-option-{optionId}.wav"):
            try :
                generate_tts_audio(result, my_seed, f"data/TTS/{id}-option-{optionId}.wav")
            except Exception as e:
                print("generate tts failed: ", e)
                time.sleep(3)

    

