# Note: makefile updates first need a 'docker compose build' before the
# makefile gets updated in the docker image...

SHELL=/bin/bash -o pipefail


message:
	@echo "make install: install everything"
	@echo "make clean: remove .venv and staticfiles"
	@echo "make test: run the tests"
	@echo "make beautiful: flake8, black, isort"
	@echo "make upgrade: call pip-compile with --upgrade"


install: bin/pip-compile bin/.installed directories staticfiles/.installed


clean:
	rm -rf .venv staticfiles/ bin/ lib/ share/ pyvenv.cfg bower_components/ node_modules/


# A virtualenv creates bin/activate
bin/activate:
	python3 -m venv .


# Without pip-compile we first need to do the one-time installation.
bin/pip-compile: bin/activate
	bin/pip install --upgrade pip setuptools wheel pip-tools


requirements/requirements.txt: requirements/requirements.in setup.py
	bin/pip-compile --output-file=requirements/requirements.txt requirements/requirements.in


upgrade:
	bin/pip-compile --upgrade \
	    --output-file=requirements/requirements.txt requirements/requirements.in
	@echo "Don't forget to run 'make install' now"


bin/.installed: requirements/requirements.txt
	bin/pip-sync requirements/requirements.txt
	touch $@

# Note: no var/static anymore.
directories: var/media var/log var/db var/cache var/plugins


var/%:
	mkdir -p var/$*


staticfiles/.installed: bower_components
	bin/python manage.py collectstatic --noinput
	touch $@


bower_components: bower.json node_modules/bower/bin/bower
	node_modules/bower/bin/bower --allow-root install


node_modules/bower/bin/bower:
	npm install bower


test: install
	bin/pytest | tee trs/pytest-coverage.txt


beautiful:
	bin/isort trs
	bin/black trs
