import logging
import os
import pickle
import sys
import time

from datetime import datetime


class ErrorParser(object):
    def __init__(self, debug=False):
        self.all_errors = []
        self.reports_cache_path = '/tmp/infinitory_cache'
        self.debug = debug
        self._logger = logging.getLogger()
        self._reports = dict()
        self.unique_errors = []
        self.delete_report_cache()

    def delete_report_cache(self):
        if not os.path.isdir(self.reports_cache_path):
            os.mkdir(self.reports_cache_path)

        for file in os.listdir(self.reports_cache_path):
            # Delete cache item if older than 2 hours
            absolute_cache_file_path = os.path.join(self.reports_cache_path,file)
            time_one_hour_ago = time.mktime(datetime.now().timetuple()) - (1 * 3600)
            if os.stat(absolute_cache_file_path).st_mtime < time_one_hour_ago:
                print("Deleting File " + absolute_cache_file_path)
                os.remove(absolute_cache_file_path)

    def load_reports(self, pupdb):
        """ I didn't use a subquery because it takes much longer than loading
        the reports one by one """
        for report in pupdb._query('nodes', query='["extract", ["certname", "latest_report_hash"]]'):
            if report["latest_report_hash"] != None:
                cache_file = "%s/%s" % (self.reports_cache_path, report["latest_report_hash"])
                if os.path.isfile(cache_file):
                    full_report = pickle.load(open(cache_file, "rb"))
                    if self.debug:
                        sys.stdout.write('#')
                else:
                    query = '["=", "hash", "%s"]' % report["latest_report_hash"]
                    full_report = pupdb._query('reports', query=query)
                    pickle.dump( full_report, open(cache_file, "wb" ) )
                    if self.debug:
                        sys.stdout.write('.')
                sys.stdout.flush()

                self._reports[report["certname"]] = full_report[0]

    def common_error_prefixes(self):
        return [
            "Could not retrieve catalog from remote server: Error 500 on SERVER: Server Error: Evaluation Error: Error while evaluating a Function Call, Untrusted facts (left) don't match values from certname (right)"
        ]

    def matches_stored_error(self, message):
        for se in self.common_error_prefixes():
            if message.startswith(se):
                return se

        return None

    def clean_error_message(self, error_message):
        stored_error = self.matches_stored_error(error_message)

        if stored_error:
            return stored_error

        return error_message

    def modify_unique_errors_at(self, i, log_level, certname):

        new_certname_list = self.unique_errors[i]['certnames']
        new_certname_list.add(certname)

        self.unique_errors[i] = {
            'count': self.unique_errors[i]['count'] + 1,
            'level': log_level,
            'certnames': new_certname_list,
            'message': self.unique_errors[i]['message']
        }

    def append_unique_error(self, error_message, log_level, certname):
        for i, ue in enumerate(self.unique_errors):
            if ue['message'] == error_message:
                self.modify_unique_errors_at(i, log_level, certname)
                return

        self.unique_errors.append({
            'count': 1,
            'level': log_level,
            'certnames': set([certname]),
            'message': error_message,
        })

    def extract_errors_from_reports(self):
        for node, report in self._reports.items():

            self._logger.debug("%s -- %s" % (report["certname"], report["status"]))
            for log_message in report['logs']['data']:
                if log_message['level'] == 'err' or log_message['level'] == 'warning':
                    error = {
                        'level': log_message['level'],
                        'hostname': report["certname"],
                        'message': log_message['message']
                    }

                    self.all_errors.append(error)

                    error_message = self.clean_error_message(error['message'])

                    self.append_unique_error(
                        error_message,
                        log_message['level'],
                        report['certname']
                    )
