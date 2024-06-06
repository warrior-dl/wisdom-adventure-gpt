import gradio as gr
import uuid
import time
from io import BytesIO
import base64
from loguru import logger
from controller import Controller
from langchain.schema import AIMessage, HumanMessage


controller = Controller()

def format_history(history, message):
    history_langchain_format = []
    for human, ai in history:
        history_langchain_format.append(HumanMessage(content=human))
        history_langchain_format.append(AIMessage(content=ai))
    history_langchain_format.append(HumanMessage(content=message))
    return history_langchain_format

def submit(session, option, history):
    logger.info("session: {}, option: {}".format(session, option))
    event = controller.get_event(session)
    if event is not None and event.get_type() == "characterInteraction":
        langchain_format = format_history(history, "")
        try:
            optionId = controller.referee_judge(session, langchain_format)
        except:
            logger.error("referee failed")
            optionId = None
    else:
        if option == []:
            return None, display_status(session)
        logger.info("player options: {}".format(option))
        try:
            ## 取出option中: 前的数字id
            optionId = option.split(":")[0]
            # 转为int
            optionId = int(optionId)
        except:
            optionId = None
            logger.error("optionId is not int: {}".format(optionId))
    if optionId is None:
        return None, display_status(session)

    try:
        logger.info("optionId: {}".format(optionId))
        controller.update_resource(session, optionId)
        result = controller.get_event_option(session, optionId)["result"]
    except:
        result = None
        logger.error("get_event_option failed: {}", optionId)

    return result, display_status(session)


def start(session, chatbot, chatbot_history):
    logger.info("session: {}".format(session))
    old = controller.get_event(session)
    old_event_type = None
    if old is not None:
        old_event_type = controller.get_event(session).get_type()
    ret = controller.update_event(session)
    if not ret:
        logger.info("No more event")
        return "恭喜！你已完成所有探险事件！", None, chatbot, chatbot_history
    event = controller.get_event(session).get_content()
    if event is None:
        logger.error("No event")
        return "恭喜！你已完成所有探险事件！", None, chatbot, chatbot_history
    logger.info("event: {}".format(event))
    new_event_type = controller.get_event(session).get_type()
    logger.info("old_event_type: {}", old_event_type)
    logger.info("now event type: {}", new_event_type)
    if old_event_type != None:
        # 非角色事件切换到角色事件
        if old_event_type != "characterInteraction" and new_event_type == "characterInteraction":
            chatbot_history = chatbot
            chatbot = []
        # 角色事件切换到非角色事件
        if old_event_type == "characterInteraction" and new_event_type != "characterInteraction":
            chatbot = chatbot_history
        # 角色事件切换到角色事件
        if old_event_type == "characterInteraction" and new_event_type == "characterInteraction":
            chatbot = []

    options = event["eventOptions"]
    str_options = [f"{option['optionId']}: {option['optionContent']}" for option in options]
    if new_event_type == "characterInteraction":
        str_options = []
    logger.info("content: {}".format(event["eventContent"]))
    logger.info("options: {}".format(str_options))
    radio = gr.Radio(str_options,label="选项")
    return event["eventContent"], radio, chatbot, chatbot_history

def clear_result():
    return ""

def bot(session, message, history):
    history_langchain_format = format_history(history, message)
    logger.info("history_langchain_format: {}", history_langchain_format)
    gpt_response = controller.chat(history_langchain_format, session)
    history = history + [[message, None]]
    history[-1][1] = ""
    for chunk in gpt_response:
        logger.info("chunk: {}", chunk)
        history[-1][1] += chunk
        time.sleep(0.05)
        yield "", history

def add_text(history, text, chatbot):
    history = history + [(text, None)]
    return history, ""

def display_status(session=None) -> str:
    """Return a markdown string displaying the player's status."""
    logger.info("session: {}", session)
    status = controller.get_resource(session)
    return (
        "## 游戏资源 <br /> \n"
        f"### **星际货币**: {status.stellarCurrency}  "
        f"**飞船能量**: {status.shipEnergy} "
        f"**探索能力**: {status.explorationCapability} "
        f"**声誉值**: {status.reputationValue}"
    )
def introduce():
    return (        "## 智途问答大冒险 <br /> \n"
        "### 你是一名勇敢的星际探险家，与智能AI助手小桨一同驾驶着先进的宇宙飞船，穿梭于广袤无垠的宇宙中，展开一段充满未知与挑战的探险旅程。 <br /> \n")

def generate_session_id() -> str:
    logger.info("session")
    return str(uuid.uuid4())

def event_speech(text):
    if text == "" or text is None:
        return None
    tts = controller.get_tts(text)

    audio_bytes = BytesIO(tts)
    audio = base64.b64encode(audio_bytes.read()).decode("utf-8")
    audio_player = f'<audio src="data:audio/mpeg;base64,{audio}" controls autoplay></audio>'

    return audio_player

def bot_speech(history):
    logger.info("history: {}", history)
    if history == []:
        return None
    text = history[-1][1]
    logger.info("text: {}", text)
    tts = controller.get_tts(text)

    audio_bytes = BytesIO(tts)
    audio = base64.b64encode(audio_bytes.read()).decode("utf-8")
    audio_player = f'<audio src="data:audio/mpeg;base64,{audio}" controls autoplay></audio>'

    return audio_player

def chat_with_audio(file_path, chatbot):
    logger.info("file_path: {}", file_path)
    logger.info("chatbot: {}", chatbot)
    return chatbot

def asr_audio(audio):
    logger.info("audio: {}", audio)
    asr = controller.get_asr(audio)
    logger.info("asr: {}", asr["result"])
    return None, asr["result"][0]

if __name__ == '__main__':
    with gr.Blocks(title='wisdom-adventure', theme=gr.themes.Soft()) as demo:
        session = gr.State(generate_session_id)
        chatbot_history = gr.State([])
        with gr.Column():
            intro = gr.Markdown(value=introduce())
            resource = gr.Markdown(label="游戏资源", value=display_status())
            start_button = gr.Button("出发")
            event = gr.Textbox(label="事件内容")
            event_content_tts = gr.HTML()
            options = gr.Radio(label="选项", choices=[])
            submit_button = gr.Button("提交")
            result = gr.Textbox(label="事件结果")
            # event_result_tts = gr.HTML()
            input_audio = gr.Audio(
                sources=["microphone"],
                waveform_options=gr.WaveformOptions(
                    waveform_color="#01C6FF",
                    waveform_progress_color="#0066B4",
                    skip_length=2,
                    show_controls=False,
                ),
                type="filepath",
            )
            chatbot = gr.Chatbot()
            msg = gr.Textbox()
            msg.submit(bot, [session, msg, chatbot], [msg, chatbot]).then(bot_speech, [chatbot], [event_content_tts])
            submit_button.click(submit,[session, options, chatbot],[result, resource]).then(event_speech, [result], [event_content_tts])
            start_button.click(start,[session, chatbot, chatbot_history],[event, options, chatbot, chatbot_history]).then(clear_result, [], [result]).then(event_speech, [event], [event_content_tts])
            audio_text = gr.Textbox(visible=False)
            input_audio.stop_recording(asr_audio, [input_audio], [input_audio, audio_text]).then(
                bot, [session, audio_text, chatbot], [audio_text, chatbot]).then(
                    bot_speech, [chatbot], [event_content_tts])

    demo.queue().launch(server_name="0.0.0.0")
