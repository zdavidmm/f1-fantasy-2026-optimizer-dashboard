.PHONY: setup run serve test

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

run:
	. .venv/bin/activate && python -m src.cli run --mode all && python -m src.cli build-site

serve:
	python3 -m http.server 8000 --directory dist

test:
	. .venv/bin/activate && pytest -q
