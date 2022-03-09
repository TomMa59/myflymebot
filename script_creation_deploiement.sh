#!/bin/bash

# Authentification
az login --output none
az account set \
    --subscription "OCR - Microsoft Azure"

ma_localisation=westeurope
resource_group_name=myflymebot


# Resource group creation
#az group create \
    --location $ma_localisation \
    --name $resource_group_name

#Luis resources creation
az cognitiveservices account create \
     -n luis-authoring  \
     -g $resource_group_name \
     --kind LUIS.Authoring \
     --sku F0 \
     -l $ma_localisation \
     --yes

#az cognitiveservices account create \
     -n luis-pred \
     -g $resource_group_name \
     --kind LUIS \
     --sku F0 \
     -l westeurope \
     --yes

# Luis API authentication key
LuisAPIKey=$(az cognitiveservices account keys list \
                    --name luis-authoring \
                    --resource-group $resource_group_name \
                    --query key1 -o tsv)
export LuisAPIKey

# Create, train and publish luis app
python luis_app_creation_train_publish.py
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!LuisAPPId=$(bf luis:application:show --appId)
echo $LuisAPPId

# Addition of the prediction resource to the Luis app

arm_access_token=$(az account get-access-token \
    --resource=https://management.core.windows.net/ \
    --query accessToken \
    --output tsv)


luis set --appId $LuisAPPId --versionId 0.1 --authoringKey $LuisAPIKey --region westeurope

#az cognitiveservices account purge --location westeurope --resource-group myflymebot --name luis-authoring
#az account show
#tenant_id_test=$(az account show --query tenantId -o tsv)
#echo $tenant_id_test