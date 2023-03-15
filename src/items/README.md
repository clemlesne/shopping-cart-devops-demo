# Cart service

Includes:

- [ ] Authenticates to Azure services [with Azure AD Pod Identity](https://learn.microsoft.com/en-us/azure/aks/use-azure-ad-pod-identity)
- [ ] Automated build & deploy with Azure DevOps Pipelines and Azure DevOps Artifacts
- [ ] Azure Application Insights with [opencensus-python](https://github.com/census-instrumentation/opencensus-python)

## Dev

Prerequisites:

- Install dependencies, `make install`

Start the local app, `make dev`. Test your code, `make test-local`. By default, port is 8081. See OpenAPI doc at [127.0.0.1:8082/redoc](http://127.0.0.1:8082/redoc).

Note, OpenAPI documentation can be accessed here:

- JSON schema: http://localhost:8082/openapi.json
- Interface: http://localhost:8082/redoc

## Deploy

Prerequisites:

```bash
FUNCTION_IDENTITY=/subscriptions/823cb2a9-1bf9-4063-a05a-39e3eba43024/resourceGroups/shopping-cart-devops-demo/providers/Microsoft.ManagedIdentity/userAssignedIdentities/shopping-cart-devops-demo

# Create an Azure Storage Blob resource
az storage account create \
    --location westeurope \
    --name shppngcrtdvpsdmfnc \
    --resource-group shopping-cart-devops-demo \
    --sku Standard_LRS

# Create your Azure Functions resource
# See: https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python?tabs=azure-cli%2Cbash&pivots=python-mode-decorators#create-supporting-azure-resources-for-your-function
az functionapp create \
    --app-insights shopping-cart-devops-demo \
    --assign-identity $FUNCTION_IDENTITY \
    --consumption-plan-location westeurope \
    --functions-version 4 \
    --name shopping-cart-devops-demo-items \
    --os-type linux \
    --resource-group shopping-cart-devops-demo \
    --runtime python \
    --runtime-version 3.10 \
    --storage-account shppngcrtdvpsdmfnc

# Disable built-in logging
# See: https://learn.microsoft.com/en-us/azure/azure-functions/configure-monitoring?tabs=v2#disable-built-in-logging
az functionapp config appsettings delete \
    --name shopping-cart-devops-demo-items \
    --resource-group shopping-cart-devops-demo \
    --setting-names AzureWebJobsDashboard

# Retreive the Application Insights connection stirng
APPLICATIONINSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
        --app shopping-cart-devops-demo \
        --resource-group shopping-cart-devops-demo \
    | jq -r ".connectionString")

# Enable Azure Application Insights in the App Functions (APPLICATIONINSIGHTS_CONNECTION_STRING) and enable Python v2 model (AzureWebJobsFeatureFlags)
# See: https://learn.microsoft.com/en-us/azure/azure-monitor/app/sdk-connection-string?tabs=net#environment-variable
# See: https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python?pivots=python-mode-decorators&tabs=azure-cli%2Cbash
az functionapp config appsettings set \
    --name shopping-cart-devops-demo-items \
    --resource-group shopping-cart-devops-demo \
    --settings APPLICATIONINSIGHTS_CONNECTION_STRING=$APPLICATIONINSIGHTS_CONNECTION_STRING AzureWebJobsFeatureFlags=EnableWorkerIndexing
```

Deploy the application, `make deploy`.
