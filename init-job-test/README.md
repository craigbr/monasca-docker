init-job-test Dockerfile
=====================

This image checks that the init jobs have succeeded for a running instance of Monasca
that is deployed using monasca-helm. It queries the Kubernetes API to determine
the jobs have completed and succeeded. It is not useful in docker-compose and will
not work.

Sources: [monasca-helm][1]

Tags
----

Images in this repository are tagged as follows:

 * `latest`: refers to the latest stable point release, e.g. `1.0.0`
 * `1.0.0`, `1.0`, `1`: standard semver tags

Usage
-----

This image requires a running instance of Monasca that is deployed via monasca-helm.

monasca-helm adds additional templating that allows it to be run using helm test.

[1]: https://github.com/hpcloud-mon/monasca-helm
