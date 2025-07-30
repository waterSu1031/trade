FROM openjdk:17-slim

WORKDIR /app

# Copy the JAR file
COPY target/*.jar app.jar

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Run the application
ENTRYPOINT ["java", "-jar", "app.jar"]