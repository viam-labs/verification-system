module.tar.gz: meta.json requirements.txt *.sh src/*.py
	tar czf module.tar.gz $^
