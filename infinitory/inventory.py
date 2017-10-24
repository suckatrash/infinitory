from collections import defaultdict
from operator import itemgetter
from simplepup import puppetdb

class Inventory(object):
    def __init__(self, filters=set()):
        self.filter = puppetdb.QueryFilter(filters)
        self.nodes = None
        self.roles = None

    def add_active_filter(self):
        self.filter.add("nodes { deactivated is null and expired is null }")

    def add_filter(self, filter):
        self.filter.add(filter)

    def load_nodes(self, pdb):
        self.nodes = dict()
        for node in pdb.query(self.filter('inventory {}')):
            node["other"] = defaultdict(list)
            self.nodes[node["certname"]] = node

    def query_classes(self, pdb, class_name):
        return self.query_resources(pdb,
            'title="%s" and type="Class"' % class_name)

    def query_resources(self, pdb, condition, include_absent=False):
        for resource in pdb.query(self.filter('resources {}', condition)):
            if not include_absent:
                if resource["parameters"].get("ensure", None) == "absent":
                    continue

            try:
                yield self.nodes[resource["certname"]], resource
            except KeyError:
                continue

    def load_backups(self, pdb):
        for node, resource in self.query_resources(pdb, 'type="Backup::Job"'):
            paths = resource["parameters"]["files"]
            if type(paths) is list:
                node["other"]["backups"].extend(paths)
            else:
                node["other"]["backups"].append(paths)

    def load_logging(self, pdb):
        for node, resource in self.query_classes(pdb, "Profile::Logging::Rsyslog::Client"):
            node["other"]["logging"] = True

    def load_metrics(self, pdb):
        for node, resource in self.query_classes(pdb, "Profile::Metrics"):
            node["other"]["metrics"] = True

    def load_monitoring(self, pdb):
        for node, resource in self.query_classes(pdb, "Profile::Server::Monitor"):
            node["other"]["monitoring"] = True

        for node, resource in self.query_classes(pdb, "Profile::Monitoring::Icinga2::Common"):
            node["other"]["icinga_notification_period"] = resource["parameters"]["notification_period"]
            node["other"]["icinga_environment"] = resource["parameters"]["icinga2_environment"]
            node["other"]["icinga_owner"] = resource["parameters"]["owner"]

    def load_roles(self, pdb):
        self.roles = defaultdict(list)

        condition = 'type = "Profile::Motd::Register" and file ~ "/site[.]pp$"'
        for node, resource in self.query_resources(pdb, condition):
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

