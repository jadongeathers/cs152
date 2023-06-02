class ReportInfo:
    def __init__(self):
        self.total_reports_filed = 0
        self.total_reports_confirmed = 0
        self.accurate_reports = 0

    def get_percentage(self):
        return self.accurate_reports / self.total_reports_confirmed

# new user is created
# user_report_info[user_id] = ReportInfo()

# to access it in the future
# user_report_info[user_id].get_percentage()...
class DataManager:
    def __init__(self):
        self.trust_scores = dict()
        self.user_report_info = dict()

    def get_trust_score(self, user):
        self.user_report_info[user].get_percentage()

    def add_user_report(self, user):
        if user not in self.user_report_info:
            self.user_report_info[user] = ReportInfo()
        self.user_report_info[user].total_reports_filed += 1

    def add_true_report(self, user):
        self.user_report_info[user].accurate_reports += 1




    """Step 1"""
    # make a command to allow the moderator to view a trust score

    """Step 2"""
    # take in a username or user id, etc, and
    # return the trust score for that user
    #   -- find out how to get the user in question (user.name in the Member class)
    # message -> channel obj -> list of members -> member obj --> name

    """Step 3"""
    # increment total report count and accurate report count
    # with the correct user object, return their trust score
    #   -- user_report_info[user_id].get_percentage()

