ARG TF_VERSION=1.1.1
FROM hashicorp/terraform:${TF_VERSION}

RUN apk add --no-cache --update python3 py3-pip

RUN pip3 install boto3

COPY scripts /scripts

ENTRYPOINT ["/scripts/infra.py"]

CMD ["--help"]
