FROM python:3
ADD generate.py /
ENV TOKEN $TOKEN
ENV BUCKET $BUCKET
ENV GOOGLE_APPLICATION_CREDENTIALS $GOOGLE_APPLICATION_CREDENTIALS
RUN pip install --upgrade pip
RUN pip install -i https://artifactory.delivery.puppetlabs.net/artifactory/api/pypi/pypi/simple -v infinitory==0.1.6 
ENTRYPOINT python generate.py ${PDB_HOST} ${TOKEN} ${BUCKET}
