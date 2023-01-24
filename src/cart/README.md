# Cart service

After being deployed with Azure DevOps Pipelines, [the service is available here](https://shopping-cart-devops-demo.westeurope.cloudapp.azure.com/cart). [OpenAPI schema can be accessed here](https://shopping-cart-devops-demo.westeurope.cloudapp.azure.com/cart/openapi.json).

Includes:

- [x] Authenticates to Azure services [with Azure AD Pod Identity](https://learn.microsoft.com/en-us/azure/aks/use-azure-ad-pod-identity)
- [x] Automated build & deploy with Azure DevOps Pipelines and Azure DevOps Artifacts
- [x] Azure Application Insights with [opencensus-python](https://github.com/census-instrumentation/opencensus-python)

## Dev

Prerequisites:

```bash
# Install dependencies
make install
```

Start the local app, `make dev`. Test your code, `make test-dev`. By default, port is 8081. See OpenAPI doc at [127.0.0.1:8081/redoc](http://127.0.0.1:8081/redoc).

Note, OpenAPI documentation can be accessed here:

- JSON schema: http://localhost:8081/openapi.json
- Interface: http://localhost:8081/redoc

## Build

This will includes both the container and the Helm chart. The deployment procedure is container based, `make build`.

## Run

Run the container in local, `make run-build`.

## Publish

Prerequisites:

```bash
# Login to Azure Container Registry
DOCKER_TOKEN=$(az acr login --expose-token --name shoppingcartdevopsdemo)
LOGIN_SERVER=$(echo $DOCKER_TOKEN | jq -r '.loginServer')

docker login $LOGIN_SERVER \
    -p $(echo $DOCKER_TOKEN | jq -r '.accessToken') \
    -u 00000000-0000-0000-0000-000000000000
```

This will includes both the container and the Helm chart. Publish the current build, `make server=$LOGIN_SERVER publish-build`.

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
```

Deploy the application, `make namespace=$NAMESPACE deploy-build`.
