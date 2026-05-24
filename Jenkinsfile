pipeline {
    agent any

    environment {
        // Tagging image for the internal Minikube registry
        IMAGE_NAME   = 'localhost:5000/flask-todo'
        IMAGE_TAG    = 'latest'
        NAMESPACE    = 'production'
        
        // Configured Jenkins Credential IDs
        SONAR_CRED_ID  = 'sonar-token1'
        KUBE_CRED_ID   = 'kubeconfig-file'
    }

    stages {
        stage('Checkout Source') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('OWASP Dependency-Check Scan') {
            steps {
                echo 'Running Composition Analysis for software vulnerabilities...'
                dependencyCheck additionalArguments: '--scan ./ --format ALL', odcInstallation: 'OWASP-DepCheck'
                dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
            }
        }

        stage('SonarQube Code Analysis') {
            steps {
                echo 'Executing static application security testing (SAST)...'
                script {
                    def scannerHome = tool name: 'SonarQubeScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                    withCredentials([string(credentialsId: "${SONAR_CRED_ID}", variable: 'SONAR_TOKEN')]) {
                        withSonarQubeEnv('SonarQube') {
                            sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectKey=flask-todo -Dsonar.token=\${SONAR_TOKEN}"
                        }
                    }
                }
            }
        }

        stage('SonarQube Quality Gate Validation') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') error "SonarQube Quality Gate failed: ${qg.status}"
                    }
                }
            }
        }

        stage('Secure Multi-Stage Docker Build') {
            steps {
                echo 'Building and pushing image to local Minikube registry...'
                script {
                    // Build image and push to the registry-addon service
                    sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                    sh "docker push ${IMAGE_NAME}:${IMAGE_TAG}"
                }
            }
        }

        stage('Trivy Image Vulnerability Scan') {
            steps {
                echo 'Scanning image...'
                sh "trivy image --exit-code 1 --severity HIGH,CRITICAL ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Secure Deployment to Kubernetes') {
            steps {
                withKubeConfig([credentialsId: "${KUBE_CRED_ID}"]) {
                    sh '''
                        kubectl apply -f k8s/namespace.yaml
                        kubectl apply -f k8s/
                    '''
                }
            }
        }

        stage('Verification & Health Audit') {
            steps {
                withKubeConfig([credentialsId: "${KUBE_CRED_ID}"]) {
                    sh "kubectl rollout status deployment/flask-todo -n ${NAMESPACE} --timeout=90s"
                }
            }
        }
    }
}
