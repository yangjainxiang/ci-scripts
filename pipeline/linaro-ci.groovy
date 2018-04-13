def clone2local(giturl, branchname, localdir) {
    def exists = fileExists localdir
    if (!exists){
        new File(localdir).mkdir()
    }
    dir (localdir) {
        checkout([$class: 'GitSCM', branches: [[name: branchname]],
                extensions: [[$class: 'CloneOption', timeout: 120]], gitTool: 'Default',
                userRemoteConfigs: [[url: giturl]]
            ])
    }
}

def getGitBranchName() {
    return scm.branches[0].name
}

def getGitUrl() {
    return scm.getUserRemoteConfigs()[0].getUrl()
}

node ('compile'){
    stage('Preparation') { // for display purposes
        echo " ### the git url : " + getGitUrl()

        clone2local(getGitUrl(), getGitBranchName(), './local/ci-scripts')

        dir('./local/ci-test-cases') {
            deleteDir()
        }
        if (TEST_REPO == "" || TEST_REPO == null) {
            TEST_REPO = "https://github.com/qinshulei/ci-test-cases.git"
        }
        clone2local(TEST_REPO, '*/master', './local/ci-test-cases')


        // prepare variables.
        sh 'env'

        GIT_DESCRIBE = VERSION

        // save the properties
        //sh "echo SKIP_BUILD=true > env.properties"
        sh 'echo "" > env.properties'

        // save jenkins enviroment properties.
        sh "echo BUILD_URL=\\\"${BUILD_URL}\\\" >> env.properties"

        // save jenkins parameters.
        if (env.TREE_NAME) {
            sh "echo TREE_NAME=\\\"${TREE_NAME}\\\" >> env.properties"
        }
        if (env.BOOT_PLAN) {
            sh "echo BOOT_PLAN=\\\"${BOOT_PLAN}\\\" >> env.properties"
        }

        if (env.SHELL_PLATFORM) {
            sh "echo SHELL_PLATFORM=\\\"${SHELL_PLATFORM}\\\" >> env.properties"
        }
        if (env.SHELL_DISTRO) {
            sh "echo SHELL_DISTRO=\\\"${SHELL_DISTRO}\\\" >> env.properties"
        }

        if (env.TEST_REPO) {
            sh "echo TEST_REPO=\\\"${TEST_REPO}\\\" >> env.properties"
        }
        if (env.TEST_PLAN) {
            sh "echo TEST_PLAN=\\\"${TEST_PLAN}\\\" >> env.properties"
        }
        if (env.TEST_SCOPE) {
            sh "echo TEST_SCOPE=\\\"${TEST_SCOPE}\\\" >> env.properties"
        }
        if (env.TEST_LEVEL) {
            sh "echo TEST_LEVEL=\\\"${TEST_LEVEL}\\\" >> env.properties"
        }

        if (env.GIT_DESCRIBE) {
            sh "echo GIT_DESCRIBE=\\\"${GIT_DESCRIBE}\\\" >> env.properties"
        }

        if (env.DEBUG) {
            sh "echo DEBUG=\\\"${DEBUG}\\\" >> env.properties"
        }
    }

    stage ('mirror') {
        build job: 'step_mirror_test_repo_in_lava', parameters: [[$class: 'StringParameterValue', name: 'TEST_REPO', value: TEST_REPO]]
    }

    // load functions
    def functions = load "./local/ci-scripts/pipeline/functions.groovy"

    def test_result = 0
    stage('Test') {
        test_result = sh script: "./local/ci-scripts/test-scripts/jenkins_boot_start.sh -p env.properties 2>&1", returnStatus: true
    }
    if (test_result == 0) {
        echo "Test success"
    } else {
        echo "Test failed"
        functions.send_mail()
        currentBuild.result = 'FAILURE'
        return
    }


    stage('Result') {
        functions.send_mail()
    }
}
