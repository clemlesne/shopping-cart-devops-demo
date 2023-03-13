env := dev
instance := none
version_small ?= $(shell $(MAKE) --directory ../../ --silent version)
version_full ?= $(shell $(MAKE) --directory ../../ --silent version-full)
tmp_path := $(shell mktemp -d)
archive_path := $(shell echo "$(shell mktemp)$(shell echo ".zip")")
dest_path ?= $(shell echo "$(realpath .)$(shell echo "/dest")")
function_dest := $(shell echo "$(shell echo $(dest_path))$(shell echo "/function-$(version_small).zip")")

install:
	@pip install --requirement ./requirements/default.txt
	@pip install --requirement ./requirements/dev.txt
	@pip freeze --all --requirement ./requirements/default.txt > ./requirements/prod.txt

test-local:
	@black app

# TODO: Use "env" and "instance" variables to custom the deploy destination
deploy:
	@pip install \
		--target=".python_packages/lib/site-packages" \
		--requirement ./requirements/prod.txt \
		--platform manylinux_2_17_x86_64 \
		--only-binary=:all:

	@func azure functionapp publish shopping-cart-devops-demo-items --no-build --python

	@az functionapp config appsettings set \
		--name shopping-cart-devops-demo-items \
		--resource-group shopping-cart-devops-demo \
		--settings APP_VERSION=$(version_full)
