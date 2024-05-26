import gradio as gr
from loguru import logger
from controller import Controller

controller = Controller()
def submit(option):
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
    controller.update_status(optionId)
    result = controller.get_event_option(optionId)["result"]
    return result, display_status()


def start():
    controller.update_event()
    event = controller.get_event()
    if event is None:
        logger.error("No event")
        return
    logger.info("event: {}".format(event))
    options = event["eventOptions"]
    str_options = [f"{option['optionId']}: {option['optionContent']}" for option in options]
    logger.info("content: {}".format(event["eventContent"]))
    logger.info("options: {}".format(str_options))
    radio = gr.Radio(str_options,label="选项")
    return event["eventContent"], radio

async def bot(message, history):
    logger.info("user message: {}".format(message))
    bot_message = await controller.chat_with_guider(message)
    logger.info("bot message: {}".format(bot_message))
    history.append((message, bot_message))
    return "", history
def add_text(history, text):
    history = history + [(text, None)]
    return history, ""

def display_status() -> str:
    """Return a markdown string displaying the player's status."""
    status = controller.get_status()
    return (
        "## 智途问答大冒险 <br /> \n"
        "### 你是一名勇敢的星际探险家，与智能AI助手小桨一同驾驶着先进的宇宙飞船，穿梭于广袤无垠的宇宙中，展开一段充满未知与挑战的探险旅程。 <br /> \n"
        "## 游戏资源 <br /> \n"
        f"### **星际货币**: {status.stellarCurrency}  "
        f"**飞船能量**: {status.shipEnergy} "
        f"**探索能力**: {status.explorationCapability} "
        f"**声誉值**: {status.reputationValue}"
    )

if __name__ == '__main__':
    with gr.Blocks(title='wisdom-adventure', theme=gr.themes.Soft()) as demo:
        with gr.Column():
            resource = gr.Markdown(label="游戏资源", value=display_status())
            start_button = gr.Button("出发")
            event = gr.Textbox(label="事件内容")
            options = gr.Radio(label="选项", choices=[])
            submit_button = gr.Button("提交")
            result = gr.Textbox(label="事件结果")
            chatbot = gr.Chatbot(label="小桨")
            user_input = gr.Textbox(label="用户输入")
            user_input.submit(bot, [user_input, chatbot], [user_input, chatbot])
            submit_button.click(submit,[options],[result, resource])
            start_button.click(start,[],[event, options])

    demo.queue().launch(inbrowser=True,server_name="0.0.0.0",)
