# TensorFlow Serving Docker Image
FROM tensorflow/serving:latest

# Set environment variables
ENV MODEL_BASE_PATH=/models
ENV MODEL_NAME=trade_model

# Copy model files (will be mounted via volume in production)
# COPY ./models /models

# Expose ports
# REST API Port
EXPOSE 8501
# gRPC Port
EXPOSE 8500

# The serving command is already set in the base image
# It will automatically serve models from MODEL_BASE_PATH/MODEL_NAME