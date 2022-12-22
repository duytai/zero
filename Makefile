PYTHON=venv/bin/python3
ENTRY=main.py

all: compile run

compile:
	cd contracts/ && solc --ast-compact-json ABC.sol | tail -n +5 > ABC.json

run:
	$(PYTHON) $(ENTRY)