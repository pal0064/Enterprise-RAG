#!/bin/bash

# Define the URL for the TorchServe inference API
URL="http://localhost:8100/predictions/speecht5_tts"

# Define the input JSON payload
INPUT_JSON=$(cat <<EOF
{
  "inputs": ["Hi team rag 3?"],
  "voice":"default"
}
EOF
)

# Send the request to the TorchServe inference API
RESPONSE=$(curl -X POST "$URL" -H "Content-Type: application/json" -d "$INPUT_JSON")

# Check if the response contains valid data
if [[ $RESPONSE == *"["* ]]; then
  # Write the response to a file
  echo $RESPONSE > output.json
#   echo $RESPONSE | jq -r '.[0]' > output.json
  echo "Inference successful, output saved to output.json"
fi