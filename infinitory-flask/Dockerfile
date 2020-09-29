FROM python:3
ADD app.py /
ENV GOOGLE_APPLICATION_CREDENTIALS $GOOGLE_APPLICATION_CREDENTIALS
ENV TZ=America/Los_Angeles
ENV BUCKET $BUCKET
RUN pip install --upgrade pip
RUN pip install flask google-cloud-storage
EXPOSE 5000
ENTRYPOINT python app.py ${BUCKET}
