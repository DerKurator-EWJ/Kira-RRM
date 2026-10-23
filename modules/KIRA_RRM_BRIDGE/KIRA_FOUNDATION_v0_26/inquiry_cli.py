from pathlib import Path
from foundation.inquiry_queue import InquiryQueue
from foundation.epistemic_regulation import EpistemicCore

Path('data').mkdir(exist_ok=True)
q=InquiryQueue('data/inquiry_queue.sqlite',budget=3)
e=EpistemicCore('data/inquiry_epistemic.sqlite')
try:
    qid=q.propose('A','Warum folgt auf A ein bestimmtes Ereignis?',relevance=2,uncertainty=.8,gain=3,cost=2)
    q.propose('B','Welche Relation bleibt stabil?',relevance=1,uncertainty=.5,gain=1,cost=1)
    print('Open:',q.list('open'))
    print('Selected:',q.investigate())
    for outcome in ['X']*5+['Y']*14:
        result=e.observe('A',outcome)
        if result['action']=='revise':
            print('Revision:',result['model'])
            print('Reopened questions:',q.reopen_on_revision('A'))
    print('Queue:',q.list())
    print('Events:',q.events(qid))
finally:
    q.close();e.close()
