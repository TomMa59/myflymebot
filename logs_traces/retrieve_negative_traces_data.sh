#!/bin/bash

# Authentification
echo "Login and Authenticate..."
az login --output none
az account set \
     --subscription "OCR - Microsoft Azure" \
     --output none

# get negative traces for the last 24 hours, will be used to improve Luis application
echo $(az monitor app-insights query -a luis-follow \
                               --resource-group myflymebot \
                               --analytics-query "traces" \
                               --offset 2h20m) | jq '.' > trace_logs.json

python treat_neg_traces.py