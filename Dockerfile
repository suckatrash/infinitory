FROM python:3
ADD generate.py /
RUN pip install --upgrade pip
#RUN pip install --upgrade --extra-index-url https://artifactory.delivery.puppetlabs.net/artifactory/api/pypi/pypi/simple infinitory
RUN pip install git+git://github.com/puppetlabs/infinitory.git@setup_fixup
CMD [ "python", "generate.py", "pe-master-infranext-prod-1.infc-aws.puppet.net" ]
