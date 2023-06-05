#!/usr/bin/python3
# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from googleapiclient import discovery
from report import Report, Review
import pdb
from data_manager import DataManager
from openai import OpenAIMod

# Coefficients for Google Perspective classification
GOOGLE_COEFFS = {
    'intercept': -1.3228379330359248,
    'INSULT': 3.8921009196729774,
    'IDENTITY_ATTACK': 0.9563236343157535,
    'THREAT': 0.31681785782996336
}

# Coefficients for OpenAI classification
OPENAI_COEFFS = {
    'intercept': -1.5949516955386068,
    'hate': 2.514414538130454,
    'hate/threatening': -0.11870110156245899,
    'violence': -0.704727776293726
}

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']
    google_token = tokens['google']
    openai_token = tokens['open_ai']

# Google Perspective API setup
GOOGLE_API_KEY = google_token
OPENAI_API_KEY = openai_token

google = discovery.build(
  "commentanalyzer",
  "v1alpha1",
  developerKey=GOOGLE_API_KEY,
  discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
  static_discovery=False,
)

class ModBot(discord.Client):
    def __init__(self): 
        intents = discord.Intents.default()
        try:
            intents.message_content = True
        except:
            intents.messages = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report
        self.unreviewed = {} # Map from user IDs to unreviewed reports
        self.reviews = {} # Map from user IDs to the state of their review
        self.data_manager = DataManager()
        self.report_in_progress = False

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel
        

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)
            self.unreviewed[author_id] = [self.reports[author_id]]
        else:
            self.unreviewed[author_id].append(Report(self))

        # Let the report class handle this message; forward all the messages it returns to uss
        responses = await self.reports[author_id].handle_message(message)
        for r in responses:
            await message.channel.send(r)

        # If the report is complete or cancelled, remove it from our map
        if self.reports[author_id].report_complete():
            if not self.reports[author_id].cancelled:
                self.data_manager.add_user_report(author_id)
            self.reports.pop(author_id)

    async def handle_channel_message(self, message):

        # Forward the message to the mod channel
        mod_channel = self.mod_channels[message.guild.id]
        if message.channel.name == f'group-{self.group_num}':
            await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')

        if message.channel.name == f'group-{self.group_num}-mod':

            # Handle a help message
            if message.content == Review.HELP_KEYWORD:
                reply = "Use the `review` command to begin the review process.\n"
                reply += "Use the `cancel` command to cancel the review process.\n"
                await message.channel.send(reply)
                return

            author_id = message.author.id
            responses = []

            # If there are no reports, return
            if not self.unreviewed and message.content == Review.START_KEYWORD:
                await message.channel.send('No available unreviewed reports or reports in progress.')
                return

            # Select a report (no priority yet)
            # user_report_id = list(self.unreviewed.keys())[0]
            # report = self.unreviewed[user_report_id][0]
            # offending_message = report.offending_message
            # reporter = report.reporter_id

            user_report_id = None

            # Only respond to messages if they're part of a review flow
            if author_id not in self.reviews and not message.content.startswith(Review.START_KEYWORD):
                return

            # If we don't currently have an active review for this mod, add one
            if author_id not in self.reviews and message.content == Review.START_KEYWORD:
                self.report_in_progress = True
                self.reviews[author_id] = Review(self, unreviewed=self.unreviewed, data_manager=self.data_manager)

            if self.report_in_progress:
                # Let the review class handle this message; forward all the messages it returns to us
                responses = await self.reviews[author_id].handle_message(message)
                for r in responses:
                    await message.channel.send(r)

                if author_id in self.reviews and self.reviews[author_id].review_cancelled():
                    self.reviews.pop(author_id)
                    self.report_in_progress = False

                # If there are no reports for this category, remove the review
                if author_id in self.reviews and self.reviews[author_id].cannot_review():
                    self.reviews.pop(author_id)
                    self.report_in_progress = False

                # If the review is complete or cancelled, remove it from the appropriate maps
                if author_id in self.reviews and self.reviews[author_id].review_complete():
                    user_report_id = self.reviews[author_id].user_report_id
                    await message.channel.send('Done. Review complete.')
                    # if report is accurate, increment accurate reports count by one
                    if not self.reviews[author_id].noaction:
                        self.data_manager.add_true_report(user_report_id)
                    # if report isn't cancelled, increment confirmed reports by one
                    if not self.reviews[author_id].review_cancelled():
                        self.data_manager.add_confirmed_report(user_report_id)
                    self.reviews.pop(author_id)
                    self.unreviewed[user_report_id].pop(0)
                    if not self.unreviewed[user_report_id]:
                        self.unreviewed.pop(user_report_id)
                    self.report_in_progress = False

        if message.channel.name == f'group-{self.group_num}':
            if model_type == 'google':
                # google_score = self.eval_google(message)
                # openai_scores = OpenAIMod.discord_eval(message)
                scores = self.eval_google(message)
                score = 0
                for key in scores:
                    score += GOOGLE_COEFFS[key] * scores[key]
                score += GOOGLE_COEFFS['intercept']

                if score > 0.5:
                    await mod_channel.send('Made automatic report.')
                    report = Report(self)
                    report.reporter_id = 'BOT'
                    report.offending_message = message
                    self.data_manager.add_user_report('BOT')
                    if 'BOT' not in self.unreviewed:
                        self.unreviewed['BOT'] = []
                    self.unreviewed['BOT'].append(report)
                await mod_channel.send(self.code_format(score))

            elif model_type == 'open_ai':
                openai_model = OpenAIMod()
                scores = openai_model.discord_eval(message)
                score = 0
                for key in scores:
                    score += OPENAI_COEFFS[key] * scores[key]
                score += OPENAI_COEFFS['intercept']

                if score > 0.5:
                    await mod_channel.send('Made automatic report.')
                    report = Report(self)
                    report.reporter_id = 'BOT'
                    report.offending_message = message
                    self.data_manager.add_user_report('BOT')
                    if 'BOT' not in self.unreviewed:
                        self.unreviewed['BOT'] = []
                    self.unreviewed['BOT'].append(report)
                await mod_channel.send(self.code_format(score))

            elif model_type == 'combo':
                google_scores = self.eval_google(message)
                google_score = 0
                for key in google_scores:
                    google_score += GOOGLE_COEFFS[key] * google_scores[key]
                google_score += GOOGLE_COEFFS['intercept']

                if google_score > 0.5:
                    openai_model = OpenAIMod()
                    openai_scores = openai_model.discord_eval(message)
                    score = 0
                    for key in openai_scores:
                        score += OPENAI_COEFFS[key] * openai_scores[key]
                    score += OPENAI_COEFFS['intercept']

                    if score > 0.5:
                        await mod_channel.send('Made automatic report.')
                        report = Report(self)
                        report.reporter_id = 'BOT'
                        report.offending_message = message
                        self.data_manager.add_user_report('BOT')
                        if 'BOT' not in self.unreviewed:
                            self.unreviewed['BOT'] = []
                        self.unreviewed['BOT'].append(report)
                    await mod_channel.send(self.code_format(score))

                    # TODO: RETURN PREDICTION OF SEVERITY

        return

    def eval_google(self, message):
        analyze_request = {
            'comment': {'text': message.content},
            'requestedAttributes': {
                'IDENTITY_ATTACK': {},
                'INSULT': {},
                'THREAT': {}
            }
        }
        response = google.comments().analyze(body=analyze_request).execute()
        probs = {flag: response['attributeScores'][flag]['summaryScore']['value'] for flag in response['attributeScores']}
        return probs

    def code_format(self, text):
        # if text.dtype == int:
        return "Evaluated by Google Perspective: '" + str(text)+ "'"
        # if text.dtype == list:
        #         return "Evaluated by OpenAI's Moderator: '" + str(text)+ "'"
        # return "Evaluated: '" + str(text)+ "'"


import argparse

ALLOWED_MODEL_TYPES = ["google", "open_ai", "combo"]
parser = argparse.ArgumentParser()
parser.add_argument("--model_type", type=str, choices=ALLOWED_MODEL_TYPES, help="Specify the model type (google, open_ai, combo)")
args = parser.parse_args()
model_type = args.model_type

client = ModBot()
client.run(discord_token)