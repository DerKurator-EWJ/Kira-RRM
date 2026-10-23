"""Run python benchmark.py; fair end-to-end prototype comparison (not optimized native runtime)."""
import json,sqlite3,time,tempfile,os
from runtime import BinaryRuntime
from rrm05 import Kernel

def state(i):
    return {'nodes':{'a':'point','b':'point','c':'signal'},'edges':[['a',('near','far')[i%2],'b'],['c',('red','blue')[(i//20)%2],'a']]}

def run(n=1000):
    with tempfile.TemporaryDirectory() as d:
        rows=[]
        for label,cls in [('json',Kernel),('hybrid',BinaryRuntime)]:
            path=os.path.join(d,label+'.sqlite'); k=cls(path)
            t=time.perf_counter()
            for i in range(n): k.observe('x',state(i))
            write=time.perf_counter()-t
            t=time.perf_counter()
            for i in range(100): k.predict('x',state(i),focus=0)
            read=time.perf_counter()-t
            k.close(); size=os.stat(path).st_size
            rows.append((label,size,write,read))
        for label,size,write,read in rows:
            print(f'{label:8} db_bytes={size:8} observe_s={write:.4f} predict_100_s={read:.4f}')
        print('Results depend on Python, SQLite, input shape, and machine; no general speed claim.')
if __name__=='__main__':run()
