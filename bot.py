import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

print(DISCORD_TOKEN)  # ← デバッグ用、一度だけ試す

import discord
import requests
from datetime import datetime

# 環境変数
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")

# Discord設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Gemini要約関数
def summarize_with_gemini(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": f"以下の会話を簡潔な議事録にまとめてください:\n{text}"}]
        }]
    }
    res = requests.post(url, json=payload)
    data = res.json()
    if "candidates" not in data:
        return "（要約に失敗しました）"
    return data["candidates"][0]["content"]["parts"][0]["text"]

# Notion登録関数
def save_to_notion(title, summary):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            "日付": {"date": {"start": datetime.now().isoformat()}},
            "スレッド名": {"title": [{"text": {"content": title}}]},
            "要約": {"rich_text": [{"text": {"content": summary}}]}
        }
    }
    requests.post(url, headers=headers, json=payload)

# マーカー検知
@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.strip() == "/end":
        channel = message.channel
        messages = []
        async for m in channel.history(limit=50):
            if not m.content.startswith("/end"):
                messages.append(f"{m.author.display_name}: {m.content}")
        conversation = "\n".join(reversed(messages))

        summary = summarize_with_gemini(conversation)
        save_to_notion(channel.name, summary)

        await channel.send("✅ 議事録をNotionに保存しました！")

client.run(DISCORD_TOKEN)