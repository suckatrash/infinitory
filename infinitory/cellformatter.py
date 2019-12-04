# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

from jinja2 import Markup
from operator import itemgetter
import re


class Base(object):
    def __init__(self, section, key, header=None):
        self.section = section
        self.key = key

        if header is None:
            self.header = key
        else:
            self.header = header

        if re.search(r"[^a-zA-Z0-9_-]", key):
            raise ValueError("Invalid key: {}".format(key))

    def body_class(self, record):
        return ["key_{}".format(self.key)]

    def head_html(self):
        return Markup('<th class="key_%s">%s</th>') % (self.key, self.header)

    def body_html(self, record):
        return Markup('<td class="%s">%s</td>') % (" ".join(self.body_class(record)), self.value_html(record))

    def value_html(self, record):
        return self.value(record)

    def head_csv(self):
        return self.header

    def body_csv(self, record):
        return self.value_csv(record)

    def value_csv(self, record):
        return self.value(record)

    def value(self, record):
        if record[self.section] is None:
            return ""
        else:
            return record[self.section].get(self.key, None) or ""

class Boolean(Base):
    def body_class(self, record):
        return super(Boolean, self).body_class(record) \
            + [("true" if self.value(record) else "false")]

    def value_html(self, record):
        return u"✔︎" if self.value(record) else ""

    def value_csv(self, record):
        return "Y" if self.value(record) else "N"


class TruncatedList(Base):
    def value_html(self, record):
        items = [self.item_html(i) for i in self.value(record)]
        return Markup("<ol>%s</ol>") % Markup("\n").join(items[:5])

    def item_html(self, item):
        return Markup("<li>%s</li>") % item

    def value_csv(self, record):
        return "\n".join([self.item_csv(i) for i in self.value(record)])

    def item_csv(self, item):
        return item


class List(Base):
    def value_html(self, record):
        items = [self.item_html(i) for i in self.value(record)]
        return Markup("<ol>%s</ol>") % Markup("\n").join(items)

    def item_html(self, item):
        return Markup("<li>%s</li>") % item

    def value_csv(self, record):
        return "\n".join([self.item_csv(i) for i in self.value(record)])

    def item_csv(self, item):
        return item


class Set(Base):
    def value_html(self, record):
        items = [self.item_html(i) for i in self.value(record)]

        # set() is used here to dedupe things that can't be put into a set in
        # value(), like a list of dicts()
        return Markup("<ul>%s</ul>") % Markup("\n").join(set(items))

    def item_html(self, item):
        return Markup("<li>%s</li>") % item

    def value_csv(self, record):
        return "\n".join(set([self.item_csv(i) for i in self.value(record)]))

    def item_csv(self, item):
        return item

    def value(self, record):
        return sorted(set(record[self.section].get(self.key, [])))


class Roles(Set):
    def item_html(self, role):
        return Markup('<li><a href="../roles/index.html#%s">%s</a></li>') % (role, role)


class Services(Set):
    def value(self, record):
        profile_metadata = record["facts"].get("profile_metadata", dict())
        return sorted(profile_metadata.get("services", list()), key=itemgetter("human_name"))

    def item_html(self, service):
        return Markup('<li><a href="../services/%s.html">%s</a></li>') % (
            service["class_name"],
            service["human_name"])

    def item_csv(self, service):
        return service["class_name"]


class Owners(Services):
    def item_html(self, service):
        if service.get("owner_uid", ":undef") == ":undef":
            return ""
        else:
            return Markup('<li>%s</li>') % service["owner_uid"]

    def item_csv(self, service):
        if service.get("owner_uid", ":undef") == ":undef":
            return ""
        else:
            return service["owner_uid"]


class Teams(Services):
    def item_html(self, service):
        if service.get("team", ":undef") == ":undef":
            return ""
        else:
            return Markup('<li>%s</li>') % service["team"]

    def item_csv(self, service):
        if service.get("team", ":undef") == ":undef":
            return ""
        else:
            return service["team"]


class Fqdn(Base):
    def body_html(self, record):
        # Use th instead of td:
        return Markup('<th class="%s">%s</th>') % (
            " ".join(self.body_class(record)),
            self.value_html(record))

    def value_html(self, record):
        if "hostname" not in record["facts"]:
            return Markup('<a href="%s.html">%s</a>') % (
                record["certname"],
                record["certname"])
        elif "domain" not in record["facts"]:
            return Markup('<a href="%s.html"><b>%s</b></a>') % (
                record["certname"],
                record["facts"]["hostname"])
        else:
            return Markup(
                '<a href="%s.html"><b>%s<span>.</span></b><i>%s</i></a>') % (
                record["certname"],
                record["facts"]["hostname"],
                record["facts"]["domain"])


class Os(Base):
    def value(self, record):
        os_fact = record["facts"].get("os", dict())
        os = [os_fact.get("name", "")]

        try:
            os.append(os_fact["release"]["full"])
        except KeyError:
            pass

        return " ".join(os)
