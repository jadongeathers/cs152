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
        
        if self.state == State.MESSAGE_IDENTIFIED:
            self.state = State.USER_FIRST_PROMPT
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```",
                    "Why are you reporting this message (please respond with the corresponding number)? \n(1) Fraud\n(2) Verbal Abuse\n(3) Harassment/Intimidation of Violence\n(4) Sensitive/Disturbing Content\n(5) Other\n"]
        
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
    
class ReviewState(Enum):
    REVIEW_START = auto()
    REVIEW_FIRST_MESSAGE = auto()
    REVIEW_ILLEGAL_OR_THREATENING = auto()
    REVIEW_NOT_ILLEGAL_OR_THREATENING = auto()
    REVIEW_FRAUD = auto()
    REVIEW_HATE_SPEECH = auto()
    REVIEW_OTHER = auto()
    REVIEW_HARASSMENT = auto()
    REVIEW_SENSITIVE = auto()
    REVIEW_NOT_ILLEGAL = auto()

class Review:
    START_KEYWORD = "review"

    def __init__(self, client):
        self.state = ReviewState.REVIEW_START
        self.client = client
        self.message = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''
        
        if self.state == ReviewState.REVIEW_START:
            reply =  "Thank you for starting the review process. \n"
            reply += 'Is the reported content illegal/immediately threatening to users? (yes/no)'
            self.state = ReviewState.REVIEW_FIRST_MESSAGE
            return [reply]
        
        if self.state == ReviewState.REVIEW_FIRST_MESSAGE and message in ('yes', 'no'):
            if message == 'yes':
                self.state = ReviewState.REVIEW_ILLEGAL_OR_THREATENING
                return ['To which category does this report belong (please respond with the corresponding number): \n(1) Harassment/Intimidation of violence \n(2) Sensitive/Disturbing Content']
            else:
                self.state = ReviewState.REVIEW_NOT_ILLEGAL_OR_THREATENING
                return ['To which category does this report belong (please respond with the corresponding number): \n(1) Fraud \n(2) Hate Speech \n(3) Other']
        
        if self.state == ReviewState.REVIEW_ILLEGAL_OR_THREATENING and message in ('1', '2'): 
            if message == '1':
                self.state = ReviewState.REVIEW_HARASSMENT
                return ['Is the content illegal (yes/no)?'] 
            else: 
                self.state = ReviewState.REVIEW_SENSITIVE
                return ['Which category does it fall under (please respond with the corresponding number): \n(1) CSAM\n (2) Self Harm \n(3) Other\n']  

        if self.state == ReviewState.REVIEW_NOT_ILLEGAL_OR_THREATENING and message in ('1', '2', '3'): 
            if message == '1':
                self.state = ReviewState.REVIEW_FRAUD 
                return ['Has the user previously received a disciplinary action (yes/no)?']
            elif message == '2': 
                self.state = ReviewState.REVIEW_HATE_SPEECH 
                return ['Has the user previously received a disciplinary action (yes/no)?'] 
            else:
                self.state = ReviewState.REVIEW_OTHER
                return ['Has the user previously received a disciplinary action (yes/no)?'] 
        
        if self.state in (ReviewState.REVIEW_FRAUD, ReviewState.REVIEW_HATE_SPEECH, ReviewState.REVIEW_OTHER) and message in ('yes', 'no'):
            if message == 'yes':
                self.review_complete(self)
                return ['Take down post - move reported user one step up the disciplinary actions hierarchy']
            else:
                self.review_complete(self)
                return ['Take down post - send user a warning']
            
        if self.state == ReviewState.REVIEW_SENSITIVE and message in ('1', '2', '3'):
            if message == '1':
                self.review_complete()
                return ['Report to NCMEC + Ban user + store content securely as required by law']
            if message == '2':
                self.review_complete()
                return ['Connect reported user with self help resources']
            if message == '3':
                self.state = ReviewState.REVIEW_HARASSMENT
                return ['Is the content illegal (yes/no)?'] 
        
        if self.state == ReviewState.REVIEW_HARASSMENT and message in ('yes', 'no'):
            if message == 'yes':
                self.review_complete()
                return ['Ban User + Store content securely as required by law']
            else: 
                self.state = ReviewState.REVIEW_NOT_ILLEGAL
                return ['Has the reported user previously received a one week feature block (yes/no)?']
            
        if self.state == ReviewState.REVIEW_NOT_ILLEGAL and message in ('yes','no'):
            if message == 'yes':
                self.review_complete()
                return ['One week mute/suspension + warning']
            else: 
                self.review_complete()
                return ['Ban User']
        
        return []

    def review_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    

