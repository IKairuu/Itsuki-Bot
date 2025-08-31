import discord
from discord.ext import commands
import random
import os
import cohere
from googletrans import Translator
from elevenlabs.client import ElevenLabs
import tempfile, json

from httpx import HTTPError

class Background(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.inVoiceChannel = False

        self.cohere = cohere.AsyncClientV2(os.getenv("COHERE"))
        self.elevenLabs = ElevenLabs(api_key=os.getenv("VOICEAPISEC"))

        with open("main.json", "r", encoding="utf-8") as json_file:
            self.data = json.load(json_file)

        with open("quotes.json", "r", encoding="utf-8") as json_file:
            self.quotes = json.load(json_file)

        with open("links.txt", "r", encoding="utf-8") as links:
            contents = links.readlines()
            for voiceLink in contents:
                self.data["voice_links"].append(voiceLink.replace("\n",""))


    # ------------------------------------ QUIZ ------------------------------------------------------       
    @commands.command(name="start", help="start the quiz")
    async def start_quiz(self, ctx):
        if self.find_author(ctx.message.author.id):
            await self.answer_quiz(ctx)
        else:
            await ctx.send("There is no quz list ")

    def find_author(self, id:str):
        for users in self.data["quiz"]["user_quiz"]:
            if id == users:
                return True
        return False

    async def answer_quiz(self, ctx):
        def check_author(m):
            return m.author == ctx.author and m.channel == ctx.channel
        incorrectAnswers =  0
        questionsDict = {self.data["quiz"]["user_quiz"][ctx.message.author.id][0][x]:self.data["quiz"]["user_quiz"][ctx.message.author.id][1][x] for x, y in enumerate(self.data["quiz"]["user_quiz"][ctx.message.author.id])}
        string = "\n".join(self.data["quiz"]["user_quiz"][ctx.message.author.id][0])
        await ctx.send(f"```QUESTIONS:\n{string}```\n{self.quotes['ready_quotes'][random.randint(0, len(self.quotes['ready_quotes'])-1)]}")

        question_list = list(questionsDict.items())
        random.shuffle(question_list)
        new_question_list = dict(question_list)

        passing = len(new_question_list) * 0.75
        for nums, questions in enumerate(new_question_list):
            wrong_answer = True
            while wrong_answer:
                await ctx.send(f"QUESTION {nums+1}:\n```{nums+1}.{questions}```")
                user_answer = await self.bot.wait_for("message", check = check_author, timeout = 60.0)
                if user_answer.content == new_question_list[questions]:
                    wrong_answer = False
                else:
                    incorrectAnswers += 1
                    await ctx.send(self.quotes["incorrect_answer_quotes"][random.randint(0, len(self.quotes["incorrect_answer_quotes"])-1)])
        if incorrectAnswers > passing: 
            await ctx.send(f"Incorrect Answers: {incorrectAnswers}\nTotal Items: {str(len(self.data['quiz']['user_quiz'][ctx.message.author.id][0]))}\n\n" + self.quotes['failed_quotes'][random.randint(0, len(self.quotes["failed_quotes"])-1)])
        else:
            await ctx.send(f"Incorrect Answers: {incorrectAnswers}\nTotal Items: {str(len(self.data['quiz']['user_quiz'][ctx.message.author.id][0]))}\n\n" + self.quotes['passed_quotes'][random.randint(0, len(self.quotes['passed_quotes'])-1)])

    @commands.command(name="quiz", help="the bot will input the questions with answers")
    async def create_quiz(self, ctx, lines):
        def check_author(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            numQuestion = int(lines)

            if numQuestion > 15:
                await ctx.send("I can only accept 15 questions")
            else:
                author_id = ctx.message.author.id

                for nums in range(1, numQuestion+1, 1):
                    await ctx.send(f"Input Question #{nums}")
                    ask = await self.bot.wait_for("message", check = check_author)
                    await ctx.send(f"Input Answer for #{nums}")
                    answer = await self.bot.wait_for("message", check = check_author)
                    self.data["quiz"]["questions"].append(str(ask.content))
                    self.data["quiz"]["answers"].append(str(answer.content))
                    await ctx.send(f"```{str(nums) +'.'+(str(ask.content))}```")
            await ctx.send("Quiz Inputted Successfully")
            self.data["quiz"]["user_quiz"][author_id] = [self.data["quiz"]["questions"], self.data["quiz"]["answers"]]
            self.data["quiz"]["answers"] = []
            self.data["quiz"]["questions"] = []

        except Exception as error:
            await ctx.send(self.quotes["invalid_quotes"][random.randint(0, len(self.quotes["invalid_quotes"])-1)])
            print(error)

    @commands.command(name="restart", help="Restart the quiz")
    async def restart_quiz(self, ctx):
        if not self.find_author(ctx.message.author.id):
            await ctx.send("There are no inputted Questions")
        else:
            await self.answer_quiz(ctx)

    @commands.command(name="clear", help="Clears the questions")
    async def clear_questions(self, ctx):
        if not self.find_author(ctx.message.author.id):
            await ctx.send("There are no inputted questions")
        else:
            self.data["quiz"]["user_quiz"].pop(ctx.message.author.id)
            await ctx.send("Inputted Questions Cleared") 


    # ------------------------------------ TALK FUNCTION ------------------------------------------------------       
    @commands.command(name="talk", help="join in voice channel")
    async def join_audio(self, ctx):
        try:
            channel = ctx.author.voice.channel
            audio_source = discord.FFmpegOpusAudio(self.data["voice_links"][random.randint(0, len(self.data["voice_links"])-1)])
            if channel:
                if not self.inVoiceChannel:
                    await channel.connect()
                    self.inVoiceChannel = True

                try:
                    ctx.voice_client.play(audio_source)
                except Exception as error:
                    await ctx.send(f"Error playing the audio: {error}")
        except Exception or AttributeError as error:
            if AttributeError:
                await ctx.send(f"You need to be in a voice channel to use this command.")
            else:
                await ctx.send("Im tired right now, talk to me again later")
                print(error)

    @commands.command(name="leave", help="join in voice channel")
    async def disconnect_audio(self, ctx):
        await ctx.voice_client.disconnect()
        self.inVoiceChannel = False

    # ------------------------------------ TTS ------------------------------------------------------       
    async def translate_text(self, text:str):
        async with Translator() as translator:
            reponse = await translator.translate(text=text, dest="ja")
            string = reponse.pronunciation
            return string

    async def speech_generate(self, text:str, ctx):
        self.data["voice_model"]["text"] = await self.translate_text(text)
        voice = self.elevenLabs.text_to_speech.convert(text=self.data["voice_model"]["text"], voice_id=self.data["voice_model"]["voice_id"], model_id=self.data["voice_model"]["model_id"], output_format=self.data["voice_model"]["output_format"])
        self.data["voice_model"]["text"] = "" 
        temp = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".mp3")
        for chunks in voice:
            temp.write(chunks)
        temp.close()
        print(temp.name)
        print(type(temp.name))
        return temp.name

    @commands.command(name="speak", help="Text-to-speech")
    async def speak_bot(self, ctx):
        def check_author(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            channel = ctx.author.voice.channel
            await ctx.send(self.quotes["speak_quotes"][random.randint(0, len(self.quotes["speak_quotes"])-1)] + "\n\nType the message you want me to speak")
            bot_speak = await self.bot.wait_for("message", check = check_author, timeout = 60.0)

            mp3_path = await self.speech_generate(bot_speak.content, ctx)
            audio_source = discord.FFmpegOpusAudio(mp3_path)
            if channel:
                if not self.inVoiceChannel:
                    await channel.connect()
                    self.inVoiceChannel = True
                try:
                    ctx.voice_client.play(audio_source)
                except Exception as error:
                    await ctx.send(f"Error playing the audio")
                    print(error)
        except Exception or AttributeError as error:
            if AttributeError:
                await ctx.send(f"You need to be in a voice channel to use this command.")
                print(error)
            else:
                await ctx.send("Im tired right now, talk to me again later")
                print(error)


    # ------------------------------------ ASK FUNCTION ------------------------------------------------------       
    @commands.command(name="ask", help="Asks a question to a bot")
    async def ask_bot(self, ctx):
        def check_author(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send(f"{self.quotes['asking_quotes'][random.randint(0, len(self.quotes['asking_quotes'])-1)]}\n\nMessage your question")
        ask = await self.bot.wait_for("message", check = check_author, timeout = 60.0)
        try:
            response = await self.cohere.chat(model=self.data["cohere_model"], messages=[cohere.UserChatMessageV2(content=self.data["AICOMMAND"] + ask.content)])
            if len(response.message.content[0].text) >= 2000:
                await ctx.send("Ask again,its too much for me")
            else:
                await ctx.send(response.message.content[0].text)
        except ValueError or Exception as error:
            await ctx.send("Im tired, let me rest for now, talk to me later")
            print(error)


    # ------------------------------------ INFORMATION ------------------------------------------------------       
    @commands.command(name="about", help="Display Developer Information")
    async def display_dev(self, ctx):
        await ctx.send(self.quotes["dev_quotes"][random.randint(0, len(self.quotes["dev_quotes"])-1)] + "\nhttps://github.com/IKairuu\n\n" + self.quotes["repo_quotes"][random.randint(0, len(self.quotes["repo_quotes"])-1)] + "\nhttps://github.com/IKairuu/Itsuki-Bot")
