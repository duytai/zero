PYTHON=venv/bin/python3
ENTRY=main.py

all: compile run

compile:
	cd contracts/ && solc --ast-compact-json THY.sol | tail -n +5 > THY.json

run:
	$(PYTHON) $(ENTRY)