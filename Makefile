docs:
	@sphinx-apidoc --force -o docs/api restlib2
	@make -C docs -f Makefile html

.PHONY: docs
