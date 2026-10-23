from foundation.epistemic_regulation import EpistemicCore
from pathlib import Path
Path("data").mkdir(exist_ok=True)
core = EpistemicCore("data/epistemic.sqlite", budget=100)
for i, outcome in enumerate(["B"]*6+["C"]*10,1):
    event=core.observe("A",outcome)
    print(f"{i:02d} A -> {outcome} | {event['action']:<16} | {event['state']:<12} | model={event['model']}")
print("Revision history:",core.history("A"))
core.close()
