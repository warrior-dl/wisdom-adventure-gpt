import gradio as gr
import uuid
import time
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

def submit_choice_event(session, optionId):
    if optionId is None:
        return None
    logger.info("player optionId: {}".format(optionId))

    return settle_event_result(session, optionId)

def settle_event_result(session, optionId):
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
        optionId, result = controller.referee_judge(session, langchain_format)
        settle_event_result(session, optionId)
    except:
        logger.error("referee failed")
        return "你道别后重新出发，未收获特别的资源"
    if  result is None:
        return "你道别后重新出发，未收获特别的资源"
    return result

def submit_battle_event(session, optionId):
    battle_result, msg = get_battle_result(session, optionId)
    return battle_result, msg

def submit(session, optionId, history):
    logger.info("session: {}, optionId: {}".format(session, optionId))
    event = controller.get_event(session)
    if event is None:
        return None, GameStatus.NOT_START
    event_type = event.get_type()
    ## 根据事件类型进行分类处理
    next_game_status = GameStatus.EVENT_END
    result = ""
    match event_type:
        case "choice":
            if optionId == None:
                return None, GameStatus.EVENT_GOING
            result = submit_choice_event(session, optionId)
        case "characterInteraction":
            result = submit_characterInteraction_event(session,  history)
        case "battle":
            if optionId == None:
                return None, GameStatus.EVENT_GOING
            battle_result, msg = submit_battle_event(session, optionId)
            if battle_result == BattleResult.PLAYER_WIN:
                result = msg
                next_game_status = GameStatus.EVENT_END
            if battle_result == BattleResult.RESOURCE_NOT_ENOUGH:
                result = msg
                next_game_status = GameStatus.EVENT_GOING
            if battle_result == BattleResult.ENEMY_WIN:
                result = msg
                next_game_status = GameStatus.GAME_OVER
            if battle_result == BattleResult.NOT_FINISHED:
                result = msg
                next_game_status = GameStatus.EVENT_GOING
        case _:
            result = None
    return result, next_game_status


def start(session, chatbot, chatbot_history):
    logger.info("session: {}".format(session))
    next_game_status = GameStatus.EVENT_GOING
    game_clear_text =  "恭喜！你已通关！"
    old = controller.get_event(session)
    old_event_type = None
    tts_text = ""
    if old is not None:
        old_event_type = controller.get_event(session).get_type()
    ret = controller.update_event(session)
    if not ret:
        logger.info("game end")
        next_game_status = GameStatus.GAME_OVER
        return game_clear_text, None, chatbot, chatbot_history, game_clear_text, next_game_status
    event = controller.get_event(session).get_content()
    if event is None:
        logger.error("No event")
        next_game_status = GameStatus.GAME_OVER
        return game_clear_text, None, chatbot, chatbot_history, game_clear_text, next_game_status
    logger.info("event: {}".format(event))
    tts_text = ""
    new_event_type = controller.get_event(session).get_type()
    logger.info("old_event_type: {}", old_event_type)
    logger.info("now event type: {}", new_event_type)
    if old_event_type != None:
        # 非角色事件切换到角色事件
        if old_event_type != "characterInteraction" and new_event_type == "characterInteraction":
            chatbot_history = chatbot
            self_introduction = controller.get_event(session).get_self_introduction()
            chatbot = [["", self_introduction]]
            tts_text =  self_introduction
        # 角色事件切换到非角色事件
        if old_event_type == "characterInteraction" and new_event_type != "characterInteraction":
            chatbot = chatbot_history
        # 角色事件切换到角色事件
        if old_event_type == "characterInteraction" and new_event_type == "characterInteraction":
            self_introduction = controller.get_event(session).get_self_introduction()
            chatbot = [["", self_introduction]]
            tts_text =  self_introduction
    elif new_event_type == "characterInteraction":
        self_introduction = controller.get_event(session).get_self_introduction()
        chatbot = [["", self_introduction]]
        tts_text = self_introduction
    options = event["eventOptions"]
    str_options = [f"{option['optionId']}: {option['optionContent']}" for option in options]
    if new_event_type == "characterInteraction":
        str_options = []
    logger.info("options: {}".format(str_options))
    radio = gr.Radio(str_options,label="选项")
    return event["eventContent"], radio, chatbot, chatbot_history, tts_text, next_game_status


