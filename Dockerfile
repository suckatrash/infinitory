FROM python:3
ADD generate.py /
ENV TOKEN $TOKEN
ENV BUCKET $BUCKET
ENV GOOGLE_APPLICATION_CREDENTIALS $GOOGLE_APPLICATION_CREDENTIALS
RUN pip install --upgrade pip
RUN pip install --no-cache-dir git+git://github.com/suckatrash/infinitory.git@puppetdb_remote_queries
ENTRYPOINT python generate.py pe-infranext-prod.infc-aws.puppet.net ${TOKEN} ${BUCKET}
