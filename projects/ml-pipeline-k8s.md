---
title: "ML Pipeline Orchestrator on Kubernetes"
slug: ml-pipeline-k8s
date: 2024-06-10
type: github
description: "Kubernetes-native machine learning training and deployment pipeline with auto-scaling, experiment tracking, and model versioning."
technologies:
  - Kubernetes
  - Airflow
  - MLflow
  - Docker
  - Python
tags:
  - mlops
  - kubernetes
  - automation
  - ci-cd
featured: true
featured_image: null
github_url: https://github.com/muhsinkompas/ml-pipeline-k8s
demo_url: null
stars: 124
forks: 34
draft: false
---

# ML Pipeline Orchestrator on Kubernetes

A production-ready MLOps platform for orchestrating machine learning workflows on Kubernetes, featuring automated training, versioning, and deployment.

## Motivation

Managing ML workloads in production requires:
- Reproducible experiments
- Efficient resource utilization
- Automated deployment pipelines
- Model monitoring and rollback

This platform addresses these challenges with a cloud-native approach.

## System Components

### 1. Airflow for Orchestration
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

dag = DAG(
    'ml_training_pipeline',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily'
)

train = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag
)
```

### 2. Kubernetes Jobs for Training
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: model-training
spec:
  template:
    spec:
      containers:
      - name: trainer
        image: ml-trainer:latest
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: 16Gi
```

### 3. MLflow for Experiment Tracking
```python
import mlflow

with mlflow.start_run():
    mlflow.log_params({"lr": 0.001, "batch_size": 32})
    mlflow.log_metrics({"accuracy": 0.95, "loss": 0.23})
    mlflow.pytorch.log_model(model, "model")
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Airflow Scheduler                  │
│         (Workflow Orchestration)                │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼──────┐  ┌──────▼────────┐
│  Data Prep   │  │  Model Train  │
│  K8s Job     │  │  K8s Job      │
└───────┬──────┘  └──────┬────────┘
        │                 │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  MLflow Server  │
        │  (Tracking)     │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Model Registry │
        │  (Versioning)   │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Seldon Core    │
        │  (Serving)      │
        └─────────────────┘
```

## Features

### Auto-scaling
- **Horizontal Pod Autoscaler**: Scale training jobs based on CPU/GPU usage
- **Cluster Autoscaler**: Add nodes dynamically for large experiments
- **Vertical Pod Autoscaler**: Optimize resource requests

### Experiment Management
- Centralized tracking of hyperparameters and metrics
- Version control for datasets and models
- Comparison of experiment results
- Artifact storage (models, plots, logs)

### Deployment Pipeline
1. Model trained and logged to MLflow
2. Automated testing (accuracy, latency, memory)
3. Promotion to staging environment
4. A/B testing against current production model
5. Gradual rollout to production
6. Monitoring and alerting

### Resource Optimization
- GPU sharing for small models
- Spot instances for non-critical training
- Dynamic resource allocation
- Cost tracking per experiment

## Setup

### Prerequisites
- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm 3.x
- Docker registry access

### Installation

1. **Deploy Infrastructure**
```bash
# Add Helm repos
helm repo add apache-airflow https://airflow.apache.org
helm repo add mlflow https://community-charts.github.io/helm-charts

# Install Airflow
helm install airflow apache-airflow/airflow -f airflow-values.yaml

# Install MLflow
helm install mlflow mlflow/mlflow -f mlflow-values.yaml
```

2. **Deploy Application**
```bash
# Build images
docker build -t ml-pipeline:latest .

# Deploy to cluster
kubectl apply -f k8s/
```

3. **Configure Airflow DAGs**
```bash
kubectl cp dags/ airflow-scheduler-0:/opt/airflow/dags/
```

## Usage Example

### Train a Model

```python
# Submit training job
from ml_pipeline import PipelineClient

client = PipelineClient(api_url="http://airflow.example.com")

run = client.submit_training(
    model_type="resnet50",
    dataset="imagenet",
    hyperparams={
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 100
    },
    resources={
        "gpus": 4,
        "memory": "32Gi"
    }
)

print(f"Training job submitted: {run.id}")
```

### Monitor Progress

```bash
# View job status
kubectl get jobs -l pipeline=ml-training

# Stream logs
kubectl logs -f job/model-training-abc123

# Check MLflow UI
open http://mlflow.example.com
```

### Deploy Model

```python
# Promote to production
client.promote_model(
    model_id="abc123",
    environment="production",
    traffic_percentage=10  # Canary deployment
)
```

## Performance Metrics

| Metric | Value |
|--------|-------|
| Pipeline Setup Time | < 5 min |
| Training Job Startup | < 30 sec |
| Model Deployment | < 2 min |
| Cost Savings (vs cloud ML platforms) | ~40% |

## Monitoring

### Prometheus Metrics
- Training job duration
- Resource utilization (CPU, GPU, Memory)
- Model serving latency
- Prediction error rates

### Grafana Dashboards
- Training pipeline overview
- Cost analysis
- Model performance comparison
- Infrastructure health

## Best Practices

1. **Version Everything**: Code, data, models, and configs
2. **Test Pipelines**: Unit tests for data processing and model logic
3. **Resource Limits**: Prevent jobs from consuming entire cluster
4. **Secrets Management**: Use Kubernetes secrets for credentials
5. **Backup Models**: Regular snapshots of model registry

## Troubleshooting

### Common Issues

**Job fails with OOM**
```bash
# Increase memory limits
kubectl edit job model-training-abc123
```

**GPU not allocated**
```bash
# Check node labels
kubectl get nodes --show-labels | grep nvidia
```

**Airflow DAG not appearing**
```bash
# Sync DAGs
kubectl exec -it airflow-scheduler-0 -- airflow dags list
```

## Roadmap

- [ ] Support for distributed training (Horovod, DeepSpeed)
- [ ] Integration with Feast for feature store
- [ ] Automated model drift detection
- [ ] Multi-cloud support (AWS, GCP, Azure)
- [ ] Cost optimization recommendations

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

Apache 2.0 - See [LICENSE](LICENSE)
