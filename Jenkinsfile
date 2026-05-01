pipeline {
    agent any
    
    environment {
        // The ID of the vault lock we just created in Step 2
        DOCKER_CREDENTIALS_ID = 'docker-hub-credentials'
        // --- CHANGE THIS LINE TO YOUR DOCKER HUB USERNAME ---
        DOCKER_HUB_USER = 'mithilesh321'
    }
    
    stages {
        stage('Clone Repository') {
            steps {
                echo "Downloading the latest code from GitHub..."
                checkout scm
            }
        }
        
        stage('Build Docker Images') {
            steps {
                script {
                    echo "Building API Image..."
                    sh "docker build -t ${DOCKER_HUB_USER}/scraper-api:latest ./api-service"
                    
                    echo "Building Worker Image..."
                    sh "docker build -t ${DOCKER_HUB_USER}/scraper-worker:latest ./scraper-worker"
                }
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                script {
                    echo "Uploading finished containers to Docker Hub..."
                    withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS_ID, passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                        sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                        sh "docker push ${DOCKER_HUB_USER}/scraper-api:latest"
                        sh "docker push ${DOCKER_HUB_USER}/scraper-worker:latest"
                    }
                }
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    echo "Deploying the entire cloud infrastructure to Minikube..."
                    withCredentials([file(credentialsId: 'k8s-kubeconfig', variable: 'KUBECONFIG')]) {
                        
                        // 1. Deploy the Core Infrastructure (Kafka & Zookeeper) FIRST
                        sh "kubectl apply -f infrastructure/k8s/kafka-deployment.yaml --kubeconfig=\$KUBECONFIG"
                        sh "kubectl apply -f infrastructure/k8s/service.yaml --kubeconfig=\$KUBECONFIG"
                        
                        // 2. Deploy your Custom Code (API & Workers)
                        sh "kubectl apply -f infrastructure/k8s/api-deployment.yaml --kubeconfig=\$KUBECONFIG"
                        sh "kubectl apply -f infrastructure/k8s/worker-deployment.yaml --kubeconfig=\$KUBECONFIG"
                        
                        // 3. Force Kubernetes to pull the latest V2 images from Docker Hub and reboot the pods!
                        sh "kubectl rollout restart deployment api-deployment --kubeconfig=\$KUBECONFIG"
                        sh "kubectl rollout restart deployment worker-deployment --kubeconfig=\$KUBECONFIG"
                    }
                }
            }
        } 
    }
}