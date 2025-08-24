import discord
import asyncio
import os
from discord.ext import commands
from help_cog import HelpCog
from background_cog import Background

activity = discord.Game(name="&help to interrupt Itsuki")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="&", activity=activity,intents=intents, help_command=None)

async def setup():
    await bot.add_cog(HelpCog(bot))
    await bot.add_cog(Background(bot))
        
asyncio.run(setup())
bot.run(os.getenv('TOKEN'))
