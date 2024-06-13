import gradio as gr
import uuid
import time
from io import BytesIO
import base64
from loguru import logger
from controller import Controller
from status import GameStatus, BattleResult
from langchain.schema import AIMessage, HumanMessage


controller = Controller()

def format_history(history, message):
    history_langchain_format = []
    for human, ai in history:
        history_langchain_format.append(HumanMessage(content=human))
        history_langchain_format.append(AIMessage(content=ai))
    history_langchain_format.append(HumanMessage(content=message))
    return history_langchain_format

def submit_choice_event(session, option):
    if option == []:
        return None
    logger.info("player options: {}".format(option))
    try:
        ## 取出option中: 前的数字id
        optionId = option.split(":")[0]
        # 转为int
        optionId = int(optionId)
    except:
        optionId = None
        logger.error("optionId is not int: {}".format(optionId))

    return get_event_result(session, optionId)

def get_event_result(session, optionId):
    if optionId is None:
        return None
    try:
        logger.info("optionId: {}", optionId)
        controller.update_resource(session, optionId)
        option = controller.get_event_option(session, optionId)
        if option is None:
            logger.error("get_event_option failed: {}", optionId)
            return None
        return controller.get_event_option(session, optionId)["result"]
    except:
        logger.error("get_event_option failed: {}", optionId)
        return None

def get_battle_result(session, optionId):
    if optionId is None:
        return None
    try:
        logger.info("optionId: {}", optionId)
        battle_result, msg = controller.update_battle_status(session, optionId)
        logger.info("battle_result: {}", battle_result)
        logger.info("msg: {}", msg)

        return battle_result, msg
    except Exception as e:
        logger.error("get_battle_result failed: {}, error:{}", optionId, e)
        return None, ""

def submit_characterInteraction_event(session, history):
    langchain_format = format_history(history, "")
    try:
        optionId = controller.referee_judge(session, langchain_format)
    except:
        logger.error("referee failed")
        return "你道别后重新出发，未收获特别的资源"
    result = get_event_result(session, optionId)
    if  result is None:
        return "你道别后重新出发，未收获特别的资源"
    return result

def submit_battle_event(session, option):
    if option == []:
        return None
    logger.info("player options: {}".format(option))
    try:
        ## 取出option中: 前的数字id
        optionId = option.split(":")[0]
        # 转为int
        optionId = int(optionId)
    except:
        optionId = None
        logger.error("optionId is not int: {}".format(optionId))

    battle_result, msg = get_battle_result(session, optionId)
    return battle_result, msg

def submit(session, option, history):
    logger.info("session: {}, option: {}".format(session, option))
    event = controller.get_event(session)
    if event is None:
        return None, GameStatus.NOT_START
    event_type = event.get_type()
    ## 根据事件类型进行分类处理
    next_game_status = GameStatus.EVENT_END
    result = ""
    match event_type:
        case "choice":
            if option == None:
                return None, GameStatus.EVENT_GOING
            result = submit_choice_event(session, option)
        case "characterInteraction":
            result = submit_characterInteraction_event(session,  history)
        case "battle":
            if option == None:
                return None, GameStatus.EVENT_GOING
            battle_result, msg = submit_battle_event(session, option)
            if battle_result == BattleResult.PLAYER_WIN:
                result = msg
                next_game_status = GameStatus.EVENT_END
            if battle_result == BattleResult.RESOURCE_NOT_ENOUGH:
                result = msg
                next_game_status = GameStatus.EVENT_GOING
            if battle_result == BattleResult.ENEMY_WIN:
                result = msg
                next_game_status = GameStatus.EVENT_END
            if battle_result == BattleResult.NOT_FINISHED:
                result = msg
                next_game_status = GameStatus.EVENT_GOING
        case _:
            result = None
    return result, next_game_status


def start(session, chatbot, chatbot_history):
    logger.info("session: {}".format(session))
    game_clear_text =  "恭喜！你已完成所有探险事件！"
    old = controller.get_event(session)
    old_event_type = None
    tts_text = ""
    if old is not None:
        old_event_type = controller.get_event(session).get_type()
    ret = controller.update_event(session)
    if not ret:
        logger.info("No more event")
        return game_clear_text, None, chatbot, chatbot_history, game_clear_text
    event = controller.get_event(session).get_content()
    if event is None:
        logger.error("No event")
        return game_clear_text, None, chatbot, chatbot_history, game_clear_text
    logger.info("event: {}".format(event))
    ec = event["eventContent"]
    tts_text = ec
    new_event_type = controller.get_event(session).get_type()
    logger.info("old_event_type: {}", old_event_type)
    logger.info("now event type: {}", new_event_type)
    if old_event_type != None:
        # 非角色事件切换到角色事件
        if old_event_type != "characterInteraction" and new_event_type == "characterInteraction":
            chatbot_history = chatbot
            self_introduction = controller.get_event(session).get_self_introduction()
            chatbot = [["", self_introduction]]
            tts_text = tts_text + "\n" + self_introduction
        # 角色事件切换到非角色事件
        if old_event_type == "characterInteraction" and new_event_type != "characterInteraction":
            chatbot = chatbot_history
        # 角色事件切换到角色事件
        if old_event_type == "characterInteraction" and new_event_type == "characterInteraction":
            self_introduction = controller.get_event(session).get_self_introduction()
            chatbot = [["", self_introduction]]
            tts_text = tts_text + "\n" + self_introduction
    elif new_event_type == "characterInteraction":
        self_introduction = controller.get_event(session).get_self_introduction()
        chatbot = [["", self_introduction]]
        tts_text = tts_text + "\n" + self_introduction
    options = event["eventOptions"]
    str_options = [f"{option['optionId']}: {option['optionContent']}" for option in options]
    if new_event_type == "characterInteraction":
        str_options = []
    logger.info("content: {}".format(ec))
    logger.info("options: {}".format(str_options))
    radio = gr.Radio(str_options,label="选项")
    return ec, radio, chatbot, chatbot_history, tts_text

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
def display_battle_status(session=None) -> str:
    """Return a markdown string displaying the player's status."""
    logger.info("session: {}", session)
    event = controller.get_event(session)
    if event is None:
        return None
    event_type = event.get_type()
    if event_type == "battle":
        status = controller.get_battle_status(session)
        return (
            f"### **玩家血量**: {status.get_player_hp()}  "
            f"**敌人血量**: {status.get_enemy_hp()} "
        )
