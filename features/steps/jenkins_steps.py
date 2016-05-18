# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Jenkins configuration for feature tests"""

import collections
import hashlib
import os.path
import shutil

from behave import given

from ..environment import update_jenkins


@given(u'there is a jenkins job with name="{name}"')
def given_there_is_a_jenkins_job_with_name(context, name):
    jobs = getattr(context, 'jenkins_jobs', None)
    if jobs is None:
        jobs = context.jenkins_jobs = []

    jobs.append(name)

    job_url = context.build_jenkins_url('job/' + name)

    update_jenkins(
        context, 'api/python',
        dict(
            jobs=[dict(
                color='blue',
                name=name,
                url=job_url
            )]
        )
    )

    update_jenkins(
        context,
        'job/%s/api/python' % name,
        dict(
            actions=[{}],
            buildable=True,
            builds=[],
            name=name,
            url=job_url,
            lastSuccessfulBuild=None,
            lastUnstableBuild=None,
            lastFailedBuild=None,
            lastCompletedBuild=None,
            lastUnsuccessfulBuild=None,
            lastBuild=None,
            lastStableBuild=None,
        )
    )


@given(u'the job has a build with number="{number}"')
def given_the_job_has_a_build(context, number):
    create_jenkins_artifact(context, number)


@given(u'the job has a build with number="{number}" with malformed data')
def given_the_job_has_a_build_with_malformed_data(context, number):
    create_jenkins_artifact(context, number, True)


def create_jenkins_artifact(context, number, malformed=False):
    job = context.jenkins_jobs[-1]

    builds = getattr(context, 'jenkins_builds', None)
    if builds is None:
        builds = context.jenkins_builds = collections.defaultdict(list)

    builds[job].append(number)

    number = int(number)
    path_fragment = 'job/%s/%s' % (job, number)

    update_jenkins(
        context,
        'job/%s/api/python' % job,
        dict(
            builds=[
                dict(
                    number=number,
                    url=context.build_jenkins_url(path_fragment)
                )
            ]
        )
    )

    artifact_filename = '%s-%s-1.noarch.rpm' % (
        context.tds_applications[-1].name, number
    )

    update_jenkins(
        context,
        path_fragment + '/api/python',
        dict(
            fullDisplayName=("%s #%s" % (job, number)),
            number=number,
            # XXX: need to specify name for file
            artifacts=[dict(
                displayPath=artifact_filename,
                fileName=artifact_filename,
                relativePath=artifact_filename,
            )]
        )
    )

    artifact_fspath = path_fragment + '/artifact/' + artifact_filename

    if malformed:
        data = dict(stuff=True)
    else:
        data = dict(
            name=str(context.tds_applications[-1].name),
            version=number,
            release=1,
            arch=str(context.tds_applications[-1].arch),
        )

    update_jenkins(
        context,
        artifact_fspath,
        data,
    )

    md5 = hashlib.md5()
    with open(
        os.path.join(context.JENKINS_SERVER_DIR, artifact_fspath)
    ) as fh:
        md5.update(fh.read())
    artifact_md5 = md5.hexdigest()

    # Currently not used, but keeping for future possibilities
    # Needed for when fingerprinting is turned on and used
    update_jenkins(
        context,
        'fingerprint/%s/api/python' % artifact_md5,
        dict(
            fileName=artifact_filename,
            hash=artifact_md5,
            original=dict(
                name=job,
                number=number,
            ),
            usage=[
                dict(
                    name=job,
                    ranges=dict(
                        ranges=[dict(end=number+1, start=number)]
                    )
                )
            ],
        )
    )


@given(u"jenkins does not have the job's artifact")
def given_jenkins_does_not_have_the_artifact(context):
    job = context.jenkins_jobs[-1]
    number = context.jenkins_builds[job][-1]

    path_fragment = 'job/%s/%s' % (job, number)

    artifact_dir = os.path.join(
        context.JENKINS_SERVER_DIR, path_fragment, 'artifact'
    )
    shutil.rmtree(artifact_dir)
