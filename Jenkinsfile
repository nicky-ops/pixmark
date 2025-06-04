pipeline {
  agent any
  environment {
    IMAGE_NAME = "nickyops/pixmark:latest"
  }
  stages {
    stage('Deploy') {
      steps {
        withCredentials([file(credentialsId: 'pixmark-env-file', variable: 'ENV_FILE')]) {
          sh '''
            docker pull $IMAGE_NAME
            cp $ENV_FILE .env
            docker compose -f compose.prod.yml up -d
          '''
        }
      }
    }
  }
}
