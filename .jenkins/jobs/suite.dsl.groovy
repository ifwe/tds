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
            pylint(207, 208, 207, "reports/pylint.log")
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

def tds_update_repo = new FPMPython([
    FPMCommonArgs.verbose,
    new FPMArg('-s', 'dir'),
    FPMCommonArgs.type,
    FPMCommonArgs.autodirs,
    new FPMArg('-C', './etc'),
    new FPMArg('--prefix','/etc/init.d'),
    new FPMArg('--name', 'tds-update-repo'),
    new FPMArg('--after-install', 'pkg/rpm/after_install.sh'),
    new FPMArg('--before-remove', 'pkg/rpm/before_remove.sh'),
    new FPMArg('--depends',
    '"$FPM_PYPREFIX_PREFIX$FPM_PYPREFIX-tds = $FPM_PYPKG_VERSION-$FPM_ITERATION"',
    [
        FPMPythonScripts.fpm_interpreter,
        FPMPythonScripts.fpm_version_iteration,
        FPMPythonScripts.fpm_python_tagged_iteration,
    ]),
    new FPMArg('--description',
    "'Daemon to update repository for deployment application'"),
    FPMPythonArgs.version,
    FPMPythonArgs.iteration,
    new FPMArg('$FPM_EXTRAS'),
    FPMCommonArgs.current_dir
])

def matrixRPMs = project.pythonFPMMatrixJob([
    'fpmsteps': [tds_update_repo]
]) {
    name 'build'
    logRotator(-1, 50)

    steps {
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
