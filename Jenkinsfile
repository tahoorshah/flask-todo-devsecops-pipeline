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
                dependencyCheck additionalArguments: '--scan ./ --format ALL', odcInstallation: 'OWASP-DepCheck'
                dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
            }
        }

        stage('SonarQube Code Analysis') {
            steps {
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

        stage('Secure Docker Build & Export') {
            steps {
                echo 'Building image and exporting to tarball for Minikube...'
                script {
                    sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                    sh "docker save ${IMAGE_NAME}:${IMAGE_TAG} > image.tar"
                }
            }
        }

        stage('Load into Minikube') {
            steps {
                echo 'Transferring and importing image into Minikube...'
                // Using the SSH bridge established to bypass user permission constraints
                sh "ssh -o StrictHostKeyChecking=no tshah@localhost 'minikube image load < /var/lib/jenkins/workspace/flask-todo/image.tar'"
            }
        }

        stage('Trivy Image Vulnerability Scan') {
            steps {
                echo 'Scanning container image for vulnerabilities...'
                sh "trivy image --exit-code 1 --severity HIGH,CRITICAL ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Secure Deployment') {
            steps {
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
