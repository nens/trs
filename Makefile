# Note: makefile updates first need a 'docker compose build' before the
# makefile gets updated in the docker image...

SHELL=/bin/bash -o pipefail


message:
	@echo "make install: install everything"
	@echo "make clean: remove .venv and staticfiles"
	@echo "make test: run the tests"
	@echo "make beautiful: flake8, black, isort"
	@echo "make upgrade: run 'uv sync' with --upgrade"


install: run_uv directories staticfiles/.installed


clean:
	rm -rf .venv staticfiles/ bin/ lib/ share/ pyvenv.cfg bower_components/ node_modules/

run_uv:
	uv sync

upgrade:
	uv sync --upgrade


# Note: no var/static anymore.
directories: var/media var/log var/db var/cache var/plugins


var/%:
	mkdir -p var/$*


staticfiles/.installed: bower_components
	uv run manage.py collectstatic --noinput
	touch $@


bower_components: bower.json node_modules/bower/bin/bower
	node_modules/bower/bin/bower --allow-root install


node_modules/bower/bin/bower:
	npm install bower


test: install
	uv run pytest | tee trs/pytest-coverage.txt


beautiful:
	pre-commit run --all
