#!/bin/bash

# Clean previous build
echo "Deleting previous build"
rm -rf python auth_layer.zip

# Install using uv (Linux binary target)
echo "Installing via uv"
uv pip install -r requirements.txt \
    --target python \
    --python-version 3.14 \
    --python-platform linux \
    --only-binary=:all:

# Zip it
echo "zipping auth_layer.zip"
zip -r auth_layer.zip python

# Cleanup
echo "cleaning it up"
rm -rf python

echo "Done! Upload infrastructure/layers/auth-layer/auth_layer.zip to AWS."