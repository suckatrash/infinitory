from collections import defaultdict
from operator import itemgetter
from simplepup import puppetdb
from pypuppetdb import connect

import infinitory.errors as errors

class Inventory(object):
    def __init__(self, filters=set(), debug=False):
        self.debug = debug
        self.errorParser = errors.ErrorParser(debug=debug)
        self.filter = puppetdb.QueryFilter(filters)
        self.nodes = None
        self.roles = None

    def add_active_filter(self):
        self.filter.add("nodes { deactivated is null and expired is null }")

    def add_filter(self, filter):
        self.filter.add(filter)

    def load_nodes(self, pupdb):
        self.nodes = dict()
        for node in pupdb._query('inventory'):
            node["other"] = defaultdict(list)
            self.nodes[node["certname"]] = node

    def query_classes(self, pupdb, class_name):
        return self.query_resources(pupdb,
            '["and", ["=", "title", "%s"], ["=", "type", "Class"]]' % class_name)

    def query_resources(self, pupdb, condition, include_absent=False):
        for resource in pupdb._query('resources', query=condition):
            if not include_absent:
                if resource["parameters"].get("ensure", None) == "absent":
                    continue

            try:
                yield self.nodes[resource["certname"]], resource
            except KeyError:
                continue

    def load_backups(self, pupdb):
        for node, resource in self.query_resources(pupdb, '["=", "type", "Backup::Job"]'):
            paths = resource["parameters"]["files"]
            if type(paths) is list:
                node["other"]["backups"].extend(paths)
            else:
                node["other"]["backups"].append(paths)

    def load_errors(self, pupdb):
        self.errorParser.load_reports(pupdb)
        self.errorParser.extract_errors_from_reports()

    def wrap_with_category(self, list_of_hashes, category):
        retval = []
        for error in list_of_hashes:
            retval.append({
                category: error
            })
        return retval

    def unique_errors(self):
        return self.wrap_with_category(self.errorParser.unique_errors, "other")

    def all_errors(self):
        return self.wrap_with_category(self.errorParser.all_errors, "other")

    def load_logging(self, pupdb):
        for node, resource in self.query_classes(pupdb, "Profile::Logging::Rsyslog::Client"):
            node["other"]["logging"] = True

    def load_metrics(self, pupdb):
        for node, resource in self.query_classes(pupdb, "Profile::Metrics"):
            node["other"]["metrics"] = True

    def load_monitoring(self, pupdb):
        for node, resource in self.query_classes(pupdb, "Profile::Server::Monitor"):
            node["other"]["monitoring"] = True

        for node, resource in self.query_classes(pupdb, "Profile::Monitoring::Icinga2::Common"):
            node["other"]["icinga_notification_period"] = resource["parameters"]["notification_period"]
            node["other"]["icinga_environment"] = resource["parameters"]["icinga2_environment"]
            node["other"]["icinga_owner"] = resource["parameters"]["owner"]

    def load_roles(self, pupdb):
        self.roles = defaultdict(list)

        condition = '["and", ["=", "type", "Class"], ["~", "title", "^Role::"]]'
        for node, resource in self.query_resources(pupdb, condition):
            if resource["title"] not in ("role", "role::delivery"):
                node["other"]["roles"].append(resource["title"])
                self.roles[resource["title"]].append(node)

    def sorted_nodes(self, section, key):
        return sorted(
            self.nodes.values(),
            key=lambda node: node.get(section, dict()).get(key, ""))

    def sorted_roles(self):
        return sorted(self.roles.items())

    def sorted_services(self):
        services = dict()

        for node in self.nodes.values():
            profile_metadata = node["facts"].get("profile_metadata", dict())
            service_facts = profile_metadata.get("services", list())

            for service_fact in service_facts:
                class_name = service_fact["class_name"]
                if class_name not in services:
                    services[class_name] = service_fact
                    services[class_name]["nodes"] = list()

                services[class_name]["nodes"].append(node)

        return sorted(services.values(), key=itemgetter("human_name"))
