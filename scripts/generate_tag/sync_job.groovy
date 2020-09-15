import groovy.json.*

pipeline {
  agent {
    docker {
      image 'release-product-env'
    }
  }
  stages {
    stage("sync status") {
        steps {
                sh 'python --version'
                sh 'git config --global url."https://${TEMP_GITHUB_TOKEN}:x-oauth-basic@api.github.com/".insteadOf "https://api.github.com/"'
                sh 'sed "s/TOKEN_IN_JENKINS/${TEMP_GITHUB_TOKEN}/g" ./scripts/generate_tag/scripts/release_config.json > ./scripts/generate_tag/scripts/release_config_use.json '
                sh 'sed "s/MARS_TOKEN/${MARS_TOKEN}/g" ./scripts/generate_tag/scripts/mars.yaml > ./scripts/generate_tag/scripts/mars_use.yaml '
                sh "cp ./mars /bin/mars"
                sh 'python ./scripts/generate_tag/scripts/sync_stable_status.py'
        }
    }
  }
}
