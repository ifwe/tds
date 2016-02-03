import com.tagged.build.scm.*
import com.tagged.build.common.*
import com.tagged.build.fpm.FPMPython
import com.tagged.build.fpm.FPMArg
import com.tagged.build.fpm.FPMCommonArgs
import com.tagged.build.fpm.FPMPythonArgs
import com.tagged.build.fpm.FPMPythonScripts

def project = new PythonFPMMatrixProject(
    jobFactory,
    [
        scm: new StashSCM(project: "tds", name: "tds"),
        hipchatRoom: 'Tagged Deployment System',
        email: 'devtools@tagged.com',
        interpreters:['python27'],
    ]
)

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
def pyunit = project.downstreamJob {
    name 'pyunit'
    label 'python27 && centos6'
    steps { shell '.jenkins/scripts/pyunit.sh' }
    publishers {
        archiveJunit "reports/pyunit.xml"
        cobertura('coverage.xml')
    }
}

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

def tds_installer = new FPMPython([
    FPMCommonArgs.verbose,
    new FPMArg('-s', 'dir'),
    FPMCommonArgs.type,
    new FPMArg('-C', './etc/installer'),
    new FPMArg('--prefix','/etc/init.d'),
    new FPMArg('--name', 'tds-installer'),
    new FPMArg('--template-scripts'),
    new FPMArg('--template-value', 'update_init=tds_installer'),
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
    "'Daemon to manage installations for deployment application'"),
    FPMPythonArgs.version,
    FPMPythonArgs.iteration,
    new FPMArg('$FPM_EXTRAS'),
    FPMCommonArgs.current_dir
])

def tds_update_repo = new FPMPython([
    FPMCommonArgs.verbose,
    new FPMArg('-s', 'dir'),
    FPMCommonArgs.type,
    new FPMArg('-C', './etc/update_repo'),
    new FPMArg('--prefix','/etc/init.d'),
    new FPMArg('--name', 'tds-update-yum-repo'),
    new FPMArg('--template-scripts'),
    new FPMArg('--template-value', 'update_init=update_deploy_repo'),
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
    'fpmsteps': [tds_installer, tds_update_repo]
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
    ['Gauntlet', [pylint, pyunit, features]],
    ['Build', [matrixRPMs]],
])

def (tds, branches) = project.branchBuilders(gauntlet.name)

// Override default 30m timeout
jobFactory.referencedJobs.each {
    it.with {
        wrappers {
            timeout(180, false)
        }
    }
}
