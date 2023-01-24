docker := docker
version_small ?= $(shell $(MAKE) --directory ../../ --silent version)
version_full ?= $(shell $(MAKE) --directory ../../ --silent version-full)
dest_path ?= $(shell echo "$(realpath .)$(shell echo "/dest")")
helm_dest ?= $(shell echo "$(shell echo $(dest_path))$(shell echo "/cart-$(version_small).tgz")")

install:
	@pip install --requirement ./requirements/default.txt
	@pip install --requirement ./requirements/dev.txt
	@pip freeze --all --requirement ./requirements/default.txt > ./requirements/prod.txt

dev:
	@APP_VERSION=$(version_full) uvicorn app.main:api \
		--header x-app-version:$(version_full) \
		--port 8081 \
		--reload \
		--timeout-keep-alive 30 \
		--no-server-header \
		--proxy-headers

test-dev:
	@black ./app
	@helm lint ./helm

build:
	@$(docker) build \
		--build-arg APP_VERSION=$(version_full) \
		--cache-from shopping-cart-devops-demo/cart \
		--tag shopping-cart-devops-demo/cart:$(version_small) \
		.

	@helm package ./helm \
		--app-version $(version_small) \
		--destination ./dest \
		--version $(version_small)

run-build:
	@$(docker) run \
		--name shopping-cart-devops-demo-cart \
		--replace \
		-d \
		-p 8081:8080 \
		shopping-cart-devops-demo/cart:$(version_small)

stop-build:
	@$(docker) stop shopping-cart-devops-demo-cart

publish-build:
	@$(docker) tag \
		shopping-cart-devops-demo/cart:$(version_small) \
		$(server)/cart:$(version_small)

	@$(docker) push $(server)/cart:$(version_small)

	@az artifacts universal publish \
		--description "Helm chart" \
		--feed shopping-cart-devops-demo \
		--name cart-helm \
		--organization https://dev.azure.com/shopping-cart-devops-demo \
		--path $(helm_dest) \
		--version $(version_small)

deploy-build:
	@test -f $(helm_dest) \
		|| az artifacts universal download \
			--feed shopping-cart-devops-demo \
			--name cart-helm \
			--organization https://dev.azure.com/shopping-cart-devops-demo \
			--path $(dest_path) \
			--version $(version_small)

	@helm upgrade \
		--atomic \
		--install \
		--namespace $(namespace) \
		--timeout 10m \
		shopping-cart-devops-demo-cart \
		$(helm_dest)

test-build:
	$(eval image_sha = $(shell $(docker) images --no-trunc --quiet shopping-cart-devops-demo/cart:$(version_small)))

	$(eval graph_query_cve = securityresources | where type =~ "microsoft.security/assessments/subassessments" | extend assessmentKey=extract(@"(?i)providers/Microsoft.Security/assessments/([^/]*)", 1, id), repositoryName=tostring(properties.additionalData.repositoryName), imageSha=tostring(properties.additionalData.imageDigest), status=tostring(properties.status.code), severity=tostring(properties.status.severity), issueName=tostring(properties.displayName), issueImpact=tostring(properties.impact), issueRemediation=tostring(properties.remediation) | where assessmentKey == "dbd0cb49-b563-45e7-9724-889e799fa648" and status == "Unhealthy" and repositoryName == "cart" and imageSha == "$(image_sha)" | project severity, issueName, issueImpact, issueRemediation)

	@az graph query \
		--graph-query '$(graph_query_cve)' \
		--output table \
		--query 'data[]'

	@if [ $(shell az graph query --graph-query '$(graph_query_cve)' --query 'data[]' | jq length) -gt 0 ]; then \
		echo "Findings deteched, please fix them." \
		&& exit 1; \
	else \
		echo "No issues detected." \
		&& exit 0; \
	fi;
