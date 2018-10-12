#!/usr/bin/env python3

import click
import csv
from datetime import datetime
import jinja2
import json
import logging
import os
import markdown2
import paramiko.ssh_exception
import pygments.formatters
import re
import requests
import socket
import shutil
import sys

from infinitory import cellformatter
from infinitory.inventory import Inventory
from simplepup import puppetdb


def output_html(inventory, directory):
    if os.path.isdir(directory):
        shutil.rmtree(directory)
    os.mkdir(directory, 0o755)

    shutil.copytree(
        "{}/static".format(os.path.dirname(os.path.abspath(__file__))),
        "{}/static".format(directory))

    with open("{}/pygments.css".format(directory), "w", encoding="utf-8") as css:
        css.write(pygments.formatters.HtmlFormatter().get_style_defs('.codehilite'))

    os.mkdir("{}/errors".format(directory), 0o755)
    os.mkdir("{}/nodes".format(directory), 0o755)
    nodes = inventory.sorted_nodes("facts", "fqdn")
    generation_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

    with open("{}/index.html".format(directory), "w", encoding="utf-8") as html:
        html.write(
            render_template("home.html",
                path="",
                generation_time=generation_time))

    report_columns = [
        cellformatter.Fqdn("facts", "fqdn"),
        cellformatter.Teams("other", "teams"),
        cellformatter.Services("other", "services"),
        cellformatter.Boolean("other", "monitoring"),
        cellformatter.Boolean("other", "backups"),
        cellformatter.Boolean("other", "logging"),
        cellformatter.Boolean("other", "metrics"),
        cellformatter.Roles("other", "roles"),
    ]

    unique_error_columns = [
        cellformatter.Base("other", "count"),
        cellformatter.Base("other", "level"),
        cellformatter.Base("other", "message"),
        cellformatter.TruncatedList("other", "certnames"),
    ]

    unique_errors = inventory.unique_errors()

    with open("{}/errors/index.html".format(directory), "w", encoding="utf-8") as html:
        html.write(
            render_template("errors.html",
                path="../",
                generation_time=generation_time,
                columns=unique_error_columns,
                errors=unique_errors))

    all_error_columns = [
        cellformatter.Base("other", "message"),
        cellformatter.Base("other", "level"),
        cellformatter.Base("other", "certname"),
    ]

    all_errors = inventory.all_errors()

    with open("{}/errors/all.html".format(directory), "w", encoding="utf-8") as html:
        html.write(
            render_template("all_errors.html",
                path="../",
                generation_time=generation_time,
                columns=all_error_columns,
                errors=unique_errors))

    with open("{}/nodes/index.html".format(directory), "w", encoding="utf-8") as html:
        html.write(
            render_template("nodes.html",
                path="../",
                generation_time=generation_time,
                columns=report_columns,
                nodes=nodes))

    all_columns = [
        cellformatter.Base("facts", "fqdn"),
        cellformatter.Teams("other", "teams"),
        cellformatter.Owners("other", "owners"),
        cellformatter.Services("other", "services"),
        cellformatter.Base("other", "icinga_notification_period", "Icinga notification period"),
        cellformatter.Base("other", "icinga_stage", header="Icinga stage"),
        cellformatter.Base("other", "icinga_owner", header="Icinga owner"),
        cellformatter.Set("other", "backups"),
        cellformatter.Boolean("other", "logging"),
        cellformatter.Boolean("other", "metrics"),
        cellformatter.Base("facts", "whereami"),
        cellformatter.Base("facts", "primary_ip"),
        cellformatter.Os("facts", "os"),
        cellformatter.Roles("other", "roles"),
        cellformatter.Base("trusted", "certname"),
        cellformatter.Base("facts", "group"),
        cellformatter.Base("facts", "function"),
        cellformatter.Base("facts", "context"),
        cellformatter.Base("facts", "stage"),
        cellformatter.Base("facts", "function_number"),
    ]

    with open("{}/nodes.csv".format(directory), "w", encoding="utf-8") as out:
        csv_writer = csv.writer(out, lineterminator="\n")
        csv_writer.writerow([cell.head_csv() for cell in all_columns])
        for node in nodes:
            csv_writer.writerow([cell.body_csv(node) for cell in all_columns])

    write_json(nodes, directory, "index")

    for node in nodes:
        path = "{}/nodes/{}.html".format(directory, node["certname"])
        with open(path, "w", encoding="utf-8") as html:
            html.write(
                render_template("node.html",
                    path="../",
                    generation_time=generation_time,
                    columns=all_columns[1:],
                    node=node))

    os.mkdir("{}/roles".format(directory), 0o755)
    with open("{}/roles/index.html".format(directory), "w", encoding="utf-8") as html:
        html.write(
            render_template("roles.html",
                path="../",
                generation_time=generation_time,
                roles=inventory.sorted_roles()))

    os.mkdir("{}/services".format(directory), 0o755)
    sorted_services = inventory.sorted_services()

    with open("{}/services/index.html".format(directory), "w", encoding="utf-8") as html:
        html.write(
            render_template("services.html",
                path="../",
                generation_time=generation_time,
                services=sorted_services))

    for service in sorted_services:
        path = "{}/services/{}.html".format(directory, service["class_name"])
        with open(path, "w", encoding="utf-8") as html:
            html.write(
                render_template("service.html",
                    path="../",
                    generation_time=generation_time,
                    service=service))


