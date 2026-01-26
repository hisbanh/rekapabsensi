#!/bin/bash

echo "Testing Docker build locally..."

# Use simple Dockerfile
docker build -f Dockerfile.simple -t sipa-yaumi-test . 

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "Testing container..."
    docker run -p 8080:8080 -e PORT=8080 -e SECRET_KEY=test-key sipa-yaumi-test
else
    echo "❌ Build failed!"
    exit 1
fi
