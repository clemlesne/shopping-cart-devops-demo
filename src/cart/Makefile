component_name := cart
docker := docker
env := dev
instance := none
project_name := shopping-cart-devops-demo
azdo_url := https://dev.azure.com/shopping-cart-devops-demo
dependencytrack_url := https://dependencytrack.shopping-cart-devops-demo.lesne.pro
dependencytrack_secret := none
tmp_path ?= $(realpath .)/tmp
version_small ?= $(shell $(MAKE) --directory ../../ --silent version)
version_full ?= $(shell $(MAKE) --directory ../../ --silent version-full)
container_name := $(project_name)/$(component_name):$(version_small)
helm_dest ?= $(tmp_path)/$(component_name)-$(version_small).tgz
sbom_dir := $(tmp_path)/sbom/

install:
	@python3 -m pip install --requirement ./requirements/default.txt
	@python3 -m pip install --requirement ./requirements/dev.txt
	@python3 -m pip freeze --local --requirement ./requirements/default.txt > ./requirements/prod.txt
	@curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b $(tmp_path) v0.75.0

dev:
	@APP_VERSION=$(version_full) uvicorn app.main:api \
		--header x-app-version:$(version_full) \
		--port 8081 \
		--reload \
		--timeout-keep-alive 30 \
		--no-server-header

test-local:
	@black ./app
	@helm lint --strict ./helm
	@semgrep ci --use-git-ignore --autofix --config auto

test-ci:
	@black --diff ./app
	@helm lint --strict ./helm
	@semgrep ci --use-git-ignore --no-autofix --config auto

	@mkdir -p $(sbom_dir)

	@python3 -m cyclonedx_py \
		--environment \
		--force \
		--format json \
		--purl-bom-ref \
		--output $(sbom_dir)/app.json

	@$(tmp_path)/syft $(container_name) \
		--output cyclonedx-json=$(sbom_dir)/container.json

	@az artifacts universal publish \
			--description "SBOM files" \
			--feed $(project_name) \
			--name $(component_name)-sbom \
			--organization $(azdo_url) \
			--path $(sbom_dir) \
			--version $(version_small) || \
		true

publish-tests:
	@test -f $(sbom_dir) || \
		mkdir -p $(sbom_dir) && \
		az artifacts universal download \
			--feed $(project_name) \
			--name $(component_name)-sbom \
			--organization $(azdo_url) \
			--path $(sbom_dir) \
			--version $(version_small)

	@curl --silent -X "POST" "$(dependencytrack_url)/api/v1/bom" \
			-H "Accept: application/json" \
			-H "Content-Type: multipart/form-data" \
			-H "X-API-Key: $(dependencytrack_secret)" \
			-F "autoCreate=true" \
			-F "bom=@$(sbom_dir)/app.json" \
			-F "projectName=$(project_name)-$(component_name)" \
			-F "projectVersion=$(env)-$(instance)" \
			--insecure

	@curl --silent -X "POST" "$(dependencytrack_url)/api/v1/bom" \
			-H "Accept: application/json" \
			-H "Content-Type: multipart/form-data" \
			-H "X-API-Key: $(dependencytrack_secret)" \
			-F "autoCreate=true" \
			-F "bom=@$(sbom_dir)/container.json" \
			-F "projectName=$(project_name)-$(component_name)" \
			-F "projectVersion=$(env)-$(instance)" \
			--insecure

build:
	@$(docker) build \
		--build-arg APP_VERSION=$(version_full) \
		--tag $(container_name) \
		.

	@helm package ./helm \
		--app-version $(version_small) \
		--destination $(dir $(helm_dest)) \
		--version $(version_small)

start:
	@$(docker) run \
		--name $(project_name)-$(component_name) \
		--replace \
		-d \
		-p 8081:8080 \
		$(container_name)

	echo "See http://localhost:8081"

logs:
	@$(docker) logs \
		--follow \
		$(project_name)-$(component_name)

stop:
	@$(docker) stop $(project_name)-$(component_name)

publish-builds:
	@$(docker) tag \
		$(container_name) \
		$(server)/$(component_name):$(version_small)

	@$(docker) push $(server)/$(component_name):$(version_small)

	@az artifacts universal publish \
			--description "Helm chart" \
			--feed $(project_name) \
			--name $(component_name)-helm \
			--organization $(azdo_url) \
			--path $(helm_dest) \
			--version $(version_small) || \
		true

deploy:
	@test -f $(helm_dest) || \
		az artifacts universal download \
			--feed $(project_name) \
			--name $(component_name)-helm \
			--organization $(azdo_url) \
			--path $(tmp_path) \
			--version $(version_small)

	@helm upgrade \
		--atomic \
		--install \
		--namespace $(env) \
		--timeout 10m \
		$(component_name)-$(instance) \
		$(helm_dest)

destroy:
	@helm uninstall \
		--namespace $(env) \
		--timeout 10m \
		$(project_name)-$(component_name)-$(instance)

test-remote:
	@$(docker) pull $(server)/cart:$(version_small)

	$(eval image_sha = $(shell $(docker) image inspect $(server)/cart:$(version_small) | jq -r '[.[].RepoDigests[] | select(. | startswith("$(server)")) | match("^.*(sha256.*)$$").captures[0].string] | "(\"" + join("\", \"") + "\")"'))

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
