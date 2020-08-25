#!/usr/bin/env python3

import sys
import subprocess

puppetdb = sys.argv[1]
token = sys.argv[2]
bucket = sys.argv[3]

# Generate the report
subprocess.check_call(
    ["infinitory", "--host", puppetdb, "--token", token, "--bucket", bucket,
        "--output", "/output/infinitory"],
    timeout=300)
