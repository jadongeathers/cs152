from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    REPORT_COMPLETE = auto()
    USER_FIRST_PROMPT = auto()
    USER_FRAUD = auto()
    USER_VERBAL_ABUSE = auto()
    USER_HARASSMENT = auto()
    USER_SENSITIVE_CONTENT = auto()
    USER_OTHER = auto()
    USER_BLOCK = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```", \
                    "This is all I know how to do right now - it's up to you to build out the rest of my reporting flow!"]
        
        if self.state == State.MESSAGE_IDENTIFIED:
            self.state = State.USER_FIRST_PROMPT
            return ["Why are you reporting this message (please respond with the corresponding number)? \n(1) Fraud\n(2) Verbal Abuse\n(3) Harassment/Intimidation of Violence\n(4) Sensitive/Disturbing Content\n(5) Other\n"]
        
        if self.state == State.USER_FIRST_PROMPT:
            if message == '1':
                self.state = State.USER_FRAUD
                return ["Please select the type of harm (please respond with the corresponding number). \n(1) Impersonation\n(2) Scam\n(3) Solicitation\n"] 
            if message == '2':
                self.state = State.USER_VERBAL_ABUSE
                reply = "Please select the type of harm (please respond with the corresponding number). \n"
                reply += "(1) Violent Language: Celebration of violent acts\n"
                reply += "(2) Violent Language: Violent event denial\n"
                reply += "(3) Violent Language: Dehumanization\n"
                reply += "(4) Violent Language: Inciting or encouraging violence\n"
                reply += "(5) Hate Speech: Ethnicity/Race/Nationality\n"
                reply += "(6) Hate Speech: Gender/Sex/Sexuality\n"
                reply += "(7) Hate Speech: Religion\n"
                reply += "(8) Hate Speech: Political Beliefs\n"
                reply += "(9) Hate Speech: Disability/Health Status\n"
                reply += "(10) Hate Speech: Other\n"
                return [reply] 
            if message == '3':
                self.state = State.USER_HARASSMENT
                return ["Please select the type of harm (please respond with the corresponding number). \n(1) Sexual Harassment\n(2) Threatening to post or posting private info\n(3) Stalking/Threats to injure\n"]  
            if message == '4':
                self.state = State.USER_SENSITIVE_CONTENT
                return ["Please select the type of harm (please respond with the corresponding number). \n(1) Child Exploitation\n(2) Assault\n(3) Beastiality\n(4) Self Harm\n)"] 
            if message == '5':
                self.state = State.USER_OTHER
                return ["Why is this message harmful?"] 
        
        if self.state == State.USER_FRAUD and message in ('1', '2', '3'):
            reply = 'Thank you for your report. Our 24/7 moderation team will review it shortly.\n'
            reply += 'Would you like to block this user to prevent future interactions with this user?\n'
            self.state = State.USER_BLOCK
            return reply
        
        if self.state == State.USER_VERBAL_ABUSE and message in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10'):
            reply = 'Thank you for your report. Our 24/7 moderation team will review it shortly.\n'
            reply += 'Would you like to block this user to prevent future interactions with this user?\n'
            self.state = State.USER_BLOCK
            return reply
        
        if self.state == State.USER_HARASSMENT and message in ('1', '2', '3'):
            reply = 'Thank you for your report. Our 24/7 moderation team will review it shortly.\n'
            reply += 'Would you like to block this user to prevent future interactions with this user?\n'
            self.state = State.USER_BLOCK
            return reply
        
        if self.state == State.USER_SENSITIVE_CONTENT and message in ('1', '2', '3', '4'):
            reply = 'Thank you for your report. Our 24/7 moderation team will review it shortly.\n'
            reply += 'Would you like to block this user to prevent future interactions with this user?\n'
            self.state = State.USER_BLOCK
            return reply
        
        if self.state == State.USER_OTHER:
            reply = 'Thank you for your report. Our 24/7 moderation team will review it shortly.\n'
            reply += 'Would you like to block this user to prevent future interactions with this user (yes/no)?\n'
            self.state = State.USER_BLOCK
            return reply
        
        if self.state == State.USER_BLOCK and message in ('yes', 'no'):
            self.report_complete()
            return ['Done. Report Closed.']

        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    

