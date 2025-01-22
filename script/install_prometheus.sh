#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Ensure Helm is installed
if ! command_exists helm; then
    echo "Helm is not installed. Please install Helm before running this script."
    exit 1
fi

# Add Prometheus Helm repository
echo "Adding Prometheus repository..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Update Helm repositories
echo "Updating Helm repositories..."
helm repo update

# Install Prometheus Stack using Helm
echo "Installing Prometheus stack..."
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack

# Verify the installation
echo "Verifying Prometheus installation..."
kubectl get pods -n default | grep prometheus

echo "Prometheus installation completed!"
