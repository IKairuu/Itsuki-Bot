import discord
from discord.ext import commands
import random
import os
import google.generativeai as genai

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
        except Exception as error:
            await ctx.send(f"You need to be in a voice channel to use this command.")

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
        try:
            response = self.model.generate_content(os.getenv('AICOMMAND') + str(ask.content))
            await ctx.send(response.text)

        except Exception as error:
            await ctx.send("W-Wha?! This is way too much for me! I’m not a genius, you know… Can we slow down before my brain explodes?!😖🍞")






