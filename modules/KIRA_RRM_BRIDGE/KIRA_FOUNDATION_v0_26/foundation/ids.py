"""Exact Python ports of the two original ID conventions. No silent migration."""
import hashlib
MASK=(1<<63)-1

def stable_id(namespace: str, symbol: str, scheme: str='forge') -> int:
    person={'forge':b'EQNXID44','runtime':b'EQXNUM01'}[scheme]
    payload=(namespace+'\0'+symbol).encode('utf-8')
    value=int.from_bytes(hashlib.blake2b(payload,digest_size=8,person=person).digest(),'big')&MASK
    return value or 1

def compare(namespace: str, symbol: str) -> dict:
    return {'namespace':namespace,'symbol':symbol,'runtime':stable_id(namespace,symbol,'runtime'),'forge':stable_id(namespace,symbol,'forge'),'equal':stable_id(namespace,symbol,'runtime')==stable_id(namespace,symbol,'forge')}
