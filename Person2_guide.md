
---

### Part 1: The Master File Breakdown

#### 1. The Entryway (API Service)
*   **What it is:** The front door of your application.
*   **Files used:** 
    *   `api-service/app.py`: A FastAPI web server that acts as a "Producer"[cite: 4].
    *   `api-service/Dockerfile`: The blueprint to package the API into a Linux container and expose Port 8000[cite: 4].
    *   `api-service/requirements.txt`: The Python dependencies[cite: 4].
*   **Why it was built:** If a user submits a URL and the server takes 10 seconds to scrape it, the user is stuck staring at a loading screen. If 1,000 users do this, the server crashes.
*   **How & When it's used:** It runs constantly in Kubernetes. It accepts the URL, instantly drops it into the Kafka waiting room, and immediately responds to the user with `{"status": "success"}`[cite: 4]. 

#### 2. The Muscle (Scraper Workers)
*   **What it is:** The background heavy lifters.
*   **Files used:**
    *   `scraper-worker/worker.py`: A Python script that acts as a Kafka "Consumer"[cite: 4].
    *   `scraper-worker/Dockerfile`: Packages the worker. Notice it has NO `EXPOSE` port command because workers don't receive web traffic; they only reach *out* to Kafka[cite: 4].
    *   `scraper-worker/requirements.txt`: Dependencies for Kafka and scraping[cite: 4].
*   **Why it was built:** To decouple the heavy scraping process from the web server. 
*   **How & When it's used:** Runs infinitely in the background. It features a `while True` loop that repeatedly tries to connect to Kafka[cite: 4]. Once connected, it waits. When a URL appears in the queue, it grabs it, processes it, and waits for the next one[cite: 4].

#### 3. The Production Fleet (Kubernetes Infrastructure)
*   **What it is:** The blueprints that tell the cloud how to run your containers.
*   **Files used:**
    *   `infrastructure/k8s/kafka-deployment.yaml`: Creates a single pod containing *both* Zookeeper (the manager) and Kafka (the queue) so they can communicate seamlessly over localhost[cite: 4].
    *   `infrastructure/k8s/service.yaml`: Creates a network router (`kafka-service:9092`) so other pods can find the Kafka queue[cite: 4].
    *   `infrastructure/k8s/api-deployment.yaml`: Tells Kubernetes to run exactly 2 replicas of your API and injects the `KAFKA_BROKER` map so it can find the queue[cite: 4].
    *   `infrastructure/k8s/worker-deployment.yaml`: Tells Kubernetes to run 3 replicas of your worker, also injecting the Kafka map[cite: 4].
*   **Why it was built:** Because manually typing `docker run` is for amateurs. K8s automatically restarts crashed containers and scales your traffic.

#### 4. The Assembly Line (CI/CD Pipeline)
*   **What it is:** Your automated DevOps robot.
*   **Files used:**
    *   `ci-cd/docker-compose.yml`: Spins up your entire local testing sandbox (Kafka, Postgres, API, Worker, Jenkins) and wires Jenkins to the `minikube` network[cite: 4].
    *   `ci-cd/Dockerfile.jenkins`: Upgrades a standard Jenkins image by logging in as `root` and installing the Docker CLI and `kubectl` so it can command your infrastructure[cite: 4].
    *   `Jenkinsfile`: The literal instruction manual for your robot[cite: 4].
*   **How it works:** It executes 4 strict stages[cite: 4]:
    1.  **Clone:** Downloads the latest code from GitHub.
    2.  **Build:** Packages your Python code into fresh Docker images.
    3.  **Push:** Securely logs into Docker Hub (`mithilesh321`) and uploads the images.
    4.  **Deploy:** Uses your injected `kubeconfig` to command Minikube. It applies the Kafka infrastructure first, then your APIs/Workers, and finally triggers a `rollout restart` to execute a zero-downtime update.

---

### Part 2: The "Zero to Hero" Master Reset
If your laptop completely dies today, here are the exact commands to bring your entire DevOps architecture back to life from scratch on a new machine.

**1. Start the Local Foundations:**
```bash
git clone https://github.com/blast678/Distributed-Web-Scraper.git
cd Distributed-Web-Scraper/ci-cd
docker-compose up -d --build
minikube start
```

**2. Generate the Bypass Keys:**
*Create the uncorrupted Kubernetes config file so Jenkins can talk to Minikube[cite: 4].*
```bash
kubectl config view --flatten --minify > kubeconfig-fresh.yaml
sed -i -e 's/127\.0\.0\.1/host.docker.internal/g' -e 's/.*certificate-authority-data:.*/    insecure-skip-tls-verify: true/' kubeconfig-fresh.yaml
```
*(Open the file and manually change `host.docker.internal` to `minikube:8443`)*

**3. Configure Jenkins:**
1. Go to `http://localhost:8080` and unlock Jenkins.
2. Go to **Manage Jenkins -> Credentials**.
3. Add `docker-hub-credentials` (Username & Password).
4. Add `k8s-kubeconfig` (Upload the `kubeconfig-fresh.yaml` as a Secret File).
5. Create a new Pipeline pointing to your GitHub URL and target your `main` branch.
6. Click **Build Now**. Jenkins will build and deploy the entire architecture automatically.

---

### Part 3: The Ultimate Verification Tests
After Jenkins finishes a build, how do you prove to your team that the system is actually working? You run this exact 3-step test sequence.

**Test 1: Fleet Health Check**
Are all the containers actually running, or did they crash?
```bash
kubectl get pods
```
*(PASS CONDITION: You must see 1 Kafka pod, 2 API pods, and 3 Worker pods. All must show `Running` and `1/1` or `2/2` READY).*

**Test 2: Internal Comms Check**
Did the API and Workers successfully find Kafka using the K8s internal network?
```bash
kubectl logs -l app=scraper-api
kubectl logs -l app=scraper-worker
```
*(PASS CONDITION: Both logs must explicitly say `Successfully connected to Kafka at kafka-service:9092`[cite: 4]).*

**Test 3: The End-to-End Tracer Bullet**
Can data actually flow through the entire distributed system?
*   **Terminal 1 (Open the Tunnel):** `kubectl port-forward svc/api-service 8001:80`
*   **Terminal 2 (Watch the Workers):** `kubectl logs -l app=scraper-worker -f`
*   **Terminal 3 (Fire the Request):** 
    ```bash
    curl -X POST http://localhost:8001/scrape -H "Content-Type: application/json" -d "{\"url\": \"https://google.com\"}"
    ```