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
	rm -rf .venv staticfiles/ pyvenv.cfg node_modules/ src/trs/static/trs/trs.css

run_uv:
	uv sync

upgrade:
	uv sync --upgrade
	pre-commit autoupdate


# Note: no var/static anymore.
directories: var/media var/log var/db var/cache var/plugins


var/%:
	mkdir -p var/$*


src/trs/static/trs/trs.css: node_modules/.bin/tailwindcss tailwind-input.css src/trs/templates/trs/*.html
	node_modules/.bin/tailwindcss -i tailwind-input.css -o src/trs/static/trs/trs.css


staticfiles/.installed: src/trs/static/trs/trs.css
	uv run manage.py collectstatic --noinput
	touch $@


node_modules/.bin/tailwindcss: package.json
	npm install .


test: install
	PYTHONWARNINGS=always uv run pytest | tee pytest-coverage.txt


beautiful:
	pre-commit run --all
