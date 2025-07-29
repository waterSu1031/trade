# TorchServe Docker Image for PatchTST Model
FROM pytorch/torchserve:latest-cpu

# If you need GPU support, use:
# FROM pytorch/torchserve:latest-gpu

# Install additional dependencies for PatchTST
USER root
RUN pip install --no-cache-dir \
    einops \
    pandas \
    scikit-learn

# Create model store directory
RUN mkdir -p /home/model-server/model-store

# Set environment variables
ENV JAVA_OPTS="-Xmx2g"
ENV TS_CONFIG_FILE=/home/model-server/config.properties

# Copy configuration file (will be created)
COPY config.properties /home/model-server/config.properties

# Switch back to model-server user
USER model-server

# Expose ports
# Inference API
EXPOSE 8080
# Management API  
EXPOSE 8081
# Metrics API
EXPOSE 8082

# Model store will be mounted at runtime
WORKDIR /home/model-server

# TorchServe will start automatically with the base image CMD