def bot(session, message, history, settings):
    history_langchain_format = format_history(history, message)
    logger.info("history_langchain_format: {}", history_langchain_format)
    logger.debug("settings: {}", settings)
    if "语音播放" in settings:
        gpt_response = controller.chat_and_speech(history_langchain_format, session)
    else:
        gpt_response = controller.chat(history_langchain_format, session)
    history = history + [[message, None]]
    history[-1][1] = ""
    for chunk in gpt_response:
        history[-1][1] += chunk
        time.sleep(0.05)
        yield "", history

# 问题推荐
def create_question(session, history):
    if history == []:
        return []
    langchain_format = format_history(history, "")
    try:
        result = controller.create_question(session, langchain_format)
        logger.info("create question result: {}", result)
    except:
        logger.error("create question failed")
        return []
    return gr.Radio(result, label="问题推荐", interactive=True)

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
def display_battle_status(session) :
    """Return a markdown string displaying the player's status."""
    logger.info("session: {}", session)
    event = controller.get_event(session)
    if event is None:
        return gr.update(visible=False), None, None, None, None
    event_type = event.get_type()
    if event_type == "battle":
        status = controller.get_battle_status(session)
        enemy_hp, enemy_max = status.get_enemy_hp(), status.get_enemy_max_hp()
        player_hp, player_max_hp = status.get_player_hp(), status.get_player_max_hp()
        return gr.update(visible=True), enemy_hp, enemy_hp / enemy_max * 100, player_hp, player_hp / player_max_hp * 100
    return gr.update(visible=False), None, None, None, None
def introduce():
    return (        "## 智途问答大冒险 <br /> \n"
        "### 你是一名勇敢的星际探险家，与智能AI助手小桨一同驾驶着先进的宇宙飞船，穿梭于广袤无垠的宇宙中，展开一段充满未知与挑战的探险旅程。 <br /> \n")

def generate_session_id() -> str:
    logger.info("session")
    return str(uuid.uuid4())

def display_gallery(session=None) -> str:
    logger.info("session: {}", session)
    return controller.get_gallery(session)

def play_tts_queue(session):
    time.sleep(1)
    while True:
        tts, duration = controller.pop_tts_queue(session)
        if tts is None:
            return None
        logger.info("tts: {}", tts)
        yield tts
        time.sleep(duration)

def chat_with_audio(file_path, chatbot):
    logger.info("file_path: {}", file_path)
    logger.info("chatbot: {}", chatbot)
    return chatbot

def asr_audio(audio):
    logger.info("audio: {}", audio)
    asr = controller.get_asr(audio)
    logger.info("asr: {}", asr["result"])
    return None, asr["result"][0]

def coutinue(session, event_content, option, gallery, chatbot, chatbot_history, settings):
    game_status = controller.get_game_status(session)
    event_result = ""
    tts_text = ""
    radio = None
    enable_tts = False
    if "语音播放" in settings:
        enable_tts = True
        controller.clear_tts_queue(session)
    match game_status:
        case GameStatus.NOT_START | GameStatus.EVENT_END:
            event_content, radio, chatbot, chatbot_history, tts_text, next_game_status= start(session, chatbot, chatbot_history)
            event_result = ""
            gallery = display_gallery(session)
            controller.set_game_status(session, next_game_status)
            if enable_tts:
                event = controller.get_event(session)
                event_type = event.get_type()
                if event_type != "battle":
                    controller.push_event_content_tts(session, event.get_id())
                    controller.generate_tts(session, tts_text)
        case GameStatus.EVENT_GOING:
            try:
                ## 取出option中: 前的数字id
                optionId = option.split(":")[0]
                # 转为int
                optionId = int(optionId)
            except:
                optionId = None
                logger.warning("optionId is not int: {}".format(optionId))
            event_result, next_game_status = submit(session, optionId, chatbot)
            event = controller.get_event(session)
            if event is None:
                return None, GameStatus.NOT_START
            controller.set_game_status(session, next_game_status)
            event_type = event.get_type()
            if enable_tts:
                if event_type == "choice":
                    controller.clear_tts_queue(session)
                    controller.push_event_option_tts(session, event.get_id(), optionId)
                elif event_type == "characterInteraction":
                    controller.clear_tts_queue(session)
                    controller.generate_tts(session, event_result)
        case GameStatus.GAME_OVER:
            score = controller.calculate_score(session)
            event_content = f"游戏结束，得分：{score}"

    return event_content, radio, gallery, chatbot, chatbot_history, event_result

