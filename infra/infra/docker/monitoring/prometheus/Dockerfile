FROM prom/prometheus:latest

# Copy prometheus configuration
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Expose port
EXPOSE 9090

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1