version_small ?= $(shell $(MAKE) --directory ../../ --silent version)
version_full ?= $(shell $(MAKE) --directory ../../ --silent version-full)
tmp_path := $(shell mktemp -d)
archive_path := $(shell echo "$(shell mktemp)$(shell echo ".zip")")
dest_path ?= $(shell echo "$(realpath .)$(shell echo "/dest")")
function_dest := $(shell echo "$(shell echo $(dest_path))$(shell echo "/function-$(version_small).zip")")

install:
	@pip install --requirement ./requirements/default.txt
	@pip install --requirement ./requirements/dev.txt
	@pip freeze --all --requirement ./requirements/default.txt > ./requirements.txt

dev:
	@echo "Not yet implemented (sorry)"

test-local:
	@black app

deploy:
	@func azure functionapp publish shopping-cart-devops-demo-items --build remote

	@az functionapp config appsettings set \
		--name shopping-cart-devops-demo-items \
		--resource-group shopping-cart-devops-demo \
		--settings APP_VERSION=$(version_full)

watch-build:
	@az webapp log tail \
		--name shopping-cart-devops-demo-items \
		--resource-group shopping-cart-devops-demo
