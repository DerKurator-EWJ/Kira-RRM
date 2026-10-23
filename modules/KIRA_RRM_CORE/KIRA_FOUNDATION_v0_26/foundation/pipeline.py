"""v0.6: audio -> persistent ID stream -> online macros -> lossless ID compression.
No claims of lossless audio or autonomous cognition.
"""
from pathlib import Path
from .audio import AdaptiveAudio
from .compression import ResearchState
from .macros import OnlineMacroLearner, HierarchicalRouteIndex

class AudioPipeline:
    def __init__(self, db_path, codebook_path, stream='audio:default', frame_size=1024):
        if not stream.startswith('audio:') or not stream[6:]:
            raise ValueError('stream must be audio:<nonempty name>')
        if frame_size <= 0:
            raise ValueError('frame_size must be positive')
        self.stream=stream
        self.frame_size=frame_size
        self.codebook_path=Path(codebook_path)
        self.quantizer=AdaptiveAudio.load(self.codebook_path)
        self.store=ResearchState(db_path)
        self.new_ids=[]

    def ingest(self, frames):
        created=0
        for frame in frames:
            if len(frame)!=self.frame_size:
                raise ValueError('incorrect frame size')
            result=self.quantizer.quantize(frame)
            self.store.observe(result['id'],self.stream)
            self.new_ids.append(result['id'])
            created+=int(result['created'])
        self.quantizer.save(self.codebook_path)
        return {'frames_ingested':len(self.new_ids),'new_prototypes':created,
                'total_events':len(self.store.events(self.stream)),
                'total_prototypes':len(self.quantizer.prototypes)}

    def analyze(self, min_occurrences=3, max_width=6, max_levels=3):
        ids=self.store.events(self.stream)
        learner=OnlineMacroLearner(min_size=2,max_size=max_width,min_occurrences=min_occurrences)
        for token in ids:
            learner.observe(token,modality=self.stream)
        candidates=learner.candidates(modality=self.stream)
        index=HierarchicalRouteIndex()
        for candidate in candidates:
            index.register(candidate,modality=self.stream)
        probe,checks=index.probe(ids,modality=self.stream)
        metrics=self.store.consolidate(self.stream,min_occurrences=min_occurrences,
                                       max_width=max_width,max_levels=max_levels)
        if self.store.restore(self.stream)!=ids:
            raise AssertionError('ID stream reconstruction failed')
        return {'stream':self.stream,'events':len(ids),'unique_ids':len(set(ids)),
                'online_macro_candidates':len(candidates),
                'route_probe':probe,'route_checks':checks,
                'compression':metrics,'id_roundtrip_ok':True}

    def close(self):
        self.store.close()
