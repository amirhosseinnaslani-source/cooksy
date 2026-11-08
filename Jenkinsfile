pipeline {
    agent none
    options {
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
        skipDefaultCheckout(true)
    }
    stages {
        stage('Validate') {
            agent { label 'docker && wbg-001' }
            steps {
                checkout scm
                sh 'docker compose -f compose.yml config --quiet'
                sh 'docker build -t cooksy:ci .'
                sh 'docker image inspect cooksy:ci >/dev/null'
            }
        }
        stage('Deploy') {
            when { branch 'production' }
            agent { label 'deploy && production && wbg-001' }
            steps {
                checkout scm
                sh 'bash scripts/deploy.sh'
            }
        }
    }
}
