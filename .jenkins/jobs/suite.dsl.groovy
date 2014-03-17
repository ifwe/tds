@GrabResolver('https://artifactory.tagged.com/artifactory/libs-release-local/')
@Grab('com.tagged.build:jenkins-dsl-common:0.1.14')

import com.tagged.build.common.*

def project = new PythonFPMMatrixProject(
    jobFactory,
    [
        githubOwner: 'siteops',
        githubProject: 'deploy',
        hipchatRoom: 'Tagged Deployment System',
        email: 'devtools@tagged.com',
        interpreters:['python26', 'python27'],
    ]
)

// Report pylint warnings and go 'unstable' when over the threshold
def pylint = project.downstreamJob {
    name 'pylint'
    label 'python26 && centos6'
    steps { shell '.jenkins/scripts/pylint.sh' }

    publishers {
        warnings([], ['Pyflakes': 'reports/pyflakes.log'])
        violations {
            pylint(258, 259, 258, "reports/pylint.log")
        }
    }
}

// Run python unit tests and record results
def pyunit = project.downstreamJob {
    name 'pyunit'
    label 'python26 && centos6'
    steps { shell '.jenkins/scripts/pyunit.sh' }
    publishers {
        archiveJunit "reports/pyunit.xml"
        cobertura('coverage.xml')
    }
}

def matrixRPMs = project.pythonFPMMatrixJob {
    name 'build'
    logRotator(-1, 50)

    steps {
        shell('''
            #!/bin/bash
            if [ -n "$rvm_path" -a -f $rvm_path/scripts/rvm ]; then
                source $rvm_path/scripts/rvm
                rvm use system
            fi
            export GEM_HOME=/usr/lib/ruby/gems/1.8
            if [ "$os" == "centos54" -a "$interpreter" == "python24" ] ||
               [ "$os" == "centos64" -a "$interpreter" == "python26" ]; then
                FPM_INTERPRETER=python
                FPM_PYPREFIX=python
            else
                FPM_INTERPRETER=`echo "$interpreter" | sed -r 's/2/2\\./g'`
                FPM_PYPREFIX=$interpreter
            fi
            if [ "$os" == "centos54" ]; then
                FPM_CMD_PYTHON=python2.6
            else
                FPM_CMD_PYTHON=python
            fi
            if [ -f version.py ]; then
                FPM_PYPKG_VERSION=`$FPM_CMD_PYTHON -c "import version; v = version.__version__; print v.split('-', 1)[0] if '-' in v else v"`
                FPM_PYPKG_ITERATION=`$FPM_CMD_PYTHON -c "import version, string; v = version.__version__; print '0.' + v.split('-', 1)[1] if '-' in v and v.split('-', 1)[1][0] not in string.digits else '1'"`
                FPM_VERSION="-v $FPM_PYPKG_VERSION"
            else
                FPM_VERSION=""
                FPM_PYPKG_ITERATION="1"
            fi
            if [ "$os" == "centos54" ]; then
                FPM_PYPKG_ITERATION="$FPM_PYPKG_ITERATION.tagged.el5"
            elif [ "$os" == "centos64" ]; then
                FPM_PYPKG_ITERATION="$FPM_PYPKG_ITERATION.tagged.el6"
            fi
            FPM_ITERATION="--iteration $FPM_PYPKG_ITERATION"
            set -x
            /usr/lib/ruby/gems/1.8/bin/fpm --verbose -s dir --rpm-auto-add-directories -C ./etc --prefix /etc/init.d -n tds-update-repo -t rpm --after-install pkg/rpm/after_install.sh --before-remove pkg/rpm/before_remove.sh -d "$FPM_PYPREFIX-tds = $FPM_PYPKG_VERSION-$FPM_PYPKG_ITERATION" --description 'Daemon to update repository for deployment application' $FPM_VERSION $FPM_ITERATION $FPM_EXTRAS .
            '''.stripIndent().trim())

        publishers {
            archiveArtifacts('*.rpm')
        }
    }
}

def gauntlet = project.gauntlet([
    ['Gauntlet', [pylint, pyunit]],
    ['Build', [matrixRPMs]],
])

def (tds, branches) = project.branchBuilders(gauntlet.name)
