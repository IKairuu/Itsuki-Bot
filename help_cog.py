import discord
from discord.ext import commands
import random, json

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("quotes.json", "r", encoding="utf-8") as json_file:
            self.quotes = json.load(json_file) 
        
    @commands.command(name="help", help="Display commands")
    async def show_commands(self, ctx):
        help_message = f"""
        {str(self.quotes["help_quotes"][random.randint(0, len(self.quotes["help_quotes"])-1)])}
        ```
        COMMANDS:
        &help - display commands
        &talk - the bot will state a quote in the voice channel
        &leave - the bot will disconnect to the voice channel
        &quiz <# of questions> - the bot will input the questions with answers
        &clear - Clears the list of questions
        &restart - Restart the quiz
        &ask - asks questions to a bot
        &speak - text-to-voice bot speech
        &about - Developer Information
        ```
        """
        await ctx.send(help_message)
