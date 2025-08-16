import discord
from discord.ext import commands
import random
import os
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
import requests
import tempfile

class Background(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.inVoiceChannel = False
        self.invalidInputResponse = []
        self.voiceLinks = []
        self.questions = []
        self.answers = []

        gemini_api_key = os.getenv("API")
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.5-pro")

        self.elevenLabs = ElevenLabs(api_key=os.getenv("VOICEAPI"))

        with open("links.txt", "r", encoding="utf-8") as links:
            contents = links.readlines()
            for voiceLink in contents:
                self.voiceLinks.append(voiceLink.replace("\n",""))

        with open("invalid.txt", "r", encoding="utf-8") as responses:
            contents = responses.readlines()
            for res in contents:
                self.invalidInputResponse.append(res.replace("\n",""))

    async def answer_quiz(self, ctx):
        incorrectAnswers =  0
        readyQuotes = ["S-So… are you really ready for this? I-I mean, don’t blame me if you didn’t study properly!",
                           "T-The test is starting any minute now… D-Don’t just sit there! Are you ready or not?!",
                           "Y-You’ve worked hard, I know that… b-but are you truly prepared? I’ll be cheering for you either way!"]
        incorrectAnswerQuotes = ["W-What?! That’s not the answer! Ugh… you weren’t listening again, were you?!",
                                "I-It’s wrong… b-but it’s okay! We’ll just review it together until you get it!",
                                "H-Honestly… you need to focus more! B-But I’ll help you fix it, so don’t give up!"]
        passedQuotes = ["Y-You passed?! I knew you had it in you! …N-Not that I was worried or anything!",
                        "Amazing…! I-I mean, that was expected since I helped you review, right?",
                        "T-Totally crushed it! J-Just don’t slack off now, okay?! You have to keep it up!"]
        failedQuotes = ["Geez… How did you mess that up? A-Are you trying to stress me out?! …Hmph. Fine, we’ll try again.",
                        "I-I’m disappointed… B-But only because I know you can do better! N-Now let’s go again!",
                        "T-This is not the end! I won’t let you give up just because of one lousy score!"]
        questionsDict = {self.questions[x]:self.answers[x] for x, y in enumerate(self.questions)}
        string = "\n".join(self.questions)
        await ctx.send(f"```QUESTIONS:\n{string}```\n{readyQuotes[random.randint(0, len(readyQuotes)-1)]}")

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
                    await ctx.send(incorrectAnswerQuotes[random.randint(0, len(incorrectAnswerQuotes)-1)])
        if incorrectAnswers > passing:
            await ctx.send(f"Incorrect Answers: {incorrectAnswers}\nTotal Items: {str(len(self.questions))}\n\n" + failedQuotes[random.randint(0, len(failedQuotes)-1)])
        else:
            await ctx.send(f"Incorrect Answers: {incorrectAnswers}\n\n" + passedQuotes[random.randint(0, len(passedQuotes)-1)])

    @commands.command(name="talk", help="join in voice channel")
    async def join_audio(self, ctx):
        try:
            channel = ctx.author.voice.channel
            audio_source = discord.FFmpegOpusAudio(self.voiceLinks[random.randint(0, len(self.voiceLinks)-1)])
            if channel:
                if not self.inVoiceChannel:
                    await channel.connect()
                    self.inVoiceChannel = True
                try:
                    ctx.voice_client.play(audio_source)
                except Exception as error:
                    await ctx.send(f"Error playing the audio: {error}")
            else:
                await ctx.send(f"You need to be in a voice channel to use this command.")
        except Exception as error:
            await ctx.send(str(error))

    def speech_generate(self, text:str, id:str):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{id}/stream"
        header = {"xi-api-key" : os.getenv("VOICEAPI"), "Content-Type": "application/json"}
        data = {"text": text, "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}            

        voice_request = requests.post(url, headers=header, json=data, stream=True)

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp.write(voice_request.content)
        temp.close()
        return temp.name

    @commands.command(name="speak", help="Text-to-speech")
    async def speak_bot(self, ctx):
        speak_quotes = ["M-Mou… fine, I’ll talk. But only this once!",
                       "Okay, but if you laugh, I’m not saying another word!",
                       "You’re lucky I’m in a good mood today… okay, let’s do this.",
                       "Okay, okay, I’ll say it… sheesh, you’re so demanding.",
                       "If you wanted to hear my voice that badly… here it is!"]
        try:
            voiceId = "36saPB3WI5Qp88QPcb0F"
            channel = ctx.author.voice.channel
            await ctx.send(speak_quotes[random.randint(0,len(speak_quotes)-1)] + "\n\nType the message you want me to speak")
            bot_speak = await self.bot.wait_for("message")

            mp3_path = self.speech_generate(bot_speak.content, voiceId)
            audio_source = discord.FFmpegOpusAudio(mp3_path)
            if channel:
                if not self.inVoiceChannel:
                    await channel.connect()
                    self.inVoiceChannel = True
                try:
                    ctx.voice_client.play(audio_source)
                except Exception as error:
                    await ctx.send(f"Error playing the audio: {error}")
            else:
                await ctx.send(f"You need to be in a voice channel to use this command." + str(error))
        except Exception as error:
            await ctx.send(f"Error Loading the voice")


    @commands.command(name="leave", help="join in voice channel")
    async def disconnect_audio(self, ctx):
        self.inVoiceChannel = False
        await ctx.voice_client.disconnect()

    @commands.command(name="quiz", help="the bot will input the questions with answers")
    async def create_quiz(self, ctx, lines):
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
            await ctx.send(self.invalidInputResponse[random.randint(0, len(self.invalidInputResponse)-1)] + f"Error: {error}")

    @commands.command(name="restart", help="Restart the quiz")
    async def restart_quiz(self, ctx):
        if len(self.questions) <= 0:
            await ctx.send("There are no inputted Questions")
        else:
            await self.answer_quiz(ctx)

    @commands.command(name="clear", help="Clears the questions")
    async def clear_questions(self, ctx):
        if len(self.questions) == 0 or len(self.answers) == 0:
            await ctx.send("There are no inputted questions")
        else:
            self.questions.clear()
            self.answers.clear()
            await ctx.send("Inputted Questions Cleared") 

    @commands.command(name="ask", help="Asks a question to a bot")
    async def ask_bot(self, ctx):
        askingQuotes = ["E-Eh? You’re asking me? W-Well… I’ll try my best! Just don’t expect me to know everything, okay?!", 
                        "I-I guess I am the reliable one… F-Fine, ask your question. Let’s figure it out together!",
                        "W-What is it this time? If it’s another weird question, I swear I’ll—… Ugh, fine. Go on.",
                        "Hmph… I was in the middle of reviewing, but f-fine. Let’s see what you’ve got!"]
        await ctx.send(f"{askingQuotes[random.randint(0, len(askingQuotes)-1)]}\n\nMessage your question")
        ask = await self.bot.wait_for("message")
        response = self.model.generate_content(os.getenv('AICOMMAND') + str(ask.content))
        await ctx.send(response.text)
    
    @commands.command(name="about", help="Display Developer Information")
    async def display_dev(self, ctx):
        dev_quotes = ["O-Oh! U-Um… this is Kairu, my developer! D-Don’t get the wrong idea, they’re not perfect, but… they worked really hard to make me, s-so you better appreciate them!",
                      "Tch… I guess I should introduce the one behind all this. This is Kairu, they’re the reason I’m even talking to you right now. Don’t praise them too much, though!",
                      "If you’re wondering who made me this way… it’s Kairu! Hmph, don’t get the wrong idea, I’m not bragging about them or anything…", 
                      "You should know Kairu’s the one who worked hard to make me your study partner. I-I’m just doing my part, okay?",
                      "Don’t underestimate me just because I’m flustered sometimes! With Kairu’s help, I can handle anything you throw at me!"]

        repo_quotes = ["You’ve entered my place. Hmph, don’t touch anything without asking me first!",
                       "Listen carefully! This is Itsuki’s repository, so treat it with respect… o-or else!",
                       "This repository belongs to Itsuki Nakano! Remember that before snooping around!",
                       "Don’t get the wrong idea! This is my place, and I’m just letting you use it… got that?",
                       "Heh… you’ve stepped into Itsuki Nakano’s repository! So behave yourself properly!"]
        
        await ctx.send(dev_quotes[random.randint(0, len(dev_quotes)-1)] + "\nhttps://github.com/IKairuu\n\n" + repo_quotes[random.randint(0, len(repo_quotes)-1)] + "\nhttps://github.com/IKairuu/Itsuki-Bot")





