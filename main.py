from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FollowEvent, RichMenu, RichMenuArea, RichMenuBounds,
    URIAction, MessageAction, RichMenuSize
)
import os
from starlette.responses import PlainTextResponse

app = FastAPI()

# Azure App Serviceの環境変数から読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', None)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def create_rich_menu():
    # リッチメニューを作成
    rich_menu_to_create = RichMenu(
        size=RichMenuSize(width=2500, height=1686),
        selected=True,
        name="Nice rich menu",
        chat_bar_text="メニューを開く",
        areas=[
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
                action=URIAction(label='How to use', uri="https://your-domain.com/how-to-use")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=833, y=0, width=834, height=843),
                action=URIAction(label='Website', uri="https://your-domain.com")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1667, y=0, width=833, height=843),
                action=URIAction(label='Instagram', uri="https://www.instagram.com/your-account")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=843, width=2500, height=843),
                action=URIAction(label='Mobile Order', uri="https://your-domain.com/order")
            )
        ]
    )
    
    # リッチメニューを作成し、IDを取得
    rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)
    
    # リッチメニュー画像をアップロード
    with open("rich_menu_image.png", "rb") as f:
        line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", f)
    
    # デフォルトのリッチメニューとして設定
    line_bot_api.set_default_rich_menu(rich_menu_id)
    
    return rich_menu_id

@app.on_event("startup")
async def startup_event():
    # アプリケーション起動時にリッチメニューを作成
    try:
        create_rich_menu()
    except Exception as e:
        print(f"リッチメニューの作成に失敗しました: {str(e)}")

@app.get("/")
async def root():
    return PlainTextResponse("LINE Bot is running!")

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature', '')
    body = await request.body()
    body = body.decode('utf-8')
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    return PlainTextResponse('OK')

@handler.add(FollowEvent)
def handle_follow(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    welcome_message = TextSendMessage(text=f"""こんにちは、{profile.display_name}さん！
友だち追加ありがとうございます。

このBotでは以下のサービスをご利用いただけます：
・予約の確認
・営業時間の確認
・お問い合わせ

下のメニューからお選びください。""")
    
    line_bot_api.reply_message(event.reply_token, welcome_message)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    
    if text == "予約":
        reply_text = "予約はこちらから！\nhttps://your-booking-site.com"
    elif text == "営業時間":
        reply_text = "営業時間：10:00-20:00\n定休日：毎週水曜日"
    elif text == "せんば":
        reply_text = "たくみ"
    elif text == "おかざわ":
        reply_text = "みつお"
    else:
        reply_text = "ご質問は下のメニューからお選びください。"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
