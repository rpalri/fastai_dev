#AUTOGENERATED! DO NOT EDIT! File to edit: dev/14a_callback_data.ipynb (unless otherwise specified).

__all__ = ['CollectDataCallback', 'WeightedDL', 'weighted_databunch']

#Cell
from ..test import *
from ..basics import *

#Cell
class CollectDataCallback(Callback):
    "Collect all batches, along with `pred` and `loss`, into `self.data`. Mainly for testing"
    def begin_fit(self): self.data = L()
    def after_batch(self): self.data.append(to_detach((self.xb,self.yb,self.pred,self.loss)))

#Cell
@delegates()
class WeightedDL(TfmdDL):
    def __init__(self, dataset=None, bs=None, wgts=None, **kwargs):
        super().__init__(dataset=dataset, bs=bs, **kwargs)
        wgts = array([1.]*len(dataset) if wgts is None else wgts)
        self.wgts = wgts/wgts.sum()

    def get_idxs(self):
        if self.n==0: return []
        return list(np.random.choice(self.n, self.n, p=self.wgts))

#Cell
@patch
@delegates(DataSource.databunch)
def weighted_databunch(self:DataSource, wgts, bs=16, **kwargs):
    xtra_kwargs = [{}] * (self.n_subsets-1)
    return dsrc.databunch(bs=bs, dl_type=WeightedDL, dl_kwargs=({'wgts':wgts}, *xtra_kwargs), **kwargs)