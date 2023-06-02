#!/usr/bin/python3
# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report, Review
import pdb
from data_manager import DataManager

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
        self.unreviewed = {} # Map from user IDs to unreview report
        self.reviews = {} # Map from user IDs to the state of their review
        self.data_manager = DataManager()

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
            reply =  "Use the `report` command to begin the ing process.\n"
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
            self.unreviewed[author_id] = self.reports[author_id]

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
        # ORIGINAL:
        # Only handle messages sent in the "group-#" channel
        # if not message.channel.name == f'group-{self.group_num}':
        #     return

        ##### START ADDED #####

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
            if not self.unreviewed:
                await message.channel.send('No available unreviewed reports or reports in progress.')
                return

            # Select a report (no priority yet)
            user_report_id = list(self.unreviewed.keys())[0]
            report = self.unreviewed[user_report_id]
            offending_message = report.offending_message
            reporter = report.reporter_id

            # Only respond to messages if they're part of a review flow
            if author_id not in self.reviews and not message.content.startswith(Review.START_KEYWORD):
                return

            # If we don't currently have an active review for this mod, add one
            if author_id not in self.reviews:
                await message.channel.send('Below is the reported content:')
                await message.channel.send("```" + offending_message.author.name + ": " + offending_message.content + "```")
                await message.channel.send('Reporting User ' + str(reporter) + ' has made ' + str(self.data_manager.get_reports_confirmed(reporter))
                                           + ' previous reports with ' + str(self.data_manager.get_trust_score(reporter)) + '% accuracy ')
                self.reviews[author_id] = Review(self)

            # Let the review class handle this message; forward all the messages it returns to us
            responses = await self.reviews[author_id].handle_message(message)
            for r in responses:
                await message.channel.send(r)

            # If the review is complete or cancelled, remove it from the appropriate maps
            if self.reviews[author_id].review_complete():
                await message.channel.send('Done. Review complete.')
                # if report is accurate, incrament accurate reports count by one
                if not self.reviews[author_id].noaction:
                    self.data_manager.add_true_report(user_report_id)
                # if report isnt cancelled, increment confirmed reports by one
                if not self.reviews[author_id].review_cancelled():
                    self.data_manager.add_confirmed_report(user_report_id)
                self.reviews.pop(author_id)
                self.unreviewed.pop(user_report_id)
            if self.reviews and self.reviews[author_id].review_cancelled():
                self.reviews.pop(author_id)

        if message.channel.name == f'group-{self.group_num}':
            scores = self.eval_text(message.content)
            await mod_channel.send(self.code_format(scores))

        return

        ##### END ADDED #####

        # ORIGINAL:
        # scores = self.eval_text(message.content)
        # await mod_channel.send(self.code_format(scores))

    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        return message

    
    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return "Evaluated: '" + text+ "'"


client = ModBot()
client.run(discord_token)