#AUTOGENERATED! DO NOT EDIT! File to edit: dev/04_dataloader.ipynb (unless otherwise specified).

__all__ = ['fa_collate', 'fa_convert', 'DataLoader']

#Cell
from ..torch_basics import *
from ..test import *

from torch.utils.data.dataloader import _MultiProcessingDataLoaderIter,_SingleProcessDataLoaderIter,_DatasetKind
_loaders = (_MultiProcessingDataLoaderIter,_SingleProcessDataLoaderIter)

#Cell
def _wif(worker_id):
    info = get_worker_info()
    ds = info.dataset.d
    ds.nw,ds.offs = info.num_workers,info.id
    set_seed(info.seed)
    ds.wif()

class _FakeLoader(GetAttr):
    _auto_collation,collate_fn,drop_last,dataset_kind,_dataset_kind,_index_sampler = False,noops,False,_DatasetKind.Iterable,_DatasetKind.Iterable,Inf.count
    def __init__(self, d, pin_memory, num_workers, timeout):
        self.dataset,self.default,self.worker_init_fn = self,d,_wif
        store_attr(self, 'd,pin_memory,num_workers,timeout')

    def __iter__(self): return iter(self.d.create_batches(self.d.sample()))

    @property
    def multiprocessing_context(self): return (None,multiprocessing)[self.num_workers>0]

    @contextmanager
    def no_multiproc(self):
        old_nw = self.num_workers
        try:
            self.num_workers = 0
            yield self.d
        finally: self.num_workers = old_nw

_collate_types = (ndarray, Tensor, typing.Mapping, str)

#Cell
def fa_collate(t):
    b = t[0]
    return (default_collate(t) if isinstance(b, _collate_types)
            else type(t[0])([fa_collate(s) for s in zip(*t)]) if isinstance(b, Sequence)
            else default_collate(t))

#Cell
def fa_convert(t):
    return (default_convert(t) if isinstance(t, _collate_types)
            else type(t)([fa_convert(s) for s in t]) if isinstance(t, Sequence)
            else default_convert(t))

#Cell
@funcs_kwargs
@delegates(Sampler)
class DataLoader(GetAttr):
    wif=before_iter=after_item=before_batch=after_batch=after_iter = noops
    _methods = 'wif before_iter create_batches create_item after_item before_batch create_batch retain after_batch after_iter'.split()
    _default,_sampler = 'dataset',Sampler
    def __init__(self, dataset=None, bs=None, num_workers=0, pin_memory=False, timeout=0,
                 shuffle=False, drop_last=False, indexed=None, n=None, **kwargs):
        assert not (bs is None and drop_last)
        if indexed is None: indexed = dataset is not None and hasattr(dataset,'__getitem__')
        if n is None:
            try: n = len(dataset)
            except TypeError: pass
        store_attr(self, 'dataset,bs,shuffle,drop_last,indexed,n,pin_memory,timeout')
        self.rng,self.nw,self.offs = random.Random(),1,0
        self.fake_l = _FakeLoader(self, pin_memory, num_workers, timeout)

    def __len__(self):
        if self.n is None: raise TypeError
        if self.bs is None: return self.n
        return self.n//self.bs + (0 if self.drop_last or self.n%self.bs==0 else 1)

    def get_idxs(self):
        idxs = Inf.count if self.indexed else Inf.nones
        return idxs if self.n is None else list(itertools.islice(idxs, self.n))

    def sample(self):
        idxs = self.get_idxs()
        if self.shuffle: idxs = self.shuffle_fn(idxs)
        return (b for i,b in enumerate(idxs) if i//(self.bs or 1)%self.nw==self.offs)

    def __iter__(self):
        self.randomize()
        self.before_iter()
        for b in _loaders[self.fake_l.num_workers==0](self.fake_l): yield self.after_batch(b)
        self.after_iter()

    def create_batches(self, samps):
        self.it = iter(self.dataset) if self.dataset is not None else None
        res = map(self.do_item, samps)
        yield from map(self.do_batch, self.chunkify(res))

    def new(self, dataset=None, cls=None, **kwargs):
        if dataset is None: dataset = self.dataset
        if cls is None: cls = type(self)
        cur_kwargs = dict(dataset=dataset, num_workers=self.fake_l.num_workers, pin_memory=self.pin_memory, timeout=self.timeout,
                          bs=self.bs, shuffle=self.shuffle, drop_last=self.drop_last, indexed=self.indexed)
        for n in self._methods: cur_kwargs[n] = getattr(self, n)
        return cls(**merge(cur_kwargs, kwargs))

    @property
    def prebatched(self): return self.bs is None
    def chunkify(self, b): return b if self.prebatched else chunked(b, self.bs, self.drop_last)
    def shuffle_fn(self, idxs): return self.rng.sample(idxs, len(idxs))
    def randomize(self): self.rng = random.Random(self.rng.randint(0,2**32-1))
    def retain(self, res, b):  return retain_types(res, b[0] if is_listy(b) else b)
    def create_item(self, s):  return next(self.it) if s is None else self.dataset[s]
    def create_batch(self, b): return (fa_collate,fa_convert)[self.prebatched](b)
    def do_item(self, s):  return self.after_item(self.create_item(s))
    def do_batch(self, b): return self.retain(self.create_batch(self.before_batch(b)), b)
    def one_batch(self):
        with self.fake_l.no_multiproc(): return first(self)