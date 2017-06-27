#!/usr/bin/env python

# (C) Copyright 2017 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import print_function

import os
import socket
import sys
import time

from kubernetes import KubernetesAPIClient


NAMESPACE = '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
TIMEOUT = float(os.environ.get('WAIT_TIMEOUT', '10'))
RETRIES = int(os.environ.get('WAIT_RETRIES', '24'))
RETRY_DELAY = float(os.environ.get('WAIT_DELAY', '5.0'))

USE_KUBE_CONFIG = os.environ.get('USE_KUBE_CONFIG', False)

pod_is_self = True


def get_current_namespace():
    if 'NAMESPACE' in os.environ:
        return os.environ['NAMESPACE']

    with open(NAMESPACE, 'r') as f:
        return f.read()


def get_current_pod():
    if 'POD_NAME' in os.environ:
        return os.environ['POD_NAME']

    return socket.gethostname()


def is_condition_complete(condition):
    return condition.type == 'Complete' and str(condition.status) == 'True'


def check_success(client, namespace, job, retries):
    print('Checking job %s' % job.metadata.name)
    if 'conditions' not in job.status:
        print('Job has no conditions (probably still running), '
              'will wait for it to finish: %s/%s (%d attempts '
              'remaining)' % (namespace, job.metadata.name, retries))
        return False, retries - 1

    complete = filter(is_condition_complete, job.status.conditions)
    if not complete:
        print('Job is not complete, will wait for it to finish: %s/%s (%d '
              'attempts remaining)' % (namespace, job.metadata.name, retries))
        return False, retries - 1
    if job.status.succeeded:
    	return True, retries
    else:
        print('Job %s failed' % job.metadata.name)
	return False, 0


def main():
    client = KubernetesAPIClient()
    if USE_KUBE_CONFIG:
        client.load_kube_config()
    else:
        client.load_cluster_config()

    namespace = get_current_namespace()
    pod_name = get_current_pod()

    pod = client.get('/api/v1/namespaces/{}/pods/{}', namespace, pod_name)

    app = pod.metadata.labels['app']

    selector = 'app={}'.format(app)

    jobs = client.get('/apis/batch/v1/namespaces/{}/jobs', namespace,
                      params={'labelSelector': selector})

    items = [(item, RETRIES) for item in jobs['items']]
    if not items:
        print('No jobs!')
        sys.exit(0)

    failed = []
    while items:
        print('Checking %d jobs...' % len(items))
        remaining = []
        for job, retries in items:
            success, retries = check_success(client, namespace, job, retries)
            if success:
               print('Job %s succeeded' % job.metadata.name)
            else:
                if retries is 0:
                    failed.append(job)
                else:
                    remaining.append((job, retries))

        if remaining:
            print('Still waiting on some jobs to finish...')
            time.sleep(RETRY_DELAY)

        items = []
        for job, retries in remaining:
            refreshed_job = client.get('/apis/batch/v1/namespaces/{}/jobs/{}',
                                       namespace, job.metadata.name)
            items.append((refreshed_job, retries))

    if failed:
        print('Failed jobs:')
        for job in failed:
            job.pprint()
            sys.exit(1)
    else:
        print('All jobs completed successfully.')


if __name__ == '__main__':
    main()
