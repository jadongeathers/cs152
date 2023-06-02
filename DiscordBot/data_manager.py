class ReportInfo:
    def __init__(self):
        self.total_reports_filed = 0
        self.total_reports_confirmed = 0
        self.accurate_reports = 0

    def get_percentage(self):
        if self.total_reports_confirmed == 0:
            return None
        return 100 * self.accurate_reports / self.total_reports_confirmed


class DataManager:
    def __init__(self):
        # creates dictionary wheere userids mad to ReportInfo structs
        self.user_report_info = dict()

    def get_trust_score(self, user):
        return self.user_report_info[user].get_percentage()

    # when a user makes a report, adds it to user statistics
    def add_user_report(self, user):
        if user not in self.user_report_info:
            self.user_report_info[user] = ReportInfo()
        self.user_report_info[user].total_reports_filed += 1

    # returns number of reports a user has made than have been reviewd by mod team
    def get_reports_confirmed(self, user):
        return self.user_report_info[user].total_reports_confirmed

    # when mod team has revirew a user's report, statistic is kept for that user
    def add_confirmed_report(self, user):
        self.user_report_info[user].total_reports_confirmed += 1

    # increases count of accurate reports
    def add_true_report(self, user):
        self.user_report_info[user].accurate_reports += 1

