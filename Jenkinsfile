node('docker') {

    stage('Delegate to build job') {
        build job: '../openbach-extra-ci', parameters: [string(name: 'BRANCH_NAME', value: env.BRANCH_NAME)], propagate: true, wait: true
    }

}
