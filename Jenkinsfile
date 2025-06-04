pipeline {
  agent any
  environment {
    IMAGE_NAME = "nickyops/pixmark:latest"
  }
  stages {
    stage('Deploy') {
      steps {
        withCredentials([file(credentialsId: 'pixmark-env-file', variable: 'DOTENV')]) {
          sh '''
            docker pull $IMAGE_NAME
            ls -la && whoami && pwd
            cp $DOTENV .env
            docker compose -f compose.prod.yml up -d
          '''
        }
      }
    }
  }
}
