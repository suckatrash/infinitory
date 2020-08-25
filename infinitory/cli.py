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
from pypuppetdb import connect
from google.cloud import storage

def output_html(inventory, directory, bucket_name):
    if os.path.isdir(directory):
        shutil.rmtree(directory)
    os.mkdir(directory, 0o755)

    shutil.copytree(
        "{}/static".format(os.path.dirname(os.path.abspath(__file__))),
        "{}/static".format(directory))

    with open("{}/pygments.css".format(directory), "w", encoding="utf-8") as css:
        css.write(pygments.formatters.HtmlFormatter().get_style_defs('.codehilite'))
    gcs_upload(bucket_name=bucket_name, source_file_name="{}/pygments.css".format(directory), destination_blob_name="pygments.css")

    os.mkdir("{}/errors".format(directory), 0o755)
    os.mkdir("{}/nodes".format(directory), 0o755)
    nodes = inventory.sorted_nodes("facts", "fqdn")
    generation_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

    with open("{}/index.html".format(directory), "w", encoding="utf-8") as html:
        html.write(
            render_template("home.html",
                path="",
                generation_time=generation_time))
    gcs_upload(bucket_name=bucket_name, source_file_name="{}/index.html".format(directory), destination_blob_name="index.html")

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
    gcs_upload(bucket_name=bucket_name, source_file_name="{}/errors/index.html".format(directory), destination_blob_name="errors/index.html")

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
    gcs_upload(bucket_name=bucket_name, source_file_name="{}/errors/all.html".format(directory), destination_blob_name="errors/all.html")


    with open("{}/nodes/index.html".format(directory), "w", encoding="utf-8") as html:
        html.write(
            render_template("nodes.html",
                path="../",
                generation_time=generation_time,
                columns=report_columns,
                nodes=nodes))
    gcs_upload(bucket_name=bucket_name, source_file_name="{}/nodes/index.html".format(directory), destination_blob_name="nodes/index.html")


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
    gcs_upload(bucket_name=bucket_name, source_file_name="{}/nodes.csv".format(directory), destination_blob_name="nodes.csv")


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
        gcs_upload(bucket_name=bucket_name, source_file_name="{}/nodes/{}.html".format(directory, node["certname"]), destination_blob_name="nodes/{}.html".format(node["certname"]))

    os.mkdir("{}/roles".format(directory), 0o755)
    with open("{}/roles/index.html".format(directory), "w", encoding="utf-8") as html:
        html.write(
            render_template("roles.html",
                path="../",
                generation_time=generation_time,
                roles=inventory.sorted_roles()))
    gcs_upload(bucket_name=bucket_name, source_file_name="{}/roles/index.html".format(directory), destination_blob_name="roles/index.html")


    os.mkdir("{}/services".format(directory), 0o755)
    sorted_services = inventory.sorted_services()

    with open("{}/services/index.html".format(directory), "w", encoding="utf-8") as html:
        html.write(
            render_template("services.html",
                path="../",
                generation_time=generation_time,
                services=sorted_services))
    gcs_upload(bucket_name=bucket_name, source_file_name="{}/services/index.html".format(directory), destination_blob_name="services/index.html")


    for service in sorted_services:
        path = "{}/services/{}.html".format(directory, service["class_name"])
        with open(path, "w", encoding="utf-8") as html:
            html.write(
                render_template("service.html",
                    path="../",
                    generation_time=generation_time,
                    service=service))
        gcs_upload(bucket_name=bucket_name, source_file_name="{}/services/{}.html".format(directory, service["class_name"]), destination_blob_name="services/{}.html".format(service["class_name"]))


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

def gcs_upload(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)
    
@click.command()
@click.option("--output", "-o", required=True, metavar="PATH", help="Directory to put report in. WARNING: this directory will be removed if it already exists.")
@click.option("--host", "-h", default="localhost", metavar="HOST", help="PuppetDB host to query")
@click.option("--token", "-t", default="123token", metavar="TOKEN", help="RBAC auth token to use")
@click.option("--verbose", "-v", default=False, is_flag=True)
@click.option("--debug", "-d", default=False, is_flag=True)
@click.option("--bucket", "-b", default="bucket", metavar="BUCKET", help="Bucket to save files to, such as GCS")
@click.version_option()
def main(host, token, output, bucket, verbose, debug ):
    """Generate SRE inventory report"""
    if debug:
        set_up_logging(logging.DEBUG)
    elif verbose:
        set_up_logging(logging.INFO)
    else:
        set_up_logging(logging.WARNING)

    pupdb = connect(host=host, port=8081, timeout=30, token=token)
    try:
        inventory = Inventory(debug=debug)
        inventory.add_active_filter()
        
        inventory.load_nodes(pupdb)
        inventory.load_errors(pupdb)
        inventory.load_backups(pupdb)
        inventory.load_logging(pupdb)
        inventory.load_metrics(pupdb)
        inventory.load_monitoring(pupdb)
        inventory.load_roles(pupdb)

        output_html(inventory, output, bucket_name=bucket)
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
