pipeline {
  agent any
  environment {
    IMAGE_NAME = "nickyops/pixmark:latest"
  }
  stages {
    stage('Deploy') {
      steps {
        sh '''
          docker pull $IMAGE_NAME
          docker compose -f compose.prod.yml up -d
        '''
      }
    }
  }
}