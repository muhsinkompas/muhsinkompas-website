---
title: "XAI Dashboard for Deep Learning"
slug: xai-dashboard
date: 2024-08-20
type: local
description: "Interactive web dashboard for explaining deep learning model predictions using SHAP, LIME, and Grad-CAM visualizations."
technologies:
  - PyTorch
  - SHAP
  - FastAPI
  - React
  - Plotly
tags:
  - machine-learning
  - explainability
  - deep-learning
  - visualization
featured: true
featured_image: null
github_url: https://github.com/muhsinkompas/xai-dashboard
demo_url: https://xai-demo.muhsinkompas.com
stars: 78
forks: 23
draft: false
---

# XAI Dashboard

An interactive web application for visualizing and understanding deep learning model decisions through state-of-the-art explainability techniques.

## Problem Statement

Deep learning models are often treated as "black boxes," making it difficult to trust their predictions in critical applications like healthcare, autonomous vehicles, and financial systems. This dashboard bridges the gap by providing intuitive visualizations of model behavior.

## Features

### Explainability Methods

1. **SHAP (SHapley Additive exPlanations)**
   - Feature importance at instance and global levels
   - Force plots for individual predictions
   - Dependence plots for feature interactions

2. **LIME (Local Interpretable Model-agnostic Explanations)**
   - Local linear approximations of model behavior
   - Text and image explanations
   - Perturbation-based analysis

3. **Grad-CAM (Gradient-weighted Class Activation Mapping)**
   - Heatmap visualizations for CNNs
   - Layer-wise activation analysis
   - Multi-class attribution

4. **Integrated Gradients**
   - Path-based attribution method
   - Baseline comparison
   - Convergence analysis

### Dashboard Capabilities

- **Real-time Inference**: Upload images or text for instant predictions
- **Batch Analysis**: Process multiple samples and compare explanations
- **Model Comparison**: Side-by-side comparison of different architectures
- **Export Reports**: Generate PDF/HTML reports of explanations
- **Audit Trail**: Log all predictions and explanations for compliance

## Architecture

```
Frontend (React + TypeScript)
       ↓
API Gateway (FastAPI)
       ↓
┌──────────────┬──────────────┬──────────────┐
│  ML Models   │  Explainers  │   Storage    │
│  (PyTorch)   │  (SHAP/LIME) │ (PostgreSQL) │
└──────────────┴──────────────┴──────────────┘
```

## Supported Models

- Image Classification (ResNet, EfficientNet, ViT)
- Object Detection (YOLO, Faster R-CNN)
- Text Classification (BERT, RoBERTa, GPT)
- Tabular Data (XGBoost, LightGBM, Neural Nets)

## Installation

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Get model prediction |
| `/explain/shap` | POST | SHAP explanation |
| `/explain/lime` | POST | LIME explanation |
| `/explain/gradcam` | POST | Grad-CAM heatmap |
| `/models` | GET | List available models |
| `/reports` | GET | Retrieve saved reports |

## Example Usage

```python
import requests

# Upload image for classification
files = {'file': open('cat.jpg', 'rb')}
response = requests.post('http://localhost:8000/predict', files=files)
prediction = response.json()

# Get SHAP explanation
payload = {
    'model_id': 'resnet50',
    'image_id': prediction['image_id'],
    'method': 'deep_explainer'
}
response = requests.post('http://localhost:8000/explain/shap', json=payload)
explanation = response.json()
```

## Use Cases

### Healthcare
- Explaining disease diagnosis from medical images
- Identifying critical features in patient data
- Building trust with medical professionals

### Autonomous Vehicles
- Understanding perception model decisions
- Debugging edge cases and failures
- Regulatory compliance and safety validation

### Finance
- Credit risk assessment transparency
- Fraud detection explanation
- Regulatory reporting (GDPR, SR 11-7)

## Performance

| Model Type | Explanation Time | Throughput |
|------------|------------------|------------|
| Image (ResNet50) | 2.3s | 15 req/min |
| Text (BERT) | 1.8s | 20 req/min |
| Tabular (XGBoost) | 0.4s | 60 req/min |

*Measured on NVIDIA Tesla V100 GPU*

## Future Roadmap

- [ ] Add counterfactual explanations
- [ ] Implement attention-based explanations for transformers
- [ ] Multi-modal model support (e.g., CLIP)
- [ ] Automated fairness and bias detection
- [ ] Integration with MLOps platforms (MLflow, Weights & Biases)

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this dashboard in your research, please cite:

```bibtex
@software{kompas2024xai,
  author = {Kompas, Muhsin},
  title = {XAI Dashboard for Deep Learning},
  year = {2024},
  url = {https://github.com/muhsinkompas/xai-dashboard}
}
```

## Acknowledgments

- SHAP library by Scott Lundberg
- LIME by Marco Tulio Ribeiro
- Grad-CAM implementation by PyTorch team