def introduce():
    return (        "## 智途问答大冒险 <br /> \n"
        "### 你是一名勇敢的星际探险家，与智能AI助手小桨一同驾驶着先进的宇宙飞船，穿梭于广袤无垠的宇宙中，展开一段充满未知与挑战的探险旅程。 <br /> \n")

def generate_session_id() -> str:
    logger.info("session")
    return str(uuid.uuid4())

def display_gallery(session=None) -> str:
    logger.info("session: {}", session)
    return controller.get_gallery(session)

def event_speech(text):
    logger.info("event_speech: {}", text)
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

def coutinue(session, event_content, option, gallery, chatbot, chatbot_history):
    game_status = controller.get_game_status(session)
    event_result = ""
    tts_text = ""
    radio = None
    match game_status:
        case GameStatus.NOT_START:
            event_content, radio, chatbot, chatbot_history, tts_text = start(session, chatbot, chatbot_history)
            gallery = display_gallery(session)
            controller.set_game_status(session, GameStatus.EVENT_GOING)
        case GameStatus.EVENT_GOING:
            event_result, next_game_status = submit(session, option, chatbot)
            event = controller.get_event(session)
            if event is None:
                return None, GameStatus.NOT_START
            event_type = event.get_type()
            if event_type != "battle":
                tts_text = event_result
            controller.set_game_status(session, next_game_status)
        case GameStatus.EVENT_END:
            event_content, radio, chatbot, chatbot_history, tts_text = start(session, chatbot, chatbot_history)
            event_result = ""
            gallery = display_gallery(session)
            controller.set_game_status(session, GameStatus.EVENT_GOING)
        case GameStatus.GAME_OVER:
            pass
    return event_content, radio, gallery, chatbot, chatbot_history, event_result, tts_text

if __name__ == '__main__':
    with gr.Blocks(title='wisdom-adventure', theme=gr.themes.Soft()) as demo:
        session = gr.State(generate_session_id)
        chatbot_history = gr.State([])
        with gr.Column():
            intro = gr.Markdown(value=introduce())
            resource = gr.Markdown(label="游戏资源", value=display_status())
            battle = gr.Markdown(label="战斗状态", value=display_battle_status())
            event = gr.Textbox(label="事件内容")
            event_content_tts = gr.HTML()
            options = gr.Radio(label="选项", choices=[])
            result = gr.Textbox(label="事件结果")
            continue_button = gr.Button("行动")
            gallery = gr.Gallery(
                label="images", show_label=False, elem_id="gallery"
                , columns=[3], rows=[1], object_fit="contain", height="auto", interactive=False)
            chatbot = gr.Chatbot()
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
            tts_text = gr.Textbox(label="语音", visible=False)
            msg = gr.Textbox()
            msg.submit(bot, [session, msg, chatbot], [msg, chatbot]).then(bot_speech, [chatbot], [event_content_tts])
            continue_button.click(coutinue,[session, event, options, gallery, chatbot, chatbot_history],[event, options, gallery, chatbot, chatbot_history, result, tts_text]).then(display_battle_status, [session], [battle]).then(display_status, [session], [resource]).then(event_speech, [tts_text], [event_content_tts])
            options.input(coutinue,[session, event, options, gallery, chatbot, chatbot_history],[event, options, gallery, chatbot, chatbot_history, result, tts_text]).then(display_battle_status, [session], [battle]).then(display_status, [session], [resource]).then(event_speech, [tts_text], [event_content_tts])
            audio_text = gr.Textbox(visible=False)
            input_audio.stop_recording(asr_audio, [input_audio], [input_audio, audio_text]).then(
                bot, [session, audio_text, chatbot], [audio_text, chatbot]).then(
                    bot_speech, [chatbot], [event_content_tts])

    demo.queue().launch(server_name="0.0.0.0")
