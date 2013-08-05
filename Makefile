docs:
	@sphinx-apidoc --force -o docs/api restlib2
	@make -C docs html

.PHONY: docs
