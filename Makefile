PYTHONPATH := ./verification-system:$(PYTHONPATH)

module.tar.gz: requirements.txt *.sh src/*.py
	tar czf module.tar.gz $^

test:
	PYTHONPATH=$(PYTHONPATH) pytest
