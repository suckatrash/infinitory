SRE Inventory Report
====================

Generate a report on SRE inventory, including hosts, roles, and
services.

## Architecture

This app has two components:

`infinitory` - the data colection portion. Which can be run in cron or otherwise scheduled to collect data from Puppetdb using token authentication. Data can be stored locally as well as  pushed to a GCS bucket. 

`infinitory-flask` - the web frontend portion. This can be pointed to resources collected by the `infinitory` (cron) app and serves data from the GCS bucket

## Running in Docker

`infinitory`
```
docker run -e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS -e BUCKET=<GCP_BUCKET_NAME> -e TOKEN=<PDB_ACCESS_TOKEN> -v /tmp:/output:rw --add-host <pdb-host>:<pdb-hostip> infinitory-app
```

`infinitory-flask`
```
docker run -e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS -e BUCKET=<GCP_BUCKET_NAME> infinitory-flask
```

Using `GOOGLE_APPLICATION_CREDENTIALS` may require an extra volume mount in some cases:

```
-v /path/to/creds.json:/creds.json
```

...where your ENV variable points to that file:

```
export GOOGLE_APPLICATION_CREDENTIALS=/creds.json
```

## Developing

Use python setup.py develop to install dependencies

Running `infinitory` in Dev:

```
bin/infinitory -h pdb.ops.puppetlabs.net -t <pdb-access-token> -o /tmp/output -b <gcs-bucket-name>
```

Running `infinitory-flask` in Dev:

```
infinitory-flask/python app.py infinitory-prod
```

### Build / release

`infinitory` - For infinitory, you must first release the python package and then build / push the docker image
```
## Release a python build
## (with .pypirc in place)
python setup.py sdist upload -r local

```

`infinitory-flask` - Simply build and push the docker image to release this portion of the app.
