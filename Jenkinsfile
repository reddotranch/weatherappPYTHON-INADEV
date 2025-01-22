pipeline {
    agent { node { label "MAVEN-SONAR" } }   
    parameters {
      choice(name: 'aws_account',choices: ['654654193818', '4568366404742', '922266408974','576900672829'], description: 'aws account hosting image registry')
      choice(name: 'Environment', choices: ['Dev', 'QA', 'UAT', 'Prod'], description: 'Target environment for deployment')
      string(name: 'ecr_tag', defaultValue: '1.0.0', description: 'Assign the ECR tag version for the build')
    }
/*
    tools {
      maven "Maven-3.9.8"
    }
*/
    stages {
    stage('1. Git Checkout') {
      steps {
        git branch: 'master', credentialsId: 'jenkins2025weather', url: 'https://github.com/mbwork1/weatherappPYTHON-INADEV.git'
      }
    }

    stage('2. SonarQube Analysis') {
          environment {
                scannerHome = tool 'SonarQube-Scanner-6.2.1'
            }
            steps {
              withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
                      sh """
                      ${scannerHome}/bin/sonar-scanner  \
                      -Dsonar.projectKey=weather-app \
                      -Dsonar.projectName='weather-app' \
                      -Dsonar.host.url=https://sonarqube1.kubeigu.plainandplane.com \
                      -Dsonar.token=${SONAR_TOKEN} \
                      -Dsonar.sources=.\
                     """
                  }
              }
        }

    stage('3. Docker Image Build') {
      steps {
          sh "aws ecr get-login-password --region us-east-2 | sudo docker login --username AWS --password-stdin ${aws_account}.dkr.ecr.us-east-2.amazonaws.com"
          sh "sudo docker build -t weatherapp ."
          sh "sudo docker tag weatherapp:latest ${aws_account}.dkr.ecr.us-east-2.amazonaws.com/weatherapp:${params.ecr_tag}"
          sh "sudo docker push ${aws_account}.dkr.ecr.us-east-2.amazonaws.com/weatherapp:${params.ecr_tag}"
      }
    }

    stage('4. Application Deployment in EKS') {
      steps {
        kubeconfig(caCertificate: '', credentialsId: 'kubeconfig', serverUrl: '') {
          sh "kubectl apply -f manifest"
        }
      }
    }

    stage('5. Monitoring Solution Deployment in EKS') {
      steps {
        kubeconfig(caCertificate: '', credentialsId: 'kubeconfig', serverUrl: '') {
          sh "kubectl apply -k monitoring"
          sh("""script/install_helm.sh""") 
          sh("""script/install_prometheus.sh""") 
        }
      }
    }

    stage('6. Email Notification') {
      steps {
        echo 'Success'
        mail bcc: 'gofullblastonline@gmail.com', body: '''Build is Over. Check the application using the URL below:
        https://app.kubeigu.plainandplane.com/
        Let me know if the changes look okay.
        Thanks,
        TDW System Technologies,
        +1 (123) 123-4567''', 
        subject: 'Application was Successfully Deployed!!', to: 'gofullblastonline@gmail.com'
      }
    }
  }
}
