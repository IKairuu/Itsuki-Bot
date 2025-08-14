import discord
from discord.ext import commands
import random

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.itsukiHelpQuotes = [
            "H-Huh? You need my help? W-Well… o-of course you do! I-I mean, I am reliable after all!",
            "W-Wait, don’t just throw your problems at me all of a sudden! …B-But fine. I’ll help. Just this once!",
            "Geez… You’re hopeless without me, aren’t you? …I-I’m not mad, okay?! I’ll help.",
            "Okay, okay! L-Let’s not make a big deal out of it… I’ll help, but n-not because I want to!",
            "If I don’t step in, you’ll probably just make it worse… s-so I guess I have to help!"
        ]
        
    @commands.command(name="help", help="Display commands")
    async def show_commands(self, ctx):
        help_message = f"""
        {self.itsukiHelpQuotes[random.randint(0, len(self.itsukiHelpQuotes)-1)]}
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
        ```
        """
        await ctx.send(help_message)
