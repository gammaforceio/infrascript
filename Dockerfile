ARG TF_VERSION=1.1.1
FROM hashicorp/terraform:${TF_VERSION}

RUN apk add --no-cache --update python3 py3-pip

RUN pip3 install boto3

COPY src /opt/gammaforce/infrascript
COPY scripts/infrascript.py /opt/gammaforce/infra.py

ENTRYPOINT ["/usr/bin/python3", "/opt/gammaforce/infra.py"]

CMD ["--help"]
