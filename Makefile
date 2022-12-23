PYTHON=venv/bin/python3
ENTRY=main.py

all: compile run

compile:
	cd contracts/ && solc --ast-compact-json DEF.sol | tail -n +5 > DEF.json

run:
	$(PYTHON) $(ENTRY)