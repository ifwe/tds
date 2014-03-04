@GrabResolver('https://artifactory.tagged.com/artifactory/libs-release-local/')
@Grab('com.tagged.build:jenkins-dsl-common:0.1.11')

import com.tagged.build.common.*

def project = new Project(
    jobFactory,
    [
        githubOwner: 'siteops',
        githubProject: 'deploy',
        hipchatRoom: 'Tagged Deployment System',
        email: 'devtools@tagged.com',
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
            pylint(254, 255, 254, "reports/pylint.log")
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

def gauntlet = project.gauntlet([
    ['Gauntlet', [pylint, pyunit]],
])

def (tds, branches) = project.branchBuilders(gauntlet.name)
