.PHONY: test

test:
	nosetests --rednose -v -s --with-coverage --cover-package=zwave --cover-inclusive --cover-html
