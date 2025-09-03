# Student Progress Analyzer

A Docker-based Flask application to analyze and visualize student progress with PDF report generation.

## Features
- Student progress analysis
- Interactive data visualization with Plotly
- PDF report generation using WeasyPrint
- Multi-platform support (x86_64 and ARM64/Raspberry Pi)

## Requirements
- Docker and Docker Compose
- Raspberry Pi 4B with at least 4GB RAM (recommended for ARM64 deployment)

## Quick Start

### For x86_64 systems:
```bash
docker-compose up --build
```

### For Raspberry Pi 4B:
```bash
# Ensure you're using Docker with BuildKit support
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build and run
docker-compose up --build
```

### Building for specific platform:
```bash
# For ARM64 (Raspberry Pi 4B)
docker buildx build --platform linux/arm64 -t student-progress:arm64 .

# For AMD64
docker buildx build --platform linux/amd64 -t student-progress:amd64 .
```

## Raspberry Pi Optimization Notes

This application has been optimized for Raspberry Pi 4B deployment:

- Uses Python 3.11 (stable and well-supported on ARM)
- Leverages piwheels.org for pre-compiled ARM packages
- Implements memory limits appropriate for Pi hardware
- Includes build tools for compiling packages when needed
- Non-root user for enhanced security

### Pi-Specific Performance Tips:

1. **Memory**: Ensure your Pi has at least 4GB RAM for optimal performance
2. **Storage**: Use a high-quality SD card (Class 10 or better) or USB 3.0 SSD
3. **Cooling**: Adequate cooling recommended during builds and heavy usage
4. **Build Time**: Initial build may take 15-30 minutes on Pi - this is normal

## Accessing the Application

Once running, access the application at: `http://localhost:8000` (or your Pi's IP address)

## Troubleshooting

### Build Issues on Raspberry Pi:
- Increase swap space if build fails due to memory issues
- Ensure Docker has enough resources allocated
- Use `docker system prune` to free up space before building

### Runtime Issues:
- Check container logs: `docker-compose logs student-progress`
- Verify port 8000 is not in use by other applications
- Ensure all required files are present in the project directory
