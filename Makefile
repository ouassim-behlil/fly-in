PYTHON ?= python
UV ?= uv
MAP ?= map.txt

.PHONY: all install run debug clean lint lint-strict test help

all: install

install:
	$(UV) sync

run:
	$(UV) run python main.py $(MAP)

debug:
	$(UV) run python -m pdb main.py $(MAP)

clean:
	$(UV) run python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in [pathlib.Path('.mypy_cache'), pathlib.Path('.pytest_cache'), pathlib.Path('.ruff_cache'), pathlib.Path('build'), pathlib.Path('dist')]]; [p.unlink(missing_ok=True) for p in pathlib.Path('.').rglob('*.py[co]')]"
lint:
	$(UV) run flake8 .
	$(UV) run mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs .

lint-strict:
	$(UV) run flake8 .
	$(UV) run mypy --strict .

test:
	$(UV) run pytest -v

help:
	@echo Available Makefile targets:
	@echo   install      - Install project dependencies using uv
	@echo   run          - Execute the main simulation script (e.g. MAP=map.txt)
	@echo   debug        - Run main script in debug mode with pdb
	@echo   clean        - Remove temporary files and cache directories
	@echo   lint         - Run flake8 and mypy linting
	@echo   lint-strict  - Run flake8 and strict mypy type checking
	@echo   test         - Run test suite with pytest
