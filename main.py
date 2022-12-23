import json
from zero import *
from pathlib import Path

if __name__ == '__main__':
    root = Path('./contracts/DEF.json').read_text()
    root = parse(json.loads(root))
    validate(root)