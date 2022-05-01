# CHANGELOG

* 0.1.2 (2022-04-30)

Added a PerEnvironment object to allow variable resolution per environment.

* 0.1.1 (2022-04-27)

The tfvars now resolve LookupOutput objects recursively, not just in level 1.

* 0.1.0 (2022-04-03)

Add a `--environment` parameter which defaults to prod.

* 0.0.8 (2022-03-26)

`terraform output` now only prints the JSON. This makes the output subcommand
more chainable.

* 0.0.7 (2022-02-04)

Fix a regression in 0.0.6 that broke saving output

* 0.0.6 (2022-02-04)

Significant refactoring
Fix how destroy works to make it actually work. :)

* 0.0.5 (2022-01-16)

Improve code by adding a test suite

* 0.0.4 (2022-01-11)

Fix breaking bug in saving outputs when running apply

* 0.0.3 (2022-01-10)

Stream the plan/apply/destroy output

* 0.0.2 (2022-01-08)

Remove hardcoding of a Gammaforce repository and properly pass default values

* 0.0.1 (2022-01-03)

Initial version
