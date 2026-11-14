import numpy as np, pandas as pd
from scipy import stats

def deseasonalize(m):
    """Subtract monthly climatology (mean of each calendar month)."""
    clim=m.groupby(m.index.month).transform('mean')
    return m-clim

def sen_slope(y):
    """Sen's slope per time step and its 95% CI (Hirsch-style, no tie/autocorr corr here)."""
    y=np.asarray(y,float); t=np.arange(len(y))
    ok=~np.isnan(y); y=y[ok]; t=t[ok]
    i,j=np.triu_indices(len(y),1)
    sl=(y[j]-y[i])/(t[j]-t[i])
    return np.median(sl), sl

def mann_kendall(y, autocorr_correct=True):
    """Mann-Kendall with Hamed-Rao-lite: effective sample size correction via lag-1 autocorr of detrended residuals.
    Returns dict(S, z, p, slope_per_step, ci_lo, ci_hi, n, r1, n_eff)."""
    y=np.asarray(y,float); ok=~np.isnan(y); yy=y[ok]; n=len(yy)
    t=np.arange(len(y))[ok]
    # S statistic
    diff=np.sign(yy[None,:]-yy[:,None])
    S=np.triu(diff,1).sum()
    # tie-corrected variance
    _,cnt=np.unique(yy,return_counts=True)
    var=(n*(n-1)*(2*n+5)-np.sum(cnt*(cnt-1)*(2*cnt+5)))/18
    slope,sl=sen_slope(y)
    # lag-1 autocorr of residuals after removing Sen trend
    resid=yy-(slope*t+np.median(yy-slope*t))
    r1=np.corrcoef(resid[:-1],resid[1:])[0,1] if n>3 else 0
    r1=max(0.0,r1)  # only correct for positive autocorrelation
    n_eff=n*(1-r1)/(1+r1) if autocorr_correct else n
    infl=n/n_eff if autocorr_correct else 1.0
    var_c=var*infl
    z=(S-np.sign(S))/np.sqrt(var_c) if S!=0 else 0.0
    p=2*(1-stats.norm.cdf(abs(z)))
    # CI of Sen slope, with corrected variance
    N=len(sl); C=1.96*np.sqrt(var_c)
    srt=np.sort(sl)
    lo_i=int(np.floor((N-C)/2)); hi_i=int(np.ceil((N+C)/2))
    lo=srt[max(lo_i,0)]; hi=srt[min(hi_i,N-1)]
    return dict(S=int(S),z=float(z),p=float(p),slope=float(slope),ci_lo=float(lo),ci_hi=float(hi),n=n,r1=float(r1),n_eff=float(n_eff))

def ols(y):
    y=np.asarray(y,float); t=np.arange(len(y)); ok=~np.isnan(y)
    r=stats.linregress(t[ok],y[ok])
    return dict(slope=r.slope,p=r.pvalue)
