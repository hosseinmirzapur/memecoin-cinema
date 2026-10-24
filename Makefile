PY ?= python3
PORT ?= 8765

.DEFAULT_GOAL := help
.PHONY: help ui ui-build assets test check config

help:
	@echo "make ui       build the React app, then start the desk at http://127.0.0.1:$(PORT)"
	@echo "make ui-build build the React app only (installs npm deps on first run)"
	@echo "make assets   rebuild the Blender relic models in ui/public/models (needs blender on PATH)"
	@echo "make test     run unit tests"
	@echo "make check    compile scripts, then run tests"
	@echo "make config   show gmgn-cli config check"

ui/node_modules: ui/package.json
	cd ui && npm install --no-audit --no-fund
	@touch ui/node_modules

ui-build: ui/node_modules
	cd ui && npm run build

assets:
	blender -b --factory-startup -P scripts/blender/build_quest_assets.py -- ui/public/models

ui: ui-build
	$(PY) scripts/ui_server.py --port $(PORT)

test:
	$(PY) -m unittest discover -s tests -v

check:
	$(PY) -m py_compile scripts/*.py .agents/skills/gmgn-holder-analysis/analyze.py
	$(MAKE) test

config:
	gmgn-cli config --check
