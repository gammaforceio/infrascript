# infrascript

The infra scripting product

# Prerequisites

* You must have installed Docker.
    * Ensure that your Docker engine has DNS setup. If necessary, you may need to add `--dns 8.8.8.8` to your Docker command so that Terraform can reach the internet.
* You must have structured your repository as described below.

# Repository structure

```
/
    infra/
        definitions.py
        subdir1/
            file1.tf
            file2.tf
        subdir2/
            file1.tf
            file2.tf
```

## definitions.py

This is the file which controls how `infra` knows what to do.

```
from lookup_output import LookupOutput

GLOBALS = {
    'region': <region>,
    'backend': {
        'bucket_name': <Terraform S3 bucket>,
        'dynamodb_table': <Terraform Locking table>,
    },
}

SECTIONS = {
    <section_name>: {
        'subdir': <dirname, defaults to section_name>,
        'inputs': {
            <varname>: str | LookupOutput,
        },
    },
}
```

# Standard invocation

This command is packaged as a Docker image. To function properly, it requires
that you invoke it with the necessary parameters. The reasons for each will
be explained below.

```
docker run --rm \
    --user "$(id -u):$(id -g)" \
    --volume "$(pwd):/terraform" \
    --workdir "/terraform" \
    --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    --env AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
        gammaforce\infra:latest

```

* `--user "$(id -u):$(id -g)"`

Part of Terraform's processing is to write several files into the mounted
volume. By providing the invoking user's and group's ID, these files will be
written with that ID and not root. Since the Docker subsystem normally runs
as root, this can result with files owned by root on the host system.

* `--volume "$(pwd):/terraform" --workdir "/terraform"`

Specifically, pwd should be the `infra/` directory.

* `--env ...`

You need to provide the AWS credentials so that Terraform can do what it
needs to do.

## SCM organization and SCM repository

The infra script namespaces all the Terraform state files and outputs with the
SCM organization and repository. You must provide these values as environment
variables.

The `invoke` script within this repository does everything necessary.

# Limitations

## \*nix only

This has only been tested on \*nix-like systems, like Linux and OSX. This has
**not** been tested in any ways on Windows.

## AWS only

This _should_ work in Azure and GCP, but has not been tested outside of AWS.
It only uses Terraform commands, and so should function properly.