def render_template(template_name, **kwargs):
    data_path = os.path.dirname(os.path.abspath(__file__))
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader("{}/templates".format(data_path)),
        autoescape=jinja2.select_autoescape(default=True))

    md = markdown2.Markdown(extras=[
        'fenced-code-blocks',
        'cuddled-lists',
        'tables'])
    def markdown_filter(value):
        return jinja2.Markup(md.convert(value))
    environment.filters['markdown'] = markdown_filter

    def unundef(value):
        return "" if value == ":undef" else value
    environment.filters['unundef'] = unundef

    _paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
    def nl2br(value):
        return jinja2.Markup(
            u'\n\n'.join(u'<p>%s</p>'
                % jinja2.Markup.escape(p) for p in _paragraph_re.split(value)))
    environment.filters['nl2br'] = nl2br

    body_id = re.sub(r"\W+", "_", re.sub(r"\..*", "", template_name))
    template = environment.get_template(template_name)
    return template.render(body_id=body_id, **kwargs)

def set_up_logging(level=logging.WARNING):
    logging.captureWarnings(True)

    handler = logging.StreamHandler(stream=sys.stdout)
    try:
        import colorlog
        handler.setFormatter(colorlog.ColoredFormatter(
            "%(log_color)s%(name)s[%(processName)s]: %(message)s"))
    except ImportError:
        handler.setFormatter(logging.Formatter("%(name)s[%(processName)s]: %(message)s"))

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    logging.getLogger("paramiko").setLevel(logging.FATAL)

def write_json(nodes, directory, filename):
    path = "{}/nodes/{}.json".format(directory, filename)
    with open(path, "w", encoding="utf-8") as json_out:
        json_out.write(json.dumps(nodes))

@click.command()
@click.option("--output", "-o", required=True, metavar="PATH", help="Directory to put report in. WARNING: this directory will be removed if it already exists.")
@click.option("--host", "-h", default="localhost", metavar="HOST", help="PuppetDB host to query")
@click.option("--verbose", "-v", default=False, is_flag=True)
@click.option("--debug", "-d", default=False, is_flag=True)
@click.version_option()
def main(host, output, verbose, debug):
    """Generate SRE inventory report"""
    if debug:
        set_up_logging(logging.DEBUG)
    elif verbose:
        set_up_logging(logging.INFO)
    else:
        set_up_logging(logging.WARNING)

    try:
        inventory = Inventory(debug=debug)
        inventory.add_active_filter()

        with puppetdb.AutomaticConnection(host) as pupdb:
            inventory.load_nodes(pupdb)
            inventory.load_errors(pupdb)
            inventory.load_backups(pupdb)
            inventory.load_logging(pupdb)
            inventory.load_metrics(pupdb)
            inventory.load_monitoring(pupdb)
            inventory.load_roles(pupdb)

        output_html(inventory, output)
    except socket.gaierror as e:
        sys.exit("PuppetDB connection (Socket): {}".format(e))
    except paramiko.ssh_exception.SSHException as e:
        sys.exit("PuppetDB connection (SSH): {}".format(e))
    except puppetdb.ResponseError as e:
        sys.exit(e)
    except puppetdb.QueryError as e:
        sys.exit(e)
    except requests.exceptions.ConnectionError as e:
        sys.exit(e)
