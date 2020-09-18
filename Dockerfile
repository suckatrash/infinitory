FROM python:3
ADD generate.py /
ENV TOKEN $TOKEN
ENV BUCKET $BUCKET
ENV PDB_HOST $PDB_HOST
ENV GOOGLE_APPLICATION_CREDENTIALS $GOOGLE_APPLICATION_CREDENTIALS
RUN pip install --upgrade pip
RUN pip install --no-cache-dir git+git://github.com/puppetlabs/infinitory.git@master
ENTRYPOINT python generate.py ${PDB_HOST} ${TOKEN} ${BUCKET}
