import gradio as gr
import uuid
from io import BytesIO
import base64
from loguru import logger
from controller import Controller
from langchain.schema import AIMessage, HumanMessage


controller = Controller()
def submit(session, option):
    logger.info("session: {}, option: {}".format(session, option))
    if option == []:
        return
    logger.info("player options: {}".format(option))
    ## 取出option中: 前的数字id
    optionId = option.split(":")[0]
    # 转为int
    try:
        optionId = int(optionId)
    except:
        logger.error("optionId is not int: {}".format(optionId))
    controller.update_resource(session, optionId)
    result = controller.get_event_option(session, optionId)["result"]
    return result, display_status(session)


def start(session):
    logger.info("session: {}".format(session))
    ret = controller.update_event(session)
    if not ret:
        logger.info("No more event")
        return "恭喜！你已完成所有探险事件！", None
    event = controller.get_event(session).content
    if event is None:
        logger.error("No event")
        return "恭喜！你已完成所有探险事件！", None
    logger.info("event: {}".format(event))
    options = event["eventOptions"]
    str_options = [f"{option['optionId']}: {option['optionContent']}" for option in options]
    logger.info("content: {}".format(event["eventContent"]))
    logger.info("options: {}".format(str_options))
    radio = gr.Radio(str_options,label="选项")
    return event["eventContent"], radio

def bot(message, history, mic = None):
    if mic is not None:
        logger.info("mic: {}", mic)
    history_langchain_format = []
    for human, ai in history:
        history_langchain_format.append(HumanMessage(content=human))
        history_langchain_format.append(AIMessage(content=ai))
    history_langchain_format.append(HumanMessage(content=message))
    logger.info("history_langchain_format: {}", history_langchain_format)
    gpt_response = controller.chat_with_guider(history_langchain_format)
    partial_message = ""
    for chunk in gpt_response:
        logger.info("chunk: {}", chunk)
        partial_message = partial_message + chunk
        yield partial_message

def add_text(history, text):
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
    tts = controller.get_tts(text)

    audio_bytes = BytesIO(tts)
    audio = base64.b64encode(audio_bytes.read()).decode("utf-8")
    audio_player = f'<audio src="data:audio/mpeg;base64,{audio}" controls autoplay></audio>'

    return audio_player

def chat_with_audio(file_path, chatbot):
    logger.info("file_path: {}", file_path)
    logger.info("chatbot: {}", chatbot)
    return chatbot

def reverse_audio(audio):
    logger.info("audio: {}", audio)
    asr = controller.get_asr(audio)
    logger.info("asr: {}", asr)

if __name__ == '__main__':
    with gr.Blocks(title='wisdom-adventure', theme=gr.themes.Soft()) as demo:
        session = gr.State(generate_session_id)
        with gr.Column():
            intro = gr.Markdown(value=introduce())
            resource = gr.Markdown(label="游戏资源", value=display_status())
            start_button = gr.Button("出发")
            event = gr.Textbox(label="事件内容")
            event_content_tts = gr.HTML()
            options = gr.Radio(label="选项", choices=[])
            submit_button = gr.Button("提交")
            result = gr.Textbox(label="事件结果")
            event_result_tts = gr.HTML()
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
            gr.ChatInterface(bot)
            submit_button.click(submit,[session, options],[result, resource]).then(event_speech, [result], [event_result_tts])
            start_button.click(start,[session],[event, options]).then(event_speech, [event], [event_content_tts])
            input_audio.change(reverse_audio, input_audio)

    demo.queue().launch(server_name="0.0.0.0")
