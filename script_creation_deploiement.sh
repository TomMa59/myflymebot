#!/bin/bash

# Authentification
echo "Login and Authenticate..."
az login --output none
az account set \
    --subscription "OCR - Microsoft Azure" \
    --output none

ma_localisation=westeurope
echo "done"

# Resource group creation
echo "resource group creation..."
az group create \
     --location $ma_localisation \
     --name myflymebot \
     --output none
echo "done"

#Luis resources creation
echo "Luis authoring resource..."
az cognitiveservices account create \
      -n luis-authoring  \
      -g myflymebot \
      --kind LUIS.Authoring \
      --sku F0 \
      -l $ma_localisation \
      --yes \
     --output none
echo "done"

echo "Luis prediction resource..."
az cognitiveservices account create \
      -n luis-pred \
      -g myflymebot \
      --kind LUIS \
      --sku F0 \
      -l $ma_localisation \
      --yes \
     --output none
echo "done"

sleep 10

# Luis API authentication key
echo "LuisAuthKey export..."
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
echo "LuisAPPId export..."

# Addition of the prediction resource to the Luis app
echo "Addition of Luis prediction resource to Luis app..."
arm_access_token=$(az account get-access-token \
    --resource=https://management.core.windows.net/ \
    --query accessToken \
    --output tsv)

jq '."resourceGroup" = "myflymebot"' id.json > tmp.$$.json && mv tmp.$$.json id.json  
jq '."accountName" = "luis-pred"' id.json > tmp.$$.json && mv tmp.$$.json id.json  

luis set \
    --appId $LuisAPPId \
    --versionId 0.1 \
    --region $ma_localisation

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
echo "done"

# App service, Webapp and bot
# Registration
read -s -p 'Define your Microsoft App Passwords (please be careful to remember it) :' -r MicrosoftAppPassword
export MicrosoftAppPassword
echo "App registration..."
az ad app create \
     --display-name "myflymebottmz202203" \
     --password $MicrosoftAppPassword \
     --available-to-other-tenants \
     --output none
echo "done"
echo "MicrosoftAppId export..."
MicrosoftAppId=$(az ad app list --display-name myflymebottmz202203 | grep -o -P -- '"appId": "\K.{36}')
export MicrosoftAppId
echo "done"

# Service Plan
echo "App Service plan creation..."
az appservice plan create \
     -g myflymebot \
     -n flymebotserviceplan \
     --location $ma_localisation \
     --is-linux \
     --output none
echo "done"

# Web App
echo "web app creation..."
az webapp create \
     -g myflymebot \
     -p flymebotserviceplan \
     -n myflymebottmz202203 \
     --runtime "python:3.8" \
     --output none
echo "done"

# App insights
echo "App Insights creation..."
az monitor app-insights component create \
     --app luis-follow \
     --location $ma_localisation \
     --kind web \
     -g myflymebot \
     --application-type web \
     --output none
InstrumentationKey=$(az monitor app-insights component show --app luis-follow --resource-group myflymebot --query instrumentationKey -o tsv)
export InstrumentationKey
echo "done"

#API Id and key App insights
echo "App Insights API Key creation..."
AI_API_KEY=$(az monitor app-insights api-key create --api-key cle_bot \
                                        --app luis-follow \
                                        -g myflymebot \
                                        --read-properties ReadTelemetry \
                                        --query apiKey \
                                        -o tsv)
export AI_API_KEY

AI_APP_ID=$(az monitor app-insights component show --app luis-follow \
                                       --resource-group myflymebot \
                                       --query appId \
                                       -o tsv)
export AI_APP_ID
echo "done"

#Bot creation
echo "Bot creation..."
az bot create --appid $MicrosoftAppId \
                 --password $MicrosoftAppPassword \
                 --kind registration \
                 --name myflymebot \
                 --resource-group myflymebot \
                 --endpoint "https://myflymebottmz202203.azurewebsites.net/api/messages" \
                 --output none
echo "done"

#Link between bot and app insights
echo "Bot telemetry settings update..."
az bot update -n myflymebot \
               -g myflymebot \
               --ai-key $InstrumentationKey \
               --ai-app-id $AI_APP_ID \
               --ai-api-key $AI_API_KEY \
               --output none
echo "done"

#Deployment
# Web App config
echo "Web app settings update..."
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
                  SCM_DO_BUILD_DURING_DEPLOYMENT=true \
      --output none

az webapp config set \
     -n myflymebottmz202203 \
     -g myflymebot \
     --startup-file="python3.8 -m aiohttp.web -H 0.0.0.0 -P 8000 app:init_func" \
     --output none
echo "done"

# secrets definition to git hub secrets - used for unit tests during
echo "git hub secrets definition..."
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

echo "get git hub access token..."
read -s -p 'Please enter your github access token: ' -r github_access_token
export github_access_token

# git hub actions defined
echo "git hub actions definition..."
az webapp deployment github-actions add \
      --repo "TomMa59/myflymebot" \
      -g myflymebot \
      -n myflymebottmz202203 \
      -b main \
      --token $github_access_token

sleep 5

# Update publishing profile
echo "Publish profile update..."
gh secret set AZURE_WEBAPP_PUBLISH_PROFILE \
       --body "$(az webapp deployment list-publishing-profiles \
       --name myflymebottmz202203 \
       --resource-group myflymebot \
       --xml)" \
       --repo "TomMa59/myflymebot"

echo "All good, you can now push on git to update the Bot."