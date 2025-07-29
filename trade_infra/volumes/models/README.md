# ML Models Directory - TorchServe

This directory stores trained PatchTST models for serving.

## Directory Structure

```
models/
├── patch_tst_trade.mar   # Model archive file
├── patch_tst_trade_v2.mar # Version 2
└── config/
    └── model_config.json  # Optional model-specific config
```

## Model Format

Models must be in TorchServe Model Archive (.mar) format.

### Creating a Model Archive

```bash
# Basic command
torch-model-archiver \
  --model-name patch_tst_trade \
  --version 1.0 \
  --model-file model.py \
  --serialized-file model.pth \
  --handler handler.py \
  --extra-files index_to_name.json,config.json

# For PatchTST
torch-model-archiver \
  --model-name patch_tst_trade \
  --version 1.0 \
  --model-file patch_tst_model.py \
  --serialized-file patch_tst_weights.pth \
  --handler patch_tst_handler.py \
  --extra-files config.json,scaler.pkl \
  --requirements-file requirements.txt
```

## PatchTST Handler Requirements

Your `patch_tst_handler.py` should include:
- Data preprocessing (windowing, patching)
- Scaling/normalization
- Model inference
- Post-processing (inverse scaling)

Example handler structure:
```python
class PatchTSTHandler(BaseHandler):
    def preprocess(self, data):
        # Convert input to patches
        pass
    
    def inference(self, data):
        # Run PatchTST model
        pass
    
    def postprocess(self, data):
        # Format predictions
        pass
```

## Adding New Models

1. Create your model archive (.mar file)
2. Copy the .mar file to this directory
3. Register the model via Management API:
   ```bash
   curl -X POST "http://localhost:8081/models?model_name=patch_tst_trade&url=patch_tst_trade.mar"
   ```
4. Or place in model-store and restart TorchServe

## Model Versioning

- Use descriptive names: `patch_tst_trade_v1.mar`, `patch_tst_trade_v2.mar`
- Keep at least 2 versions for rollback
- Document changes in CHANGELOG.md

## API Usage

### Inference
```bash
# Single prediction
curl -X POST http://localhost:8080/predictions/patch_tst_trade \
  -H "Content-Type: application/json" \
  -d '{"data": [[1.2, 1.3, 1.4, ...]]}'

# Batch prediction  
curl -X POST http://localhost:8080/predictions/patch_tst_trade \
  -H "Content-Type: application/json" \
  -d '{"data": [[...], [...], [...]]}'
```

### Model Management
```bash
# List models
curl http://localhost:8081/models

# Get model info
curl http://localhost:8081/models/patch_tst_trade
```