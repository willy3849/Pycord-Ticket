import discord
from discord.ext import commands
import os
import datetime
from func.loadConfig import DISCORD_TOKEN, COMMAND_PREFIX

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all())

for file in os.listdir("cogs"):
    if file.endswith(".py") and not file.startswith("_"):
        cog_name=file[:-3]
        try:
            bot.load_extension(f'cogs.{cog_name}')
            print(f"Loaded extension 'cogs.{cog_name}' successfully.")
        except Exception as e:
            print(f"Failed to load extension cogs.{cog_name}.")
            current_time = datetime.datetime.now()
            filename = f"{current_time.strftime('%Y%m%d_%H%M%S')}.txt"
            log_path=os.path.join("logs", filename)
            with open(log_path, "w", encoding="utf-8")as file:
                file.write(str(e))

@bot.event
async def on_ready():
    print("==========================================")
    print(f"Bot Name    : {bot.user.name}")
    print(f"Bot ID      : {bot.user.id}")
    print("Status      : Ready and running!")
    print("------------------------------------------")
    print("Created by Yi3849")
    print("GitHub: https://github.com/willy3849")
    print("Please set .env first before using")
    print("==========================================")

bot.run(DISCORD_TOKEN)