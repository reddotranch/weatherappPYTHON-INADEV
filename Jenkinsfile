def COLOR_MAP = [
    'SUCCESS': 'good', 
    'FAILURE': 'danger',
]

pipeline {
    agent { node { label "MAVEN-SONAR" } }   
    parameters {
      choice(name: 'aws_account', choices: ['374965156099', '654654193818', '922266408974','576900672829'], description: 'aws account hosting image registry')
      choice(name: 'Environment', choices: ['Dev', 'QA', 'UAT', 'Prod'], description: 'Target environment for deployment')
      choice(name: 'Cluster', choices: ['betech-cluster', 'dev-cluster','uat-cluster'], description: 'Kubeconfig file update for the EKS cluster')
      string(name: 'ecr_tag', defaultValue: '1.5.2', description: 'Assign the ECR tag version for the build')
    }
/*
    tools {
      maven "Maven-3.9.8"
    }
*/
    stages {
    stage('1. Git Checkout') {
      steps {
        git branch: 'master', credentialsId: 'betech-pipeline', url: 'https://github.com/reddotranch/weatherappPYTHON-INADEV.git'
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
                      -Dsonar.host.url=https://sonarqube1.betechsol.com \
                      -Dsonar.token=${SONAR_TOKEN} \
                      -Dsonar.sources=.\
                     """
                  }
              }
        }

    stage('3. Docker Image Build') {
      steps {
          sh "aws ecr get-login-password --region us-west-2 | sudo docker login --username AWS --password-stdin ${aws_account}.dkr.ecr.us-west-2.amazonaws.com"
          sh "sudo docker build -t weatherapp ."
          sh "sudo docker tag weatherapp:latest ${aws_account}.dkr.ecr.us-west-2.amazonaws.com/weatherapp:${params.ecr_tag}"
          sh """sudo docker push ${aws_account}.dkr.ecr.us-west-2.amazonaws.com/weatherapp:${params.ecr_tag}"""
      }
    }

    stage('3.1. Docker Image Scan') {
      steps {
          sh "aws ecr start-image-scan --repository-name weatherapp --image-id imageTag=${params.ecr_tag} --region us-west-2"
          sh "aws ecr describe-image-scan-findings --repository-name weatherapp --image-id imageTag=${params.ecr_tag} --region us-west-2"
      }
    }

    stage('4. Update Kubeconfig') {
      steps {
        sh "aws eks --region us-west-2 update-kubeconfig --name ${params.Cluster} && export KUBE_CONFIG_PATH=~/.kube/config"
      }
    }

    stage('4.1. Application Deployment in EKS') {
      steps {
          sh '/home/ubuntu/bin/kubectl apply -f manifest'
      }
    }

    stage('5. Monitoring Solution Deployment in EKS') {
      steps {
          sh '/home/ubuntu/bin/kubectl apply -k monitoring'
          sh("""script/install_helm.sh""") 
          sh("""script/install_prometheus.sh""") 
      }
    }

    stage('6. Email Notification') {
      steps {
        echo 'Success'
        mail bcc: 'betechincorporated@gmail.com', body: '''Build is Over. Check the application using the URL below:
        https://weatherapp.betechsol.com/
        Let me know if the changes look okay.
        Thanks,
        TDW System Technologies,
        +1 (123) 123-4567''', 
        subject: 'Application was Successfully Deployed!!', to: 'tdwaws2024@gmail.com'
      }
    }
  }
    post {
         always {
            echo 'Slack Notifications.'
            slackSend channel: '#all-weatherapp-cicd',
                color: COLOR_MAP[currentBuild.currentResult],
                message: "*${currentBuild.currentResult}:* Job ${env.JOB_NAME} build ${env.BUILD_NUMBER} \n More info at: ${env.BUILD_URL}"
        }
    }
  
}
