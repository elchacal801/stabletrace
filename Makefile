.PHONY: setup ingest api app test clean

setup:
	pip install -e .[dev]

ingest:
	python -m ingest.run_ingest

api:
	uvicorn api.main:app --reload

app:
	cd app && npm run dev

test:
	pytest tests/

clean:
	rm -rf __pycache__ .pytest_cache
	
format:
	ruff format .
	ruff check . --fix
