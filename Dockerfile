ARG TF_VERSION=1.6.4
FROM hashicorp/terraform:${TF_VERSION}

RUN apk add --no-cache --update python3 py3-pip

COPY requirements.txt /opt/gammaforce/requirements.txt
RUN pip3 install -r /opt/gammaforce/requirements.txt

COPY src /opt/gammaforce/infrascript
COPY scripts/infrascript.py /opt/gammaforce/infra.py
COPY resources /opt/gammaforce/resources
RUN chmod -R 777 /opt/gammaforce/resources

ENTRYPOINT ["/usr/bin/python3", "/opt/gammaforce/infra.py"]

CMD ["--help"]
