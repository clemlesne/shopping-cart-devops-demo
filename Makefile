version:
	$(shell echo bash ./cicd/version.sh -c)

version-full:
	$(shell echo bash ./cicd/version.sh -c -m)
