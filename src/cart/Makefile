component_name := cart
docker := docker
env := dev
instance := none
project_name := shopping-cart-devops-demo
azdo_url := https://dev.azure.com/shopping-cart-devops-demo
dependencytrack_url := https://dependencytrack.shopping-cart-devops-demo.lesne.pro
dependencytrack_secret := none
git_branch := $(shell git rev-parse --abbrev-ref HEAD | tr / -)
tmp_path ?= $(realpath .)/tmp
version_small ?= $(shell $(MAKE) --directory ../../ --silent version)
version_full ?= $(shell $(MAKE) --directory ../../ --silent version-full)
container_repo := localhost
container_name := $(container_repo)/$(project_name)/$(component_name)
helm_dest ?= $(tmp_path)/$(component_name)-$(version_small).tgz
sbom_dir := $(tmp_path)/sbom/

install:
	@python3 -m pip install --requirement requirements/default.txt
	@python3 -m pip install --requirement requirements/dev.txt
	@curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | bash -s -- -b $(tmp_path) v0.75.0

dev:
	@APP_VERSION=$(version_full) uvicorn app.main:api \
		--header x-app-version:$(version_full) \
		--port 8081 \
		--reload \
		--timeout-keep-alive 30 \
		--no-server-header

test:
	@black app
	@helm lint --strict helm
	@semgrep ci --use-git-ignore --autofix --config auto

build:
	@$(docker) build \
		--build-arg APP_VERSION=$(version_full) \
		--tag $(container_name):$(git_branch) \
		--cache-from $(container_name) \
		.

	@$(docker) tag \
		$(container_name):$(git_branch) \
		$(container_name):$(version_small)

start:
	@$(docker) run \
		--name $(project_name)-$(component_name) \
		--replace \
		-d \
		-p 8081:8080 \
		$(container_name):$(git_branch)

	echo "See http://localhost:8081"

logs:
	@$(docker) logs \
		--follow \
		$(project_name)-$(component_name)

stop:
	@$(docker) stop $(project_name)-$(component_name)

deploy:
	@helm upgrade \
		--atomic \
		--install \
		--namespace $(env) \
		--timeout 10m \
		$(component_name)-$(instance) \
		helm

test-remote:
	@$(docker) pull $(container_name):$(version_small)

	$(eval image_sha = $(shell $(docker) image inspect $(container_name):$(version_small) | jq -r '[.[].RepoDigests[] | select(. | startswith("$(container_repo)")) | match("^.*(sha256.*)$$").captures[0].string] | "(\"" + join("\", \"") + "\")"'))

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
