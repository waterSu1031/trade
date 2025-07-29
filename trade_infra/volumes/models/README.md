# ML Models Directory

This directory stores trained models for serving.

## Directory Structure

```
models/
└── trade_model/          # Model name
    ├── 1/               # Version 1
    │   ├── saved_model.pb
    │   └── variables/
    ├── 2/               # Version 2
    │   ├── saved_model.pb
    │   └── variables/
    └── ...
```

## Model Format

Models should be in TensorFlow SavedModel format:
- `saved_model.pb`: Model graph definition
- `variables/`: Model weights and variables

## Adding New Models

1. Create a new version directory (incrementing number)
2. Copy your SavedModel files into the version directory
3. Update model-serving.yml if needed
4. Restart the ml-serving container

## Model Versioning

- Always use incremental version numbers (1, 2, 3, ...)
- Keep at least the last 2 versions for rollback
- Document model changes in a CHANGELOG