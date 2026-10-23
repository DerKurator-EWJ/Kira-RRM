"""Deutsche Projektbegriffe und technische englische Schreibweisen.

Nur Benennungen und dokumentierte Begriffe; kein Übersetzer für Python-Syntax.
"""
import json
from pathlib import Path

DATEI=Path(__file__).resolve().parent.parent/'begriffe.json'

def begriffe():
    return json.loads(DATEI.read_text(encoding='utf-8'))['terms']

def technisch(deutscher_begriff):
    return begriffe()[deutscher_begriff]['code']

def deutsch(technischer_begriff):
    treffer=[name for name,info in begriffe().items() if info['code']==technischer_begriff]
    if not treffer: raise KeyError(technischer_begriff)
    return treffer[0]
