// Copyright 2016 Ifwe Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import com.tagged.build.scm.*
import com.tagged.build.common.*

def project = new Project(
    jobFactory,
    [
        scm: new StashSCM(project: "tds", name: "tds", defaultRef: "origin/master"),
        notifyEmail: 'siteops@tagged.com',
    ]
)

// TODO: convert these test jobs to docker and centos 7.

// Report pylint warnings and go 'unstable' when over the threshold
def pylint = project.downstreamJob {
    name 'pylint'
    label 'python27 && centos6'
    steps { shell '.jenkins/scripts/pylint.sh' }

    publishers {
        warnings([], ['Pyflakes': 'reports/pyflakes.log'])
        violations {
            pylint(187, 188, 187, "reports/pylint.log")
        }
    }
}

// Run python unit tests and record results
//def pyunit = project.downstreamJob {
//    name 'pyunit'
//    label 'python27 && centos6'
//    steps { shell '.jenkins/scripts/pyunit.sh' }
//    publishers {
//        archiveJunit "reports/pyunit.xml"
//        cobertura('coverage.xml')
//    }
//}

// Run behave tests and record results
def features = project.downstreamJob {
    name 'features'
    label 'python27 && centos6'
    steps { shell '.jenkins/scripts/features.sh' }
    publishers {
        archiveJunit "reports/*.xml"
        cobertura 'coverage.xml'
    }
}

daemon_common_build = '''\
docker_build/run.sh -s dir --depends-same-version python-tds \\
    --version-py --iteration "$PARENT_BUILD_NUMBER" \\
    -- \\
    -a noarch --template-scripts \\
    --after-install pkg/rpm/after_install.sh.erb \\
    --before-remove pkg/rpm/before_remove.sh.erb \\
    --after-remove pkg/rpm/after_remove.sh.erb \\
    --no-rpm-auto-add-directories \\
    --prefix /lib/systemd/system \\
'''

def tds_installer = project.downstreamJob {
    name 'tds_installer'
    label 'docker'

    configure { j ->
        resetScmTriggers(j)
    }

    steps {
        shell daemon_common_build + '''\
            -C systemd/tds_installer \\
            --template-value unit=tds_installer.service \\
            --name tds-installer \\
            --description 'Daemon to manage installations for deployment application'
        '''
        publishers {
            archiveArtifacts('docker_build/pkgs/*.rpm')
        }
    }
}

def tds_update_repo = project.downstreamJob {
    name 'tds_update_repo'
    label 'docker'

    configure { j ->
        resetScmTriggers(j)
    }

    steps {
        shell daemon_common_build + '''\
            -C systemd/update_deploy_repo \\
            --template-value unit=update_deploy_repo.service \\
            --name tds-update-yum-repo \\
            --description 'Daemon to update repository for deployment application'
        '''
        publishers {
            archiveArtifacts('docker_build/pkgs/*.rpm')
        }
    }
}


def python_tds = project.downstreamJob {
    name 'python_tds'
    label 'docker'

    configure { j ->
        resetScmTriggers(j)
    }

    steps {
        shell 'docker_build/run.sh -- --iteration "$PARENT_BUILD_NUMBER"'
        publishers {
            archiveArtifacts('docker_build/pkgs/*.rpm')
        }
    }
}

def gauntlet = project.gauntlet([
//    ['Gauntlet', [pylint, pyunit, features]],
//    ['Gauntlet', [pylint, features]],
    ['Build', [tds_installer, tds_update_repo, python_tds]],
])

// Override default 30m timeout
jobFactory.referencedJobs.each {
    it.with() {
        triggers {
            scm('')
        }
        wrappers {
            timeout(240, false)
        }
    }
}
