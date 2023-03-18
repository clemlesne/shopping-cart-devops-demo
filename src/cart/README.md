# Cart service

After being deployed with Azure DevOps Pipelines, [the service is available here](https://shopping-cart-devops-demo.lesne.pro/cart-develop). [OpenAPI schema can be accessed here](https://shopping-cart-devops-demo.lesne.pro/cart/openapi.json).

Includes:

- [x] Authenticates to Azure services [with Azure AD Pod Identity](https://learn.microsoft.com/en-us/azure/aks/use-azure-ad-pod-identity)
- [x] Automated build & deploy with Azure DevOps Pipelines and Azure DevOps Artifacts
- [x] Azure Application Insights with [opencensus-python](https://github.com/census-instrumentation/opencensus-python)

## Dev

Prerequisites:

```bash
# Install dependencies
make install

APPLICATIONINSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
        --app shopping-cart-devops-demo \
        --resource-group shopping-cart-devops-demo \
    | jq -r ".connectionString")
```

Start the local app, `make dev`. Test your code, `make test-local`. By default, port is 8081. See OpenAPI doc at [127.0.0.1:8081/redoc](http://127.0.0.1:8081/redoc).

Note, OpenAPI documentation can be accessed here:

- JSON schema: http://localhost:8081/openapi.json
- Interface: http://localhost:8081/redoc

## Build

This will includes both the container and the Helm chart. The deployment procedure is container based, `make build`.

## Run

Run the container in local, `make start`.

## Publish

Prerequisites:

```bash
# Login to Azure Container Registry
DOCKER_TOKEN=$(az acr login --expose-token --name shoppingcartdevopsdemo)
DOCKER_PASS=$(echo $DOCKER_TOKEN | jq -r '.accessToken')
LOGIN_SERVER=$(echo $DOCKER_TOKEN | jq -r '.loginServer')

docker login $LOGIN_SERVER \
    -p $DOCKER_PASS \
    -u 00000000-0000-0000-0000-000000000000
```

This will includes both the container and the Helm chart. Publish the current build, `make server=$LOGIN_SERVER publish`.

## Deploy

Prerequisites:

```bash
# Connect to Azure Kubernetes Service
az aks get-credentials \
    --name shoppingcartdevopsdemo \
    --resource-group shopping-cart-devops-demo

kubelogin convert-kubeconfig -l azurecli

# Create your Kubernetes namespace
NAMESPACE=dev
kubectl create ns $NAMESPACE

# Create the Cosmos DB database
az cosmosdb create \
    --locations regionName=westeurope \
    --name shopping-cart-devops-demo \
    --resource-group shopping-cart-devops-demo

COSMOS_DB_URI=$(az cosmosdb show \
        --name shopping-cart-devops-demo \
        --resource-group shopping-cart-devops-demo \
    | jq -r ".documentEndpoint")

# Create the container to store data into
az cosmosdb sql container create \
    --account-name shopping-cart-devops-demo \
    --database-name shopping-cart-devops-demo \
    --name cart \
    --partition-key-path "/id" \
    --resource-group shopping-cart-devops-demo

# Allow the ap to access the database
az cosmosdb sql role assignment create \
    --account-name shopping-cart-devops-demo \
    --resource-group shopping-cart-devops-demo \
    --role-definition-name "Cosmos DB Built-in Data Contributor" \
    --scope "/" \
    --principal-id 2dbbd1fa-417f-48ab-aba2-d54057938b75

# Create the Redis database (cache database)
az redis create \
    --location westeurope \
    --name shopping-cart-devops-demo \
    --resource-group shopping-cart-devops-demo \
    --sku Basic \
    --vm-size c0
```

Deploy the application, `make env=$NAMESPACE deploy`.
