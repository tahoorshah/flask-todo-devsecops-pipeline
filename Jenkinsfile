pipeline {
    agent any

    environment {
        // Architecture definitions
        IMAGE_NAME   = 'localhost:5000/flask-todo'
        IMAGE_TAG    = 'latest'
        NAMESPACE    = 'production'
        
        // Credential IDs configured inside Jenkins
        SONAR_CRED_ID  = 'sonar-token'
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
                    
                    withSonarQubeEnv('SonarQube') {
                        // Using single quotes prevents Groovy from parsing the shell environment variable prematurely
                        sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectKey=flask-todo -Dsonar.sources=. -Dsonar.token=\${SONAR_TOKEN}"
                    }
                }
            }
        }

        stage('SonarQube Quality Gate Validation') {
            steps {
                echo 'Enforcing security quality boundaries...'
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline aborted: Code failed SonarQube Quality Gate metrics! Status: ${qg.status}"
                        }
                    }
                }
            }
        }

        stage('Secure Multi-Stage Docker Build') {
            steps {
                echo 'Injecting shell runtime environment into Minikube container engine...'
                script {
                    sh '''
                        eval \$(minikube docker-env)
                        docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    '''
                }
            }
        }

        stage('Trivy Image Vulnerability Scan') {
            steps {
                echo 'Scanning container image filesystem for severe vulnerabilities...'
                sh "trivy image --exit-code 1 --severity HIGH,CRITICAL ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Secure Deployment to Kubernetes') {
            steps {
                echo "Deploying application workloads into Kubernetes namespace: ${NAMESPACE}"
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
                echo 'Auditing final lifecycle state of deployment rollout...'
                withKubeConfig([credentialsId: "${KUBE_CRED_ID}"]) {
                    sh """
                        kubectl rollout status deployment/flask-todo -n ${NAMESPACE} --timeout=90s
                        kubectl get pods -n ${NAMESPACE}
                    """
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution cycle complete.'
        }
        success {
            echo 'Application securely validated, scanned, and successfully running in production!'
        }
        failure {
            echo 'Security vulnerability or build error detected. Review stage execution logs above.'
        }
    }
}
