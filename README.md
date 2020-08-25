SRE Inventory Report
====================

Generate a report on SRE inventory, including hosts, roles, and
services.

## Running in Docker

```
docker run -e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS -e BUCKET=<GCP_BUCKET_NAME> -e TOKEN=<PDB_ACCESS_TOKEN> -v /tmp:/output:rw --add-host <pdb-host>:<pdb-hostip> infinitory-app
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

Run in Dev:

bin/infinitory -h pdb.ops.puppetlabs.net -t <pdb-access-token> -o /tmp/output -b <gcs-bucket-name>
