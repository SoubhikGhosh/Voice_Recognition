#!/bin/bash

# Function to fetch the IP address dynamically using Python
get_ip() {
  python3 - <<EOF
import socket
import subprocess
import platform

def get_ip():
    try:
        if platform.system() == "Darwin":  # macOS
            ip = subprocess.check_output(["ipconfig", "getifaddr", "en0"]).decode().strip()
        elif platform.system() == "Linux":  # Linux
            ip = subprocess.check_output(["hostname", "-I"]).decode().split()[0]
        else:  # Default to socket for other systems
            ip = socket.gethostbyname(socket.gethostname())
        return ip
    except Exception as e:
        print(f"Error detecting IP: {e}")
        exit(1)

print(get_ip())
EOF
}

# Get the Backend IP dynamically
BACKEND_IP=$(get_ip)
ROOT_CA_KEY="./certificates/rootCA.key"
ROOT_CA_CERT="./certificates/rootCA.pem"
BACKEND_KEY="./certificates/backend.key"
BACKEND_CSR="./certificates/backend.csr"
BACKEND_CERT="./certificates/backend.crt"

echo "Detected Backend IP: $BACKEND_IP"

# Check if the backend IP was retrieved
if [ -z "$BACKEND_IP" ]; then
  echo "Error: Unable to determine a valid backend IP address."
  exit 1
fi

# Ensure certificates directory exists
if [ ! -d "./certificates" ]; then
  mkdir -p ./certificates
fi

echo "Generating backend certificate..."

# Regenerate the backend certificate
openssl genrsa -out $BACKEND_KEY 2048
openssl req -new -key $BACKEND_KEY -out $BACKEND_CSR -subj "/CN=$BACKEND_IP"
openssl x509 -req -in $BACKEND_CSR -CA $ROOT_CA_CERT -CAkey $ROOT_CA_KEY -CAcreateserial -out $BACKEND_CERT -days 500 -sha256

echo "Backend certificate regenerated!"

# Start the backend server with SSL if certificates exist
cert_file="./certificates/backend.crt"
key_file="./certificates/backend.key"

if [ ! -f "$cert_file" ] || [ ! -f "$key_file" ]; then
  echo "Error: SSL certificates are missing."
  exit 1
fi

echo "Starting backend server..."
python3 app.py
