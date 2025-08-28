import discord
from discord.ext import commands
import random
import os
import google.generativeai as genai
from googletrans import Translator
from elevenlabs.client import ElevenLabs
import requests, tempfile, json, asyncio

class Background(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.inVoiceChannel = False
        self.voiceLinks = []
        self.questions = []
        self.answers = []
        self.guilds = {}
        
        gemini_api_key = os.getenv("API")
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.5-pro")

        self.elevenLabs = ElevenLabs(api_key=os.getenv("VOICEAPI"))

        with open("links.txt", "r", encoding="utf-8") as links:
            contents = links.readlines()
            for voiceLink in contents:
                self.voiceLinks.append(voiceLink.replace("\n",""))
        
        with open("prompts.json", "r", encoding="utf-8") as json_file:
            self.data = json.load(json_file)
            
        with open("quotes.json", "r", encoding="utf-8") as json_file:
            self.quotes = json.load(json_file)
    
    async def add_guild(self, ctx):
        if ctx.guild.id not in self.guilds:
            self.guilds[ctx.guild.id] = False
        
    async def answer_quiz(self, ctx):
        incorrectAnswers =  0
        questionsDict = {self.questions[x]:self.answers[x] for x, y in enumerate(self.questions)}
        string = "\n".join(self.questions)
        await ctx.send(f"```QUESTIONS:\n{string}```\n{self.quotes['ready_quotes'][random.randint(0, len(self.quotes['ready_quotes'])-1)]}")

        question_list = list(questionsDict.items())
        random.shuffle(question_list)
        new_question_list = dict(question_list)

        passing = len(new_question_list) * 0.75
        for nums, questions in enumerate(new_question_list):
            wrong_answer = True
            while wrong_answer:
                await ctx.send(f"QUESTION {nums+1}:\n```{nums+1}.{questions}```")
                user_answer = await self.bot.wait_for("message")
                if user_answer.content == new_question_list[questions]:
                    wrong_answer = False
                else:
                    incorrectAnswers += 1
                    await ctx.send(self.quotes["incorrect_answer_quotes"][random.randint(0, len(self.quotes["incorrect_answer_quotes"])-1)])
        if incorrectAnswers > passing: 
            await ctx.send(f"Incorrect Answers: {incorrectAnswers}\nTotal Items: {str(len(self.questions))}\n\n" + self.quotes["failed_quotes"][random.randint(0, len(self.quotes["failed_quotes"])-1)])
        else:
            await ctx.send(f"Incorrect Answers: {incorrectAnswers}\n\n" + self.quotes["passed_quotes"][random.randint(0, len(self.quotes["passed_quotes"])-1)])

    @commands.command(name="talk", help="join in voice channel")
    async def join_audio(self, ctx):
        await self.add_guild(ctx)
        try:
            channel = ctx.author.voice.channel
            audio_source = discord.FFmpegOpusAudio(self.voiceLinks[random.randint(0, len(self.voiceLinks)-1)])
            if channel:
                if not self.guilds[ctx.guild.id]:
                    await channel.connect()
                    self.guilds[ctx.guild.id] = True
                try:
                    ctx.voice_client.play(audio_source)
                except Exception as error:
                    await ctx.send(f"Error playing the audio: {error}")
            else:
                await ctx.send(f"You need to be in a voice channel to use this command.")
        except Exception as error:
            await ctx.send(str(error))
            
    async def translate_text(self, text:str):
        async with Translator() as translator:
            reponse = await translator.translate(text=text, dest="ja")
            string = reponse.pronunciation
            return string
            
    async def speech_generate(self, text:str, id:str, ctx):  
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{id}/stream"
            header = {"xi-api-key" : os.getenv("VOICEAPI"), "Content-Type": "application/json"}
            data = {"text": await self.translate_text(text), "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}   
        except ValueError or Exception as error:
            await ctx.send("Im tired, let me rest for now, talk to me later")

        voice_request = requests.post(url, headers=header, json=data, stream=True)

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp.write(voice_request.content)
        temp.close()
        return temp.name

    @commands.command(name="speak", help="Text-to-speech")
    async def speak_bot(self, ctx):
        await self.add_guild(ctx)
        try:
            voiceId = "36saPB3WI5Qp88QPcb0F"
            channel = ctx.author.voice.channel
            await ctx.send(self.quotes["speak_quotes"][random.randint(0, len(self.quotes["speak_quotes"])-1)] + "\n\nType the message you want me to speak")
            bot_speak = await self.bot.wait_for("message")

            mp3_path = await self.speech_generate(bot_speak.content, voiceId, ctx)
            audio_source = discord.FFmpegOpusAudio(mp3_path)
            if channel:
                if not self.guilds[ctx.guild.id]:
                    await channel.connect()
                    self.guilds[ctx.guild.id] = True
                try:
                    ctx.voice_client.play(audio_source)
                except Exception as error:
                    await ctx.send(f"Error playing the audio: {error}")
            else:
                await ctx.send(f"You need to be in a voice channel to use this command." + str(error))
        except Exception as error:
            await ctx.send(f"Error Loading the voice: {error}")


    @commands.command(name="leave", help="join in voice channel")
    async def disconnect_audio(self, ctx):
        await self.add_guild(ctx)
        self.guilds[ctx.guild.id] = False
        await ctx.voice_client.disconnect()

    @commands.command(name="quiz", help="the bot will input the questions with answers")
    async def create_quiz(self, ctx, lines):
        await self.add_guild(ctx)
        try:
            numQuestion = int(lines)

            if numQuestion > 15:
                await ctx.send("I can only accept 15 questions")
            else:
                for nums in range(1, numQuestion+1, 1):
                    await ctx.send(f"Input Question #{nums}")
                    ask = await self.bot.wait_for("message")
                    await ctx.send(f"Input Answer for #{nums}")
                    answer = await self.bot.wait_for("message")
                    self.questions.append(str(ask.content))
                    self.answers.append(str(answer.content))
                    await ctx.send(f"```{str(nums) +'.'+(str(ask.content))}```")

            await self.answer_quiz(ctx)

        except Exception as error:
            await ctx.send(self.quotes["invalid_quotes"][random.randint(0, len(self.quotes["invalid_quotes"])-1)] + f"Error: {error}")

    @commands.command(name="restart", help="Restart the quiz")
    async def restart_quiz(self, ctx):
        await self.add_guild(ctx)
        if len(self.questions) <= 0:
            await ctx.send("There are no inputted Questions")
        else:
            await self.answer_quiz(ctx)

    @commands.command(name="clear", help="Clears the questions")
    async def clear_questions(self, ctx):
        await self.add_guild(ctx)
        if len(self.questions) == 0 or len(self.answers) == 0:
            await ctx.send("There are no inputted questions")
        else:
            self.questions.clear()
            self.answers.clear()
            await ctx.send("Inputted Questions Cleared") 

    @commands.command(name="ask", help="Asks a question to a bot")
    async def ask_bot(self, ctx):
        await self.add_guild(ctx)
        await ctx.send(f"{self.quotes['asking_quotes'][random.randint(0, len(self.quotes['asking_quotes'])-1)]}\n\nMessage your question")
        ask = await self.bot.wait_for("message")
        try:
            response = self.model.generate_content(self.data["AICOMMAND"] + str(ask.content))
            await ctx.send(response.text)
        except ValueError or Exception as error:
            await ctx.send("Im tired, let me rest for now, talk to me later")
    
    @commands.command(name="about", help="Display Developer Information")
    async def display_dev(self, ctx):
        await self.add_guild(ctx)
        await ctx.send(self.quotes["dev_quotes"][random.randint(0, len(self.quotes["dev_quotes"])-1)] + "\nhttps://github.com/IKairuu\n\n" + self.quotes["repo_quotes"][random.randint(0, len(self.quotes["repo_quotes"])-1)] + "\nhttps://github.com/IKairuu/Itsuki-Bot")
