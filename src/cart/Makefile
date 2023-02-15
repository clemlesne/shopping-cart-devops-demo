env := dev
instance := none
docker := docker
version_small ?= $(shell $(MAKE) --directory ../../ --silent version)
version_full ?= $(shell $(MAKE) --directory ../../ --silent version-full)
dest_path ?= $(shell echo "$(realpath .)$(shell echo "/dest")")
helm_dest ?= $(shell echo "$(shell echo $(dest_path))$(shell echo "/cart-$(version_small).tgz")")

install:
	@pip install --requirement ./requirements/default.txt
	@pip install --requirement ./requirements/dev.txt

dev:
	@APP_VERSION=$(version_full) uvicorn app.main:api \
		--header x-app-version:$(version_full) \
		--port 8081 \
		--reload \
		--timeout-keep-alive 30 \
		--no-server-header \
		--proxy-headers

test-local:
	@black ./app
	@helm lint --strict ./helm
	@semgrep ci --use-git-ignore --autofix --config auto

test-ci:
	@black --diff ./app
	@helm lint --strict ./helm
	@semgrep ci --use-git-ignore --no-autofix --config auto

build:
	@$(docker) build \
		--build-arg APP_VERSION=$(version_full) \
		--tag shopping-cart-devops-demo/cart:$(version_small) \
		.

	@helm package ./helm \
		--app-version $(version_small) \
		--destination ./dest \
		--version $(version_small)

start:
	@$(docker) run \
		--name shopping-cart-devops-demo-cart \
		--replace \
		-d \
		-p 8081:8080 \
		shopping-cart-devops-demo/cart:$(version_small)

stop:
	@$(docker) stop shopping-cart-devops-demo-cart

publish:
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
			--version $(version_small) \
		|| true

deploy:
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
		--namespace $(env) \
		--timeout 10m \
		cart-$(instance) \
		$(helm_dest)

destroy:
	@helm uninstall \
		--namespace $(env) \
		--timeout 10m \
		shopping-cart-devops-demo-cart-$(instance)

test-remote:
	@$(docker) pull $(server)/cart:$(version_small)

	$(eval image_sha = $(shell $(docker) image inspect $(server)/cart:$(version_small) | jq --raw-output '[.[].RepoDigests[] | select(. | startswith("$(server)")) | match("^.*(sha256.*)$$").captures[0].string] | "(\"" + join("\", \"") + "\")"'))

	@echo "Testing container $(image_sha)"

	$(eval graph_query_cve = securityresources | where type == "microsoft.security/assessments/subassessments" and id has "providers/Microsoft.Security/assessments" and isnotnull (properties.id) and properties.additionalData.imageDigest in $(image_sha) | project Severity=properties.status.severity, ID=strcat_array(split(properties.additionalData.cve.link, "=", 1),""), Patchable=properties.additionalData.patchable, Issue=properties.displayName, Remediation=properties.remediation, CVE=properties.additionalData.cve.link, Vendor=properties.additionalData.vendorReferences.link)

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
