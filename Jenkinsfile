pipeline {
    agent any

    environment {
        IMAGE_NAME   = 'flask-todo'
        IMAGE_TAG    = 'latest'
        NAMESPACE    = 'production'
        KUBE_CRED_ID = 'kubeconfig-file'
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
                echo 'Running Composition Analysis...'
                dependencyCheck additionalArguments: '--scan ./ --format ALL', odcInstallation: 'OWASP-DepCheck'
                dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
            }
        }

        stage('SonarQube Code Analysis') {
            steps {
                echo 'Executing SAST analysis...'
                script {
                    def scannerHome = tool name: 'SonarQubeScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                    withCredentials([string(credentialsId: 'sonar-token1', variable: 'SONAR_TOKEN')]) {
                        withSonarQubeEnv('SonarQube') {
                            sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectKey=flask-todo -Dsonar.token=\${SONAR_TOKEN}"
                        }
                    }
                }
            }
        }

        stage('Secure Docker Build') {
            steps {
                echo 'Building image...'
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage('Trivy Image Vulnerability Scan') {
            steps {
                echo 'Scanning container image (Strict Gate)...'
                // Re-enabled --exit-code 1 to stop the build on CRITICAL vulnerabilities.
                // This ensures you do not deploy insecure code.
                sh "trivy image --severity CRITICAL --exit-code 1 ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Load into Minikube') {
            steps {
                echo 'Injecting image into Minikube cluster...'
                sh "ssh -o StrictHostKeyChecking=no tshah@localhost 'MINIKUBE_HOME=/home/tshah/.minikube minikube image load ${IMAGE_NAME}:${IMAGE_TAG}'"
            }
        }

        stage('Secure Deployment') {
            steps {
                echo 'Deploying to Kubernetes...'
                withKubeConfig([credentialsId: "${KUBE_CRED_ID}"]) {
                    sh '''
                        kubectl apply -f k8s/namespace.yaml
                        kubectl apply -f k8s/
                        kubectl rollout status deployment/flask-todo -n ${NAMESPACE} --timeout=90s
                    '''
                }
            }
        }
    }
}
