FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.1

# Copy custom configuration
COPY elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml

# Set environment variables
ENV ES_JAVA_OPTS="-Xms512m -Xmx512m"
ENV discovery.type=single-node
ENV bootstrap.memory_lock=true

# Create data directory
RUN mkdir -p /usr/share/elasticsearch/data && \
    chown -R elasticsearch:elasticsearch /usr/share/elasticsearch/data

# Expose ports
EXPOSE 9200 9300

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:9200/_cluster/health || exit 1

USER elasticsearch