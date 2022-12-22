import json
from zero import *
from pathlib import Path

if __name__ == '__main__':
    root = Path('./contracts/ABC.json').read_text()
    tfm = ILTFM()
    root = parse(json.loads(root), tfm)
    print(root)
    validate(root)