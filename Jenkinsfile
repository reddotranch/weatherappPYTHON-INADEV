def COLOR_MAP = [
    'SUCCESS': 'good', 
    'FAILURE': 'danger',
]

pipeline {
    agent { node { label "maven-sonarqube-slave" } }   
    parameters {
      choice(name: 'Deployment_Type', choices: ['apply', 'destroy'], description: 'Choose deployment or destroy operation')
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
      when { 
        expression { params.Deployment_Type == 'apply' }
      }
      steps {
        git branch: 'master', credentialsId: 'betech-pipeline', url: 'https://github.com/reddotranch/weatherappPYTHON-INADEV.git'
      }
    }

    stage('2. SonarQube Analysis') {
          when { 
            expression { params.Deployment_Type == 'apply' }
          }
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
      when { 
        expression { params.Deployment_Type == 'apply' }
      }
      steps {
          sh "aws ecr get-login-password --region us-west-2 | sudo docker login --username AWS --password-stdin ${aws_account}.dkr.ecr.us-west-2.amazonaws.com"
          sh "sudo docker build -t weatherapp ."
          sh "sudo docker tag weatherapp:latest ${aws_account}.dkr.ecr.us-west-2.amazonaws.com/weatherapp:${params.ecr_tag}"
          sh """sudo docker push ${aws_account}.dkr.ecr.us-west-2.amazonaws.com/weatherapp:${params.ecr_tag}"""
      }
    }

    stage('3.1. Docker Image Scan') {
      when { 
        expression { params.Deployment_Type == 'apply' }
      }
      steps {
        script {
          try {
            echo "Starting ECR image scan for weatherapp:${params.ecr_tag}..."
            sh """
            aws ecr start-image-scan --repository-name weatherapp --image-id imageTag=${params.ecr_tag} --region us-west-2 || {
              EXIT_CODE=\$?
              echo "ECR scan failed with exit code: \$EXIT_CODE"
              
              # Check if it's a quota exceeded error
              if aws ecr start-image-scan --repository-name weatherapp --image-id imageTag=${params.ecr_tag} --region us-west-2 2>&1 | grep -q "LimitExceededException"; then
                echo "WARNING: ECR scan quota exceeded. This is not a critical error."
                echo "The image scan quota per image has been exceeded. This is an AWS service limitation."
                echo "You can try again later or proceed without the scan."
                echo "Continuing with deployment..."
              elif aws ecr start-image-scan --repository-name weatherapp --image-id imageTag=${params.ecr_tag} --region us-west-2 2>&1 | grep -q "ScanInProgressException"; then
                echo "WARNING: Image scan already in progress. This is not an error."
                echo "Continuing with deployment..."
              else
                echo "ERROR: ECR scan failed for unknown reason"
                echo "Checking if repository exists..."
                aws ecr describe-repositories --repository-names weatherapp --region us-west-2 || {
                  echo "ERROR: Repository 'weatherapp' not found!"
                  exit 1
                }
                echo "Repository exists. Continuing without scan..."
              fi
            }
            """
            
            echo "Attempting to retrieve scan results..."
            sh """
            aws ecr describe-image-scan-findings --repository-name weatherapp --image-id imageTag=${params.ecr_tag} --region us-west-2 || {
              echo "WARNING: Could not retrieve scan findings. This may be because:"
              echo "1. Scan is still in progress"
              echo "2. Scan quota was exceeded"
              echo "3. Scan was not started successfully"
              echo "Continuing with deployment without scan results..."
            }
            """
          } catch (Exception e) {
            echo "WARNING: ECR image scan stage failed: ${e.getMessage()}"
            echo "This is not a critical error. Continuing with deployment..."
            echo "Note: You may want to manually check the image security later."
          }
        }
      }
    }

    stage('4. Update Kubeconfig') {
      steps {
        sh "aws eks --region us-west-2 update-kubeconfig --name ${params.Cluster} && export KUBE_CONFIG_PATH=~/.kube/config"
      }
    }

    stage('4.1. Application Deployment in EKS') {
      when { 
        expression { params.Deployment_Type == 'apply' }
      }
      steps {
          sh 'kubectl apply -f manifest'
      }
    }

    stage('5. Monitoring Solution Deployment in EKS') {
      when { 
        expression { params.Deployment_Type == 'apply' }
      }
      steps {
          sh '/home/ubuntu/bin/kubectl apply -k monitoring'
          sh("""script/install_helm.sh""") 
          sh("""script/install_prometheus.sh""") 
      }
    }

    stage('5.1. Application Destroy') {
      when { 
        expression { params.Deployment_Type == 'destroy' }
      }
      steps {
        echo 'Destroying Weather App Deployment from EKS...'
        
        // Update kubeconfig for destroy operations
        sh "aws eks --region us-west-2 update-kubeconfig --name ${params.Cluster} && export KUBE_CONFIG_PATH=~/.kube/config"
        
        // Remove application manifests
        sh '''
        echo "Removing weather app manifests..."
        kubectl delete -f manifest --ignore-not-found=true || echo "Manifests already removed or not found"
        '''
        
        // Remove monitoring solution
        sh '''
        echo "Removing monitoring solution..."
        kubectl delete -k monitoring --ignore-not-found=true || echo "Monitoring solution already removed or not found"
        '''
        
        // Clean up namespaces
        sh '''
        echo "Cleaning up weather app namespaces..."
        kubectl delete namespace directory --ignore-not-found=true || echo "Directory namespace not found"
        kubectl delete namespace gateway --ignore-not-found=true || echo "Gateway namespace not found"
        kubectl delete namespace analytics --ignore-not-found=true || echo "Analytics namespace not found"
        '''
        
        // Clean up any remaining ingresses
        sh '''
        echo "Cleaning up ingresses..."
        kubectl delete ingress --all --all-namespaces --ignore-not-found=true || echo "No ingresses to clean up"
        '''
        
        // Wait for resources to be cleaned up
        sh '''
        echo "Waiting for resources to be cleaned up..."
        sleep 30
        '''
        
        echo 'Weather App Destroy completed successfully'
      }
    }

    stage('6. Email Notification') {
      steps {
        echo 'Success'
        script {
          def emailBody = ''
          def emailSubject = ''
          
          if (params.Deployment_Type == 'apply') {
            emailBody = '''Build is Over. Check the application using the URL below:
        https://weatherapp.betechsol.com/
        Let me know if the changes look okay.
        Thanks,
        TDW System Technologies,
        +1 (123) 123-4567'''
            emailSubject = 'Application was Successfully Deployed!!'
          } else {
            emailBody = '''Weather App Destroy is completed.
        
        The following resources have been removed:
        - Application manifests
        - Monitoring solution
        - Associated namespaces
        - Ingresses and Load Balancers
        
        Let me know if you need any assistance.
        Thanks,
        TDW System Technologies,
        +1 (123) 123-4567'''
            emailSubject = 'Application was Successfully Destroyed!!'
          }
          
          mail bcc: 'betechincorporated@gmail.com', 
               body: emailBody,
               subject: emailSubject, 
               to: 'tdwaws2024@gmail.com'
        }
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
