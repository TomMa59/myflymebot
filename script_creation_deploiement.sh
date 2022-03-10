#!/bin/bash

# Authentification
az login --output none
az account set \
    --subscription "OCR - Microsoft Azure"

ma_localisation=westeurope

# Resource group creation
az group create \
     --location $ma_localisation \
     --name myflymebot

#Luis resources creation
az cognitiveservices account create \
      -n luis-authoring  \
      -g myflymebot \
      --kind LUIS.Authoring \
      --sku F0 \
      -l $ma_localisation \
      --yes

az cognitiveservices account create \
      -n luis-pred \
      -g myflymebot \
      --kind LUIS \
      --sku F0 \
      -l westeurope \
      --yes

sleep 10

# Luis API authentication key
LuisAuthKey=$(az cognitiveservices account keys list \
                    --name luis-authoring \
                    --resource-group myflymebot \
                    --query key1 -o tsv)
export LuisAuthKey

# Create, train and publish luis app
python luis_app_creation_train_publish.py
luis set --authoringKey $LuisAuthKey
LuisAPPId=$(luis list apps --take 1 | grep -o -P -- '"id": "\K.{36}')
export LuisAPPId

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
    --region westeurope

luis add appazureaccount \
    --in id.json \
    --appId $LuisAPPId --armToken $arm_access_token

LuisAPIKey=$(az cognitiveservices account keys list \
                    --name luis-pred \
                    -g myflymebot \
                    --query key1 -o tsv)
export LuisAPIKey
LuisAPIHostName="westeurope.api.cognitive.microsoft.com"
export LuisAPIHostName

# App service, Webapp and bot
# Registration
read -s -p 'Define your Microsoft App Passwords (please be careful to remember it) :' -r MicrosoftAppPassword
export MicrosoftAppPassword
az ad app create \
     --display-name "myflymebottmz202203" \
     --password $MicrosoftAppPassword \
     --available-to-other-tenants
MicrosoftAppId=$(az ad app list --display-name myflymebottmz202203 | grep -o -P -- '"appId": "\K.{36}')
export MicrosoftAppId

# Service Plan
az appservice plan create \
     -g myflymebot \
     -n flymebotserviceplan \
     --location westeurope \
     --is-linux

# Web App
az webapp create \
     -g myflymebot \
     -p flymebotserviceplan \
     -n myflymebottmz202203 \
     --runtime "python:3.7"

az bot create --appid $MicrosoftAppId \
                 --password $MicrosoftAppPassword \
                 --kind registration \
                 --name myflymebot \
                 --resource-group myflymebot \
                 --endpoint "https://myflymebottmz202203.azurewebsites.net/api/messages" \
                 --output none

# App insights
az monitor app-insights component create \
     --app luis-follow \
     --location westeurope \
     --kind web \
     -g myflymebot \
     --application-type web
InstrumentationKey=$(az monitor app-insights component show --app luis-follow --resource-group myflymebot --query instrumentationKey -o tsv)
export InstrumentationKey

#Deployment
# Web App config
az webapp config appsettings set \
      -n myflymebottmz202203 \
      -g myflymebot \
      --settings InstrumentationKey=$InstrumentationKey \
                  LuisAPPId=$LuisAPPId \
                  LuisAPIKey=$LuisAPIKey \
                  LuisAPIHostName=$LuisAPIHostName \
                  MicrosoftAppId=$MicrosoftAppId \
                  MicrosoftAppPassword=$MicrosoftAppPassword \
                  WEBSITE_WEBDEPLOY_USE_SCM=true \
                 --output none

az webapp config set \
     -n myflymebottmz202203 \
     -g myflymebot \
     --startup-file="python3.7 -m aiohttp.web -H 0.0.0.0 -P 8000 app:init_func"

gh auth login
gh secret set APP_ID --body $MicrosoftAppId \
            --repo "TomMa59/myflymebot"
gh secret set APP_PASSWORD --body $MicrosoftAppPassword \
            --repo "TomMa59/myflymebot"
gh secret set LUIS_APP_ID --body $LuisAPPId \
            --repo "TomMa59/myflymebot"
gh secret set LUIS_API_KEY --body $LuisAPIKey \
            --repo "TomMa59/myflymebot"
gh secret set LUIS_API_HOST_NAME --body $LuisAPIHostName \
            --repo "TomMa59/myflymebot"
gh secret set APPINSIGHTS_INSTRUMENTATION_KEY --body $InstrumentationKey \
            --repo "TomMa59/myflymebot"

gh secret set AZUREAPPSERVICE_PUBLISHPROFILE \
    --body "$(az webapp deployment list-publishing-profiles \
    --name myflymebottmz202203 \
    --resource-group myflymebot \
    --xml)" \
    --repo "TomMa59/myflymebot"

az webapp deployment github-actions add \
    --repo "TomMa59/myflymebot" \
    -g myflymebot \
    -n myflymebottmz202203 \
    -b main \
    --login-with-github

##### Maybe get profile of distribution?????
# az webapp deployment source config \
#       --branch main \
#       --name myflymebottmz202203 \
#       --repo-url https://github.com/TomMa59/myflymebot \
#       --resource-group myflymebot \
#       --repository-type github \
#       --github-action true
#az cognitiveservices account purge --location westeurope --resource-group myflymebot --name luis-authoring