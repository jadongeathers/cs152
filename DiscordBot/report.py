from enum import Enum, auto
import discord
import re

from data_manager import DataManager


class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    USER_FIRST_PROMPT = auto()
    USER_FRAUD = auto()
    USER_VERBAL_ABUSE = auto()
    USER_HARASSMENT = auto()
    USER_SENSITIVE_CONTENT = auto()
    USER_OTHER = auto()
    USER_BLOCK = auto()
    REPORT_COMPLETE = auto()


class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
        self.offending_message = None
        self.cancelled = False
        self.reporter_id = None
        # Which of the five categories in our review flow does the report fall under
        self.categories = [False, False, False, False, False]
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''
        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            self.cancelled = True
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

            # Here we've found the message
            self.state = State.MESSAGE_IDENTIFIED
            self.offending_message = message

        if self.state == State.MESSAGE_IDENTIFIED:
            self.state = State.USER_FIRST_PROMPT
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```",
                     "Why are you reporting this message? Please respond with the corresponding number. "
                     "\n(1) Fraud\n(2) Verbal Abuse\n(3) Harassment/Threats of Violence"
                     "\n(4) Sensitive/Disturbing Content\n(5) Other\n"]

        if self.state == State.USER_FIRST_PROMPT:
            # saves user making the report
            self.reporter_id = message.author.id
            if message.content == '1':
                self.state = State.USER_FRAUD
                self.categories[0] = True
                return ["Select the type of harm. Please respond with the corresponding number. "
                        "\n(1) Impersonation\n(2) Scam\n(3) Solicitation\n"]
            if message.content == '2':
                self.state = State.USER_VERBAL_ABUSE
                self.categories[1] = True
                reply = "Select the type of harm. Please respond with the corresponding number. \n"
                reply += 'Violent language concerning...\n'
                reply += "(1) Celebration of violent acts\n"
                reply += "(2) Denial of a violent event\n"
                reply += "(3) Dehumanization\n"
                reply += "(4) Inciting or encouraging violence\n"
                reply += 'Hate speech concerning...\n'
                reply += "(5) Ethnicity/Race/Nationality\n"
                reply += "(6) Gender/Sex/Sexuality\n"
                reply += "(7) Religion\n"
                reply += "(8) Disability/Health Status\n"
                reply += "(9) Other\n"
                return [reply] 
            if message.content == '3':
                self.state = State.USER_HARASSMENT
                self.categories[2] = True
                return ["Select the type of harm. Please respond with the corresponding number. "
                        "\n(1) Sexual Harassment\n(2) Threatening to post or posting private info"
                        "\n(3) Stalking or threats to injure\n"]
            if message.content == '4':
                self.state = State.USER_SENSITIVE_CONTENT
                self.categories[3] = True
                return ["Select the type of harm. Please respond with the corresponding number. "
                        "\n(1) Child Exploitation\n(2) Assault\n(3) Beastiality\n(4) Self Harm\n"]
            if message.content == '5':
                self.state = State.USER_OTHER
                self.categories[4] = True
                return ["Why is this message harmful?"]

            return ['Please select a valid option.']
        
        if self.state == State.USER_FRAUD and message.content in ('1', '2', '3'):
            reply = 'Thank you for your report. Our 24/7 moderation team will review it shortly.\n'
            reply += 'Would you like to block this user to prevent future interactions with them (yes/no)?\n'
            self.state = State.USER_BLOCK
            return [reply]
        
        if self.state == State.USER_VERBAL_ABUSE and message.content in ('1', '2', '3', '4', '5', '6', '7', '8', '9'):
            reply = 'Thank you for your report. Our 24/7 moderation team will review it shortly.\n'
            reply += 'Would you like to block this user to prevent future interactions with them (yes/no)?\n'
            self.state = State.USER_BLOCK
            return [reply]

        if self.state == State.USER_HARASSMENT and message.content in ('1', '2', '3'):
            reply = 'Thank you for your report. Our 24/7 moderation team will review it shortly.\n'
            reply += 'Would you like to block this user to prevent future interactions with them (yes/no)?\n'
            self.state = State.USER_BLOCK
            return [reply]
        
        if self.state == State.USER_SENSITIVE_CONTENT and message.content in ('1', '2', '3', '4'):
            reply = 'Thank you for your report. Our 24/7 moderation team will review it shortly.\n'
            reply += 'Would you like to block this user to prevent future interactions with them (yes/no)?\n'
            self.state = State.USER_BLOCK
            return [reply]
        
        if self.state == State.USER_OTHER:
            reply = 'Thank you for your report. Our 24/7 moderation team will review it shortly.\n'
            reply += 'Would you like to block this user to prevent future interactions with them (yes/no)?\n'
            self.state = State.USER_BLOCK
            return [reply]
        
        if self.state == State.USER_BLOCK and message.content in ('yes', 'no'):
            self.state = State.REPORT_COMPLETE
            self.report_complete()
            # client.add_user_report(message.author.id)
            return ['Done. Report Closed.']

        else:
            return ['Invalid action. Please select only valid actions.']

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    
class ReviewState(Enum):
    REVIEW_START = auto()
    REVIEW_FIRST_MESSAGE = auto()
    REVIEW_FRAUD = auto()
    REVIEW_DISCRIMINATE_LOW = auto()
    REVIEW_DISCRIMINATE_HIGH = auto()
    REVIEW_DISCRIMINATE_HARASSMENT = auto()
    REVIEW_DISCRIMINATE_SENSITIVE = auto()
    REVIEW_HATE_SPEECH = auto()
    REVIEW_DEROGATORY = auto()
    REVIEW_SENSITIVE = auto()
    REVIEW_OTHER = auto()
    REVIEW_DEFAMATION = auto()
    REVIEW_ABUSIVE = auto()
    REVIEW_HARASSMENT = auto()
    REVIEW_INCITE_VIOLENCE = auto()
    REVIEW_VERBAL_ABUSE = auto()
    REVIEW_COMPLETE = auto()
    REVIEW_CANCELLED = auto()
    REVIEW_TIER_0 = auto()
    REVIEW_TIER_1 = auto()
    REVIEW_TIER_2 = auto()
    REVIEW_TIER_3 = auto()
    REVIEW_TIER_4 = auto()
    REVIEW_TIER_4_CSAM = auto()
    REVIEW_DISCRETIONARY = auto()
    REVIEW_NO_ACTION = auto()
    REVIEW_CANNOT_REVIEW = auto()
    REVIEW_BOT = auto()
    REVIEW_START_CATEGORY = auto()

class Review:
    START_KEYWORD = "review"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client, unreviewed=None, data_manager=None):
        self.state = ReviewState.REVIEW_START
        self.model_type = None
        self.client = client
        self.message = None
        self.noaction = False
        self.user_report_id = None
        self.unreviewed = unreviewed
        self.data_manager = data_manager
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the mod-side reporting flow. It defines how we transition between states and what
        prompts to offer at each of those states.
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = ReviewState.REVIEW_CANCELLED
            return ["Review cancelled."]
        
        if self.state == ReviewState.REVIEW_START:
            self.state = ReviewState.REVIEW_START_CATEGORY
            reply = "Thank you for starting the review process. \n"
            reply += "Which API would you like to use? \n"
            reply += "\n(1) Google Perspective\n(2) OpenAI\n(3) Google Perspective + OpenAI"
            return [reply]

        if self.state == ReviewState.REVIEW_START_CATEGORY and message.content in ('1', '2', '3'):
            if message.content == '1':
                self.model_type = 'google'
            elif message.content == '2':
                self.model_type = 'open_ai'
            elif message.content == '3':
                self.model_type = 'combo'
            reply = "Which category would you like to review? \n"
            reply += "\n(1) Fraud\n(2) Verbal Abuse\n(3) Harassment/Threats of Violence"
            reply += "\n(4) Sensitive/Disturbing Content\n(5) Other\n(6) Automatic Reports"
            self.state = ReviewState.REVIEW_FIRST_MESSAGE
            return [reply]
        
        if self.state == ReviewState.REVIEW_FIRST_MESSAGE and message.content in ('1', '2', '3', '4', '5', '6'):
            if message.content == '1':
                # Make queue and get report
                reports = {}
                for author in self.unreviewed:
                    for report in self.unreviewed[author]:
                        if report.categories[0]:
                            if author not in reports:
                                reports[author] = []
                            reports[author].append(report)
                if not reports:
                    self.state = ReviewState.REVIEW_CANNOT_REVIEW
                    return ['No available unreviewed reports or reports in progress.']

                self.user_report_id = list(reports.keys())[0]
                report = self.unreviewed[self.user_report_id][0]
                offending_message = report.offending_message
                reporter = report.reporter_id
                await message.channel.send('Below is the reported content:')
                await message.channel.send("```" + offending_message.author.name + ": " + offending_message.content + "```")
                await message.channel.send('Reporting User ' + str(reporter) + ' has made ' + str(self.data_manager.get_reports_confirmed(reporter))
                                           + ' previous reports with ' + str(self.data_manager.get_trust_score(reporter)) + '% accuracy ')

                reply = 'What is the type of fraud?\n'
                reply += '(1) Impersonation\n'
                reply += '(2) Scam\n'
                reply += '(3) Solicitation\n'
                self.state = ReviewState.REVIEW_FRAUD
                return [reply]

            if message.content == '2':
                # Make queue and get report
                reports = {}
                for author in self.unreviewed:
                    for report in self.unreviewed[author]:
                        if report.categories[1]:
                            if author not in reports:
                                reports[author] = []
                            reports[author].append(report)
                if not reports:
                    self.state = ReviewState.REVIEW_CANNOT_REVIEW
                    return ['No available unreviewed reports or reports in progress.']

                self.user_report_id = list(reports.keys())[0]
                report = self.unreviewed[self.user_report_id][0]
                offending_message = report.offending_message
                reporter = report.reporter_id
                await message.channel.send('Below is the reported content:')
                await message.channel.send(
                    "```" + offending_message.author.name + ": " + offending_message.content + "```")
                await message.channel.send('Reporting User ' + str(reporter) + ' has made ' + str(
                    self.data_manager.get_reports_confirmed(reporter))
                                           + ' previous reports with ' + str(
                    self.data_manager.get_trust_score(reporter)) + '% accuracy ')

                reply = 'What is the type of verbal abuse? Please select the corresponding number.\n'
                reply += '(1) Celebration of violent acts\n'
                reply += '(2) Denial of a violent event\n'
                reply += '(3) Dehumanization\n'
                reply += '(4) Inciting or encouraging violence\n'
                reply += '(5) Hate speech'
                self.state = ReviewState.REVIEW_VERBAL_ABUSE
                return [reply]

            if message.content == '3':
                # Make queue and get report
                reports = {}
                for author in self.unreviewed:
                    for report in self.unreviewed[author]:
                        if report.categories[2]:
                            if author not in reports:
                                reports[author] = []
                            reports[author].append(report)
                if not reports:
                    print('not reports')
                    self.state = ReviewState.REVIEW_CANNOT_REVIEW
                    return ['No available unreviewed reports or reports in progress.']

                self.user_report_id = list(reports.keys())[0]
                report = self.unreviewed[self.user_report_id][0]
                offending_message = report.offending_message
                reporter = report.reporter_id
                await message.channel.send('Below is the reported content:')
                await message.channel.send(
                    "```" + offending_message.author.name + ": " + offending_message.content + "```")
                await message.channel.send('Reporting User ' + str(reporter) + ' has made ' + str(
                    self.data_manager.get_reports_confirmed(reporter))
                                           + ' previous reports with ' + str(
                    self.data_manager.get_trust_score(reporter)) + '% accuracy ')

                reply = 'What is the type of harassment or intimidation? Please select the corresponding number.\n'
                reply += '(1) Threatening to post or posting private information\n'
                reply += '(2) Sexual harassment\n'
                reply += '(3) Stalking or threats to injure'
                self.state = ReviewState.REVIEW_HARASSMENT
                return [reply]

            if message.content == '4':
                # Make queue and get report
                reports = {}
                for author in self.unreviewed:
                    for report in self.unreviewed[author]:
                        if report.categories[3]:
                            if author not in reports:
                                reports[author] = []
                            reports[author].append(report)
                if not reports:
                    self.state = ReviewState.REVIEW_CANNOT_REVIEW
                    return ['No available unreviewed reports or reports in progress.']

                self.user_report_id = list(reports.keys())[0]
                report = self.unreviewed[self.user_report_id][0]
                offending_message = report.offending_message
                reporter = report.reporter_id
                await message.channel.send('Below is the reported content:')
                await message.channel.send("```" + offending_message.author.name + ": " + offending_message.content + "```")
                await message.channel.send('Reporting User ' + str(reporter) + ' has made ' + str(self.data_manager.get_reports_confirmed(reporter))
                                           + ' previous reports with ' + str(self.data_manager.get_trust_score(reporter)) + '% accuracy ')

                reply = 'What is the type of sensitive or disturbing content? Please select the corresponding number.\n'
                reply += '(1) Assault\n'
                reply += '(2) Self harm\n'
                reply += '(3) Beastiality\n'
                reply += '(4) Child exploitation'
                self.state = ReviewState.REVIEW_SENSITIVE
                return reply

            if message.content == '5':
                # Make queue and get report
                reports = {}
                for author in self.unreviewed:
                    for report in self.unreviewed[author]:
                        if report.categories[4]:
                            if author not in reports:
                                reports[author] = []
                            reports[author].append(report)
                if not reports:
                    self.state = ReviewState.REVIEW_CANNOT_REVIEW
                    return ['No available unreviewed reports or reports in progress.']

                self.user_report_id = list(reports.keys())[0]
                report = self.unreviewed[self.user_report_id][0]
                offending_message = report.offending_message
                reporter = report.reporter_id
                await message.channel.send('Below is the reported content:')
                await message.channel.send("```" + offending_message.author.name + ": " + offending_message.content + "```")
                await message.channel.send('Reporting User ' + str(reporter) + ' has made ' + str(self.data_manager.get_reports_confirmed(reporter))
                                           + ' previous reports with ' + str(self.data_manager.get_trust_score(reporter)) + '% accuracy ')
                self.state = ReviewState.REVIEW_OTHER
                return ['Does the content fit into any other violative category (yes/no)?']

            if message.content == '6':
                # Make queue and get report
                reports = {}
                if 'BOT' in self.unreviewed:
                    reports['BOT'] = self.unreviewed['BOT']
                if not reports:
                    self.state = ReviewState.REVIEW_CANNOT_REVIEW
                    return ['No available unreviewed reports or reports in progress.']

                self.user_report_id = list(reports.keys())[0]
                report = self.unreviewed[self.user_report_id][0]
                offending_message = report.offending_message
                reporter = report.reporter_id
                await message.channel.send('Below is the reported content:')
                await message.channel.send(
                    "```" + offending_message.author.name + ": " + offending_message.content + "```")
                await message.channel.send('Reporting User ' + str(reporter) + ' has made ' + str(
                    self.data_manager.get_reports_confirmed(reporter))
                                           + ' previous reports with ' + str(
                    self.data_manager.get_trust_score(reporter)) + '% accuracy ')
                self.state = ReviewState.REVIEW_BOT
                return ["What is the offense? Please respond with the corresponding number. "
                        "\n(1) Fraud\n(2) Verbal Abuse\n(3) Harassment/Threats of Violence"
                        "\n(4) Sensitive/Disturbing Content\n(5) Other\n"]

            return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_BOT and message.content in ('1', '2', '3', '4', '5'):
            if message.content == '1':
                reply = 'What is the type of fraud?\n'
                reply += '(1) Impersonation\n'
                reply += '(2) Scam\n'
                reply += '(3) Solicitation\n'
                self.state = ReviewState.REVIEW_FRAUD
                return [reply]

            if message.content == '2':
                reply = 'What is the type of verbal abuse? Please select the corresponding number.\n'
                reply += '(1) Celebration of violent acts\n'
                reply += '(2) Denial of a violent event\n'
                reply += '(3) Dehumanization\n'
                reply += '(4) Inciting or encouraging violence\n'
                reply += '(5) Hate speech'
                self.state = ReviewState.REVIEW_VERBAL_ABUSE
                return [reply]

            if message.content == '3':
                reply = 'What is the type of harassment or intimidation? Please select the corresponding number.\n'
                reply += '(1) Threatening to post or posting private information\n'
                reply += '(2) Sexual harassment\n'
                reply += '(3) Stalking or threats to injure'
                self.state = ReviewState.REVIEW_HARASSMENT
                return [reply]

            if message.content == '4':
                reply = 'What is the type of sensitive or disturbing content? Please select the corresponding number.\n'
                reply += '(1) Assault\n'
                reply += '(2) Self harm\n'
                reply += '(3) Beastiality\n'
                reply += '(4) Child exploitation'
                self.state = ReviewState.REVIEW_SENSITIVE
                return reply

            if message.content == '5':
                self.state = ReviewState.REVIEW_OTHER
                return ['Does the content fit into any other violative category (yes/no)?']

            return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_FRAUD:
            self.state = ReviewState.REVIEW_TIER_1

        if self.state == ReviewState.REVIEW_VERBAL_ABUSE:
            if message.content in ('1', '2', '3'):
                self.state = ReviewState.REVIEW_DISCRIMINATE_LOW
                return ['Does it discriminate based on inherited attributes and/or feature hate speech (yes/no)?']
            elif message.content == '4':
                self.state = ReviewState.REVIEW_DISCRIMINATE_HIGH
                return ['Does it discriminate based on inherited attributes and/or feature hate speech (yes/no)?']
            elif message.content == '5':
                self.state = ReviewState.REVIEW_INCITE_VIOLENCE
                return ['Does it encourage, incite, or threaten violence (yes/no)?']
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_HARASSMENT:
            if message.content == '1':
                self.state = ReviewState.REVIEW_DISCRIMINATE_HARASSMENT
                return ['Does it discriminate based on inherited attributes and/or feature hate speech (yes/no)?']
            elif message.content in ('2', '3'):
                self.state = ReviewState.REVIEW_TIER_3
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_SENSITIVE:
            if message.content in ('1', '2'):
                self.state = ReviewState.REVIEW_DISCRIMINATE_SENSITIVE
            elif message.content in ('3', '4'):
                self.state = ReviewState.REVIEW_TIER_4
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_OTHER and message.content in ('yes', 'no'):
            if message.content == 'no':
                self.state = ReviewState.REVIEW_ABUSIVE
                return ['Is the content abusive?']
            elif message.content == 'yes':
                reply = 'How would this abuse be categorized? Please select the corresponding number.\n'
                reply += '(0) Tier 0: Not abusive\n'
                reply += '(1) Tier 1: Low risk abuse\n'
                reply += '(2) Tier 2: Medium risk abuse\n'
                reply += '(3) Tier 3: High risk abuse\n'
                reply += '(4) Tier 4: Illegal/immediate risk abuse\n'
                reply += '(5) Tier 4: CSAM'
                self.state = ReviewState.REVIEW_DISCRETIONARY
                return [reply]
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_DEFAMATION and message.content in ('yes', 'no'):
            if message.content == 'no':
                self.state = ReviewState.REVIEW_DEROGATORY
                return ['Does it contain derogatory slurs and other intentionally abuse '
                        'language, including misgendering (yes/no)?']
            elif message.content == 'yes':
                self.state = ReviewState.REVIEW_TIER_3
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_DEROGATORY and message.content in ('yes', 'no'):
            if message.content == 'no':
                self.state = ReviewState.REVIEW_TIER_1
            elif message.content == 'yes':
                self.state = ReviewState.REVIEW_TIER_2
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_INCITE_VIOLENCE and message.content in ('yes', 'no'):
            if message.content == 'no':
                self.state = ReviewState.REVIEW_DEFAMATION
                return ['Does it involve defamation or the spreading of fear (yes/no)?']
            elif message.content == 'yes':
                self.state = ReviewState.REVIEW_TIER_4
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_DISCRIMINATE_SENSITIVE and message.content in ('yes', 'no'):
            if message.content == 'yes':
                self.state = ReviewState.REVIEW_INCITE_VIOLENCE
            elif message.content == 'no':
                self.state = ReviewState.REVIEW_TIER_1
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_DISCRIMINATE_HARASSMENT and message.content in ('yes', 'no'):
            if message.content == 'yes':
                self.state = ReviewState.REVIEW_INCITE_VIOLENCE
            elif message.content == 'no':
                self.state = ReviewState.REVIEW_TIER_3
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_DISCRIMINATE_LOW and message.content in ('yes', 'no'):
            if message.content == 'no':
                self.state = ReviewState.REVIEW_TIER_1
            elif message.content == 'yes':
                self.state = ReviewState.REVIEW_DEFAMATION
                return ['Does it involve defamation or the spreading of fear (yes/no)?']
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_DISCRIMINATE_HIGH and message.content in ('yes', 'no'):
            if message.content == 'no':
                self.state = ReviewState.REVIEW_TIER_3
            elif message.content == 'yes':
                self.state = ReviewState.REVIEW_TIER_4
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_ABUSIVE and message.content in ('yes', 'no'):
            if message.content == 'no':
                self.state = ReviewState.REVIEW_TIER_0
            elif message.content == 'yes':
                self.state = ReviewState.REVIEW_TIER_1
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_DISCRETIONARY and message.content in ('0', '1', '2', '3', '4', '5'):
            if message.content == '0':
                self.state = ReviewState.REVIEW_TIER_0
            if message.content == '1':
                self.state = ReviewState.REVIEW_TIER_1
            if message.content == '2':
                self.state = ReviewState.REVIEW_TIER_2
            if message.content == '3':
                self.state = ReviewState.REVIEW_TIER_3
            if message.content == '4':
                self.state = ReviewState.REVIEW_TIER_4
            if message.content == '5':
                self.state = ReviewState.REVIEW_TIER_4_CSAM
            else:
                return ['Please select a valid option.']

        if self.state == ReviewState.REVIEW_TIER_0:
            self.state = ReviewState.REVIEW_COMPLETE
            self.noaction = True
            return ['Notified reporter that the behavior is not abusive. Provided them with an option to dispute.']

        if self.state == ReviewState.REVIEW_TIER_1:
            self.state = ReviewState.REVIEW_COMPLETE
            return ["Removed content. Gave the offending user a warning."]

        if self.state == ReviewState.REVIEW_TIER_2:
            self.state = ReviewState.REVIEW_COMPLETE
            return ["Removed content. Gave the offending user a one-day mute."]

        if self.state == ReviewState.REVIEW_TIER_3:
            self.state = ReviewState.REVIEW_COMPLETE
            return ["Removed content. Gave the offending user a one-week mute."]

        if self.state == ReviewState.REVIEW_TIER_4:
            self.state = ReviewState.REVIEW_COMPLETE
            return ["Removed content. Permanently banned the offending user. "
                    "Stored content securely as required by law."]

        if self.state == ReviewState.REVIEW_TIER_4_CSAM:
            self.state = ReviewState.REVIEW_COMPLETE
            return ["Removed content. Permanently banned the offending user. "
                    "Stored content securely as required by law. Reported to NCMEC."]

        if self.state == ReviewState.REVIEW_CANNOT_REVIEW:
            return ['Review closed.']

        else:
            return ['Invalid action. Please select only valid actions.']

    def cannot_review(self):
        return self.state == ReviewState.REVIEW_CANNOT_REVIEW

    def review_complete(self):
        return self.state == ReviewState.REVIEW_COMPLETE

    def review_cancelled(self):
        return self.state == ReviewState.REVIEW_CANCELLED
