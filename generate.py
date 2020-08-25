#!/usr/bin/env python3

import sys
import subprocess

if len(sys.argv) == 1:
    puppetdb = 'localhost'
elif len(sys.argv) == 2:
    puppetdb = sys.argv[1]
else:
    sys.exit("Expected 1 or 0 arguments. Got {}.".format(len(sys.argv) - 1))

# Generate the report
subprocess.check_call(
    ["infinitory", "--host", "{}".format(puppetdb),
        "--output", "/srv/infinitory/output"],
    timeout=120)
