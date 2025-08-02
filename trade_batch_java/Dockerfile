FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /app

# Copy pom.xml and download dependencies
COPY pom.xml .
COPY mvnw .
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline -B

# Copy source code and build
COPY src ./src
RUN ./mvnw clean package -DskipTests

# Runtime stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Install required packages for IBKR connection
RUN apk add --no-cache tzdata curl

# Create non-root user
RUN addgroup -g 1000 -S appuser && \
    adduser -u 1000 -S appuser -G appuser

# Copy JAR from builder stage
COPY --from=builder /app/target/*.jar app.jar

# Create directories for logs
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser

# JVM memory settings and timezone
ENV JAVA_OPTS="-Xms512m -Xmx2g -Duser.timezone=Asia/Seoul"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/actuator/health || exit 1

# Expose port
EXPOSE 8080

# Run the application
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]