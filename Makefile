# Note: makefile updates first need a 'make install' before the makefile gets
# updated in the docker image...

message:
	@echo "make install: install everything"
	@echo "make clean: remove .venv and staticfiles"
	@echo "make test: run the tests"
	@echo "make beautiful: flake8, black, isort"


install: bin/pip-compile bin/.installed directories staticfiles/.installed


clean:
	rm -rf .venv var/static bin/ lib/ share/ pyvenv.cfg


# A virtualenv creates bin/activate
bin/activate:
	python3 -m venv .


# Without pip-compile we first need to do the one-time installation.
bin/pip-compile: bin/activate
	bin/pip install --upgrade pip setuptools wheel pip-tools


requirements/requirements.txt: requirements/requirements.in setup.py
	bin/pip-compile --output-file=requirements/requirements.txt requirements/requirements.in


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


bower_components: bower.json
	node_modules/bower/bin/bower --allow-root install


test: install
	bin/flake8 trs
	bin/python manage.py test
	# bin/pytest | tee pytest-coverage.txt


beautiful:
	bin/isort trs
	bin/black trs
