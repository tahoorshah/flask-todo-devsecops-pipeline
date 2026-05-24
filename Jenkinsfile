pipeline {
    agent any

    environment {
        IMAGE_NAME   = 'flask-todo'
        IMAGE_TAG    = 'latest'
        NAMESPACE    = 'production'
        KUBE_CRED_ID = 'kubeconfig-file'
        SONAR_TOKEN_ID = 'sonar-token1'
        OSS_INDEX_TOKEN_ID = 'sonatype-oss-token'
    }

    stages {
        stage('Checkout Source') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('Run Unit Tests & Coverage') {
            steps {
                echo 'Self-healing environment and generating coverage...'
                sh '''
                    # Ensure venv is created in the current workspace
                    python3 -m venv venv
                    ./venv/bin/pip install --upgrade pip
                    ./venv/bin/pip install -r requirements.txt pytest pytest-cov
                    
                    # Run tests relative to workspace
                    ./venv/bin/pytest --cov=app --cov-report=xml
                '''
            }
        }

        stage('OWASP Dependency-Check Scan') {
            steps {
                echo 'Running Composition Analysis...'
                withCredentials([string(credentialsId: "${OSS_INDEX_TOKEN_ID}", variable: 'OSS_TOKEN')]) {
                    dependencyCheck additionalArguments: "--scan ./ --format ALL --ossindexPassword ${OSS_TOKEN}", odcInstallation: 'OWASP-DepCheck'
                }
                dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
            }
        }

        stage('SonarQube Code Analysis') {
            steps {
                echo 'Executing SAST analysis...'
                script {
                    def scannerHome = tool name: 'SonarQubeScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                    withCredentials([string(credentialsId: "${SONAR_TOKEN_ID}", variable: 'SONAR_TOKEN')]) {
                        withSonarQubeEnv('SonarQube') {
                            sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectKey=flask-todo -Dsonar.token=\${SONAR_TOKEN} -Dsonar.python.coverage.reportPaths=coverage.xml"
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