def display_record(session) -> str:
    record_list = controller.get_record(session)
    return "\n".join(record_list)

def display_progress(session) -> int:
    return controller.get_game_time(session)

if __name__ == '__main__':
    with open("hp.html", "r", encoding="utf-8") as f:
        hp_html = f.read()
    with open("ui.css", "r", encoding="utf-8") as f:
        css = f.read()
    with open("ui.js", "r", encoding="utf-8") as f:
        js = f.read()
    with gr.Blocks(title='wisdom-adventure', theme=gr.themes.Soft(), css=css, js=js) as demo:
        session = gr.State(generate_session_id)
        chatbot_history = gr.State([])
        intro = gr.Markdown(value=introduce())
        resource = gr.Markdown(label="游戏资源", value=display_status())
        # battle = gr.Markdown(label="战斗状态", value=display_battle_status())
        play_hp = gr.Number(elem_id="playerHp", visible=False)
        enemy_hp = gr.Number(elem_id="enemyHp", visible=False)
        play_hp_percent = gr.Number(elem_id="playerHpPercent", visible=False)
        enemy_hp_percent = gr.Number(elem_id="enemyHpPercent", visible=False)
        with gr.Row():
            with gr.Column():
                game_progress = gr.Slider(label="游戏进度", minimum=0, maximum=15, value=0, step=1)
                event = gr.Textbox(label="事件内容")
                hp = gr.HTML(value=hp_html, visible=False)
                options = gr.Radio(label="选项", choices=[])
                result = gr.Textbox(label="事件结果")
                record = gr.Textbox(label="游戏记录", interactive=False, autoscroll=True, max_lines=3)
                gallery = gr.Gallery(
                    label="images", show_label=False, elem_id="gallery"
                    , columns=[2], rows=[1], object_fit="contain", height="auto", interactive=False)
            with gr.Column():
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
                qustion_options = gr.Radio(label="问题推荐", choices=[])
                msg = gr.Textbox()
                audio_text = gr.Textbox(visible=False)
                with gr.Row():
                    event_content_tts = gr.Audio(autoplay=True)
                    settings = gr.CheckboxGroup(["语音播放"], label="设置", info="语音播放设置")
        continue_button = gr.Button("行动")
        msg.submit(bot, [session, msg, chatbot, settings], [msg, chatbot]).then(create_question, [session, chatbot], [qustion_options])
        chatbot.change(play_tts_queue, [session], [event_content_tts])
        input_audio.stop_recording(asr_audio, [input_audio], [input_audio, audio_text]).then(
                bot, [session, audio_text, chatbot, settings], [audio_text, chatbot]).then(create_question, [session, chatbot], [qustion_options])
        qo = qustion_options.input(bot, [session, qustion_options, chatbot, settings], [qustion_options, chatbot]).then(
            create_question, [session, chatbot], [qustion_options])
        continue_button.click(coutinue,[session, event, options, gallery, chatbot, chatbot_history, settings],[event, options, gallery, chatbot, chatbot_history, result]).then(
            display_battle_status, [session], [hp, enemy_hp, enemy_hp_percent, play_hp, play_hp_percent]).then(
            display_status, [session], [resource]).then(
            display_record, [session], [record]).then(
            display_progress, [session], [game_progress]).then(
            play_tts_queue, [session], [event_content_tts]).then(
            create_question, [session, chatbot], [qustion_options])
        options.input(coutinue,[session, event, options, gallery, chatbot, chatbot_history, settings],[event, options, gallery, chatbot, chatbot_history, result]).then(
            display_battle_status, [session], [hp, enemy_hp, enemy_hp_percent, play_hp, play_hp_percent]).then(
            display_status, [session], [resource]).then(
            display_record, [session], [record]).then(
            display_progress, [session], [game_progress]).then(
            play_tts_queue, [session], [event_content_tts]).then(
            create_question, [session, chatbot], [qustion_options])
            
    # demo.queue().launch(server_name="0.0.0.0", share=True, allowed_paths=["/home/aistudio/"])
    demo.queue().launch(server_name="0.0.0.0", share=True)
