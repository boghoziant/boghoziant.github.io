PY := .venv/bin/python

build:            ## build published content into dist/
	$(PY) build.py

preview:          ## build with drafts and serve at http://localhost:8000
	$(PY) build.py --drafts
	$(PY) -m http.server 8000 -d dist

serve: build      ## build and serve at http://localhost:8000
	$(PY) -m http.server 8000 -d dist

setup:            ## create the venv and install dependencies
	python3 -m venv .venv
	$(PY) -m pip install -r requirements.txt

.PHONY: build preview serve setup
