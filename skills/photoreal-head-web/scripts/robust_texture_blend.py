"""Bounded-memory, per-texel cross-view color consensus (not intrinsic albedo)."""
import warnings
import numpy as np


def robust_blend(records, accum, weights, counts, threshold=0.06, chunk_size=32768):
    """Return linear RGB, rejected count, ambiguous flag, disagreement in sRGB.

    records: sorted unique atlas sample indices, linear RGB, geometric weights per view.
    A strict majority of at least two agreeing observations is required to reject
    an outlier. Two discordant views or no strict consensus remain ambiguous:
    preserve the weighted draft and demand review. One view is not consensus.
    Threshold is max-channel sRGB distance, not a calibrated perceptual metric.
    """
    if not 0.01 <= threshold <= 0.25 or not 1 <= chunk_size <= 65536:
        raise ValueError('Invalid consensus threshold/chunk size')
    chunk_size=min(chunk_size,max(1,1_000_000//max(1,len(records))))
    n=len(weights); rgb=np.zeros_like(accum); valid=weights>1e-10
    rgb[valid]=accum[valid]/weights[valid,None]
    view_eligible=np.zeros(len(records),np.int64); view_rejected=np.zeros(len(records),np.int64)
    rejected=np.zeros(n,np.uint16); ambiguous=np.zeros(n,bool); disagreement=np.zeros(n,np.float32)
    for start in range(0,n,chunk_size):
        end=min(start+chunk_size,n); width=end-start
        if not np.any(counts[start:end]>=2): continue
        colors=np.full((len(records),width,3),np.nan,np.float32)
        ww=np.zeros((len(records),width),np.float32)
        for k,(indices,c,q) in enumerate(records):
            a,b=np.searchsorted(indices,[start,end]); ii=indices[a:b]-start
            colors[k,ii]=c[a:b]; ww[k,ii]=q[a:b]
        present=ww>1e-10
        s=np.where(colors<=.0031308,colors*12.92,1.055*np.clip(colors,0,1)**(1/2.4)-.055)
        s[~present]=np.nan
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            median=np.nanmedian(s,axis=0)
            span=np.nanmax(s,axis=0)-np.nanmin(s,axis=0)
        delta=np.max(np.abs(s-median[None]),axis=-1)
        agree=present&(delta<=threshold); c=present.sum(axis=0); a=agree.sum(axis=0)
        spread=np.nan_to_num(np.max(span,axis=-1),nan=0.)
        # With 2 samples compare their full pairwise spread (not half-distance to median).
        conflict=(c>=2)&(spread>threshold)
        # A majority around a median is insufficient if the agreeing cluster itself spans
        # more than the tolerance; do not promote ambiguous mixtures.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            cluster=np.where(agree[...,None],s,np.nan)
            cluster_span=np.nanmax(cluster,axis=0)-np.nanmin(cluster,axis=0)
        coherent=np.nan_to_num(np.max(cluster_span,axis=-1),nan=np.inf)<=threshold
        consensus=(c>=3)&(a>c/2)&(a>=2)&coherent
        use=consensus&(a<c)
        view_eligible+=(present&consensus[None,:]).sum(axis=1)
        view_rejected+=(present&~agree&use[None,:]).sum(axis=1)
        w=ww*agree; denom=w.sum(axis=0); color=np.nan_to_num(colors,nan=0.)
        total=np.sum(color*w[...,None],axis=0)
        rgb[start:end][use]=total[use]/denom[use,None]
        rejected[start:end][use]=(c-a)[use]
        ambiguous[start:end]=conflict&~consensus
        disagreement[start:end]=spread
    return rgb,rejected,ambiguous,disagreement,view_eligible,view_rejected
