import os
import logging
import shutil
import sys
from flask import Flask, send_file, Response
from google.cloud import storage
import tempfile

app = Flask(__name__)
app.config['root_path'] = '/'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['static_url_path'] = '/static'
app.config['static_folder'] = 'static'

bucket = sys.argv[1]

if os.path.isdir('templates'):
    shutil.rmtree('templates')
os.mkdir('templates', 0o755)

if os.path.isdir('static'):
    shutil.rmtree('static')
os.mkdir('static', 0o755)

client = storage.Client()
bucket = client.get_bucket(bucket)

css = bucket.get_blob('pygments.css')
css.download_to_filename("templates/pygments.css")

static = bucket.list_blobs(prefix='static')
for b in static:
    destination_uri = '{}'.format(b.name)
    b.download_to_filename(destination_uri)

@app.route('/nodes/<string:page_name>/')
def render_static_node_page(page_name):
    return fetch_bucket_resource("nodes/"+page_name)

@app.route('/roles/<string:page_name>/')
def render_static_roles_page(page_name):
    return fetch_bucket_resource("roles/"+page_name)

@app.route('/services/<string:page_name>/')
def render_static_services_page(page_name):
    return fetch_bucket_resource("services/"+page_name)

@app.route('/errors/<string:page_name>/')
def render_static_errors_page(page_name):
    return fetch_bucket_resource("errors/"+page_name)

@app.route('/')
@app.route('/index.html/')
def render_index():
    return fetch_bucket_resource('index.html')

def fetch_bucket_resource(blob_path):
    blob = bucket.get_blob(blob_path)
    with tempfile.NamedTemporaryFile() as temp:
        blob.download_to_filename(temp.name)
        return send_file(temp.name, mimetype='html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
