#!/bin/bash

# Authentification
az login --output none
az account set \
    --subscription "OCR - Microsoft Azure"

ma_localisation=westeurope

# Resource group creation
# az group create \
#     --location $ma_localisation \
#     --name myflymebot

#Luis resources creation
# az cognitiveservices account create \
#      -n luis-authoring  \
#      -g myflymebot \
#      --kind LUIS.Authoring \
#      --sku F0 \
#      -l $ma_localisation \
#      --yes

# az cognitiveservices account create \
#      -n luis-pred \
#      -g myflymebot \
#      --kind LUIS \
#      --sku F0 \
#      -l westeurope \
#      --yes

# Luis API authentication key
LuisAuthKey=$(az cognitiveservices account keys list \
                    --name luis-authoring \
                    --resource-group myflymebot \
                    --query key1 -o tsv)
export LuisAuthKey

# Create, train and publish luis app
#python luis_app_creation_train_publish.py
LuisAPPId=$(luis list apps --take 1 | grep -o -P -- '"id": "\K.{36}')

# Addition of the prediction resource to the Luis app
arm_access_token=$(az account get-access-token \
    --resource=https://management.core.windows.net/ \
    --query accessToken \
    --output tsv)

jq '."resourceGroup" = "myflymebot"' id.json > tmp.$$.json && mv tmp.$$.json id.json  
jq '."accountName" = "luis-pred"' id.json > tmp.$$.json && mv tmp.$$.json id.json  

luis set \
    --appId $LuisAPPId \
    --versionId 0.1 \
    --authoringKey $LuisAuthKey \
    --region westeurope

#luis add appazureaccount \
#    --in id.json \
#    --appId $LuisAPPId --armToken $arm_access_token

LuisAPIKey=$(az cognitiveservices account keys list \
                    --name luis-pred \
                    -g myflymebot \
                    --query key1 -o tsv)
LuisAPIHostName="westeurope.api.cognitive.microsoft.com"

# App service, Webapp and bot
# Registration
read -s -p 'Define your Microsoft App Passwords (please be careful to remeber it) :' -r MicrosoftAppPassword
# az ad app create \
#     --display-name "myflymebottmz202203" \
#     --password $MicrosoftAppPassword \
#     --available-to-other-tenants
MicrosoftAppId=$(az ad app list --display-name myflymebottmz202203 | grep -o -P -- '"appId": "\K.{36}')

# Service Plan
# az appservice plan create \
#     -g myflymebot \
#     -n flymebotserviceplan \
#     --location westeurope \
#     --is-linux

# Web App
# az webapp create \
#     -g myflymebot \
#     -p flymebotserviceplan \
#     -n myflymebottmz202203 \
#     --runtime "python:3.7"

# az bot create --appid $MicrosoftAppId \
#                 --password $MicrosoftAppPassword \
#                 --kind registration \
#                 --name myflymebot \
#                 --resource-group myflymebot \
#                 --endpoint "https://myflymebottmz202203.azurewebsites.net/api/messages" \
#                 --output none

# App insights
# az monitor app-insights component create \
#     --app luis-follow \
#     --location westeurope \
#     --kind web \
#     -g myflymebot \
#     --application-type web
InstrumentationKey=$(az monitor app-insights component show --app luis-follow --resource-group myflymebot --query instrumentationKey -o tsv)


#Deployment
# Web App config
#  az webapp config appsettings set \
#      -n myflymebottmz202203 \
#      -g myflymebot \
#      --settings InstrumentationKey=$InstrumentationKey \
#                  LuisAppId=$LuisAPPId \
#                  LuisAPIKey=$LuisAPIKey \
#                  LuisAPIHostName=$LuisAPIHostName \
#                  MicrosoftAppId=$MicrosoftAppId \
#                  MicrosoftAppPassword=$MicrosoftAppPassword \
#                  WEBSITE_WEBDEPLOY_USE_SCM=true
#                 --output none

# az webapp config set \
#     -n myflymebottmz202203 \
#     -g myflymebot \
#     --startup-file="python3.7 -m aiohttp.web -H 0.0.0.0 -P 8000 app:init_func"

az webapp deployment github-actions add --repo "TomMa59/myflymebot" \
                                        --branch main \
                                        -g myflymebot \
                                        -n myflymebottmz202203 \
                                        --force \
                                        --login-with-github \










# az webapp deployment source config \
#     --branch main \
#     --name myflymebottmz202203 \
#     --repo-url https://github.com/TomMa59/myflymebot \
#     --resource-group myflymebot \
#     --repository-type github \
#     --github-action


#az cognitiveservices account purge --location westeurope --resource-group myflymebot --name luis-authoring