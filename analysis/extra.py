import numpy as np, math
from scipy import stats

def mk_plain(y):
    y=np.asarray(y,float); n=len(y); i,j=np.triu_indices(n,1); dy=y[j]-y[i]
    S=np.sign(dy).sum(); _,c=np.unique(y,return_counts=True)
    var=(n*(n-1)*(2*n+5)-np.sum(c*(c-1)*(2*c+5)))/18
    z=(S-np.sign(S))/math.sqrt(var) if S!=0 else 0.0
    return float(2*(1-stats.norm.cdf(abs(z)))), float(np.median(dy/(j-i)))

def tfpw(y):
    """Trend-free pre-whitening (Yue et al. 2002) then plain Mann-Kendall."""
    y=np.asarray(y,float); n=len(y); t=np.arange(n)
    _,b=mk_plain(y)
    d=y-b*t
    r1=np.corrcoef(d[:-1],d[1:])[0,1]
    w=d[1:]-r1*d[:-1]
    y3=w+b*t[1:]
    p,b3=mk_plain(y3)
    return dict(p=p,slope=b3,r1=float(r1))

def seasonal_kendall(m_raw):
    """Hirsch et al. (1982): Mann-Kendall within each calendar month, summed. Input: monthly raw values, length 12*Y."""
    y=np.asarray(m_raw,float).reshape(-1,12)   # years x months
    S=0.0; V=0.0; slopes=[]
    for k in range(12):
        x=y[:,k]; n=len(x); i,j=np.triu_indices(n,1); dy=x[j]-x[i]
        S+=np.sign(dy).sum(); _,c=np.unique(x,return_counts=True)
        V+=(n*(n-1)*(2*n+5)-np.sum(c*(c-1)*(2*c+5)))/18
        slopes.append(dy/(j-i))
    z=(S-np.sign(S))/math.sqrt(V) if S!=0 else 0.0
    return dict(p=float(2*(1-stats.norm.cdf(abs(z)))),slope_yr=float(np.median(np.concatenate(slopes))))

def hinge(y,y0,min_months=36,B=300,seed=1):
    """Continuous two-segment (hinge) line. Breakpoint uncertainty from a circular block bootstrap of residuals."""
    y=np.asarray(y,float); n=len(y); t=np.arange(n,dtype=float)
    ks=np.arange(min_months,n-min_months)
    H=np.maximum(0,t[None,:]-ks[:,None])           # K x n
    st=t.sum(); stt=(t*t).sum()
    sh=H.sum(1); sth=(H*t).sum(1); shh=(H*H).sum(1)
    XtX=np.empty((len(ks),3,3))
    XtX[:,0,0]=n; XtX[:,0,1]=XtX[:,1,0]=st; XtX[:,0,2]=XtX[:,2,0]=sh
    XtX[:,1,1]=stt; XtX[:,1,2]=XtX[:,2,1]=sth; XtX[:,2,2]=shh
    inv=np.linalg.inv(XtX)
    def best(yy):
        Xty=np.stack([np.full(len(ks),yy.sum()),np.full(len(ks),(t*yy).sum()),H@yy],1)
        beta=np.einsum('kij,kj->ki',inv,Xty)
        sse=(yy*yy).sum()-np.einsum('ki,ki->k',beta,Xty)
        a=int(np.argmin(sse)); return a,beta[a],sse
    a,beta,sse=best(y)
    fit=beta[0]+beta[1]*t+beta[2]*H[a]
    res=y-fit
    r1=max(0.0,float(np.corrcoef(res[:-1],res[1:])[0,1]))
    L=int(min(60,max(3,round(2*(1+r1)/(1-r1)))))
    rng=np.random.default_rng(seed); kb=[]
    for _ in range(B):
        starts=rng.integers(0,n,size=math.ceil(n/L))
        idx=(starts[:,None]+np.arange(L)[None,:]).ravel()[:n]%n
        kb.append(ks[best(fit+res[idx])[0]])
    kb=np.array(kb)
    # F-like comparison against a single straight line (ignores memory: descriptive only)
    sl=stats.linregress(t,y); sse1=((y-(sl.intercept+sl.slope*t))**2).sum()
    yr=lambda k: y0+k/12
    return dict(year=round(yr(ks[a]),2),lo=round(yr(np.percentile(kb,2.5)),2),hi=round(yr(np.percentile(kb,97.5)),2),
                before_dec=float(beta[1]*120),after_dec=float((beta[1]+beta[2])*120),
                k=int(ks[a]),block=L,sse_gain=float(1-sse[a]/sse1),v0=float(fit[0]),vk=float(fit[ks[a]]),vn=float(fit[-1]))

def hamed_rao(y):
    """Modified Mann-Kendall (Hamed & Rao 1998): variance inflated using all significant
    lags of the rank autocorrelation of the Sen-detrended series."""
    y=np.asarray(y,float); n=len(y); t=np.arange(n)
    i,j=np.triu_indices(n,1); dy=y[j]-y[i]; S=np.sign(dy).sum(); b=np.median(dy/(j-i))
    _,c=np.unique(y,return_counts=True)
    var=(n*(n-1)*(2*n+5)-np.sum(c*(c-1)*(2*c+5)))/18
    r=stats.rankdata(y-b*t); r=r-r.mean(); den=(r*r).sum()
    lim=1.96/math.sqrt(n); s=0.0
    for k in range(1,n-2):
        rho=(r[:-k]*r[k:]).sum()/den
        if abs(rho)>lim: s+=(n-k)*(n-k-1)*(n-k-2)*rho
    ratio=1+2*s/(n*(n-1)*(n-2))
    ratio=max(ratio,1.0)          # only inflate (conservative)
    z=(S-np.sign(S))/math.sqrt(var*ratio) if S!=0 else 0.0
    return dict(p=float(2*(1-stats.norm.cdf(abs(z)))),slope=float(b),ratio=float(ratio))

def hirsch_slack(m_raw):
    """Seasonal Kendall with the Hirsch & Slack (1984) covariance correction between seasons.
    Works on the raw monthly record: no deseasonalising needed."""
    y=np.asarray(m_raw,float).reshape(-1,12); n=y.shape[0]
    i,j=np.triu_indices(n,1)
    sg=np.sign(y[j,:]-y[i,:])                # pairs x 12
    Sg=sg.sum(0); S=Sg.sum()
    R=np.apply_along_axis(stats.rankdata,0,y)
    K=sg.T@sg                                # 12 x 12, sum over pairs of sgn*sgn
    cov=(K+4*(R.T@R)-n*(n+1)**2)/3
    for g in range(12):                      # exact tie-corrected variance on the diagonal
        _,c=np.unique(y[:,g],return_counts=True)
        cov[g,g]=(n*(n-1)*(2*n+5)-np.sum(c*(c-1)*(2*c+5)))/18
    V=cov.sum()
    z=(S-np.sign(S))/math.sqrt(V) if S!=0 else 0.0
    slope=np.median(((y[j,:]-y[i,:])/(j-i)[:,None]).ravel())
    return dict(p=float(2*(1-stats.norm.cdf(abs(z)))),slope_yr=float(slope))

def mk_ess(y):
    """Memory-corrected Mann-Kendall (lag-1 effective sample size). Returns p, Sen slope per step."""
    y=np.asarray(y,float); n=len(y); t=np.arange(n); i,j=np.triu_indices(n,1); dy=y[j]-y[i]
    S=np.sign(dy).sum(); _,c=np.unique(y,return_counts=True)
    var=(n*(n-1)*(2*n+5)-np.sum(c*(c-1)*(2*c+5)))/18
    b=float(np.median(dy/(j-i))); res=y-b*t; res=res-np.median(res)
    r1=max(0.0,float(np.corrcoef(res[:-1],res[1:])[0,1])); neff=n*(1-r1)/(1+r1)
    z=(S-np.sign(S))/math.sqrt(var*n/neff) if S!=0 else 0.0
    return float(2*(1-stats.norm.cdf(abs(z)))), b

def robustness(raw, anom, y0, y1, grid_map):
    """Multiverse: every window >= max(10, half the record) x four defensible methods."""
    years=y1-y0+1; minlen=max(10,math.ceil(years/2))
    W=[(a,b) for a in range(y0,y1+1) for b in range(a+minlen-1,y1+1)]
    raw=np.asarray(raw,float); anom=np.asarray(anom,float)
    ann=raw.reshape(-1,12).mean(1)
    out={'minlen':minlen,'a':[],'b':[],'m':[[],[],[],[]]}
    for a,b in W:
        i0=(a-y0)*12; i1=(b-y0+1)*12
        g=grid_map[(a,b)]                       # [a,b,slope_dec,lp_careful,lp_naive]
        out['a'].append(a); out['b'].append(b)
        out['m'][0].append([g[2],g[3]])
        hr=hamed_rao(anom[i0:i1]); out['m'][1].append([g[2],round(math.log10(max(hr['p'],1e-300)),2)])
        hs=hirsch_slack(raw[i0:i1]); out['m'][2].append([float(f"{hs['slope_yr']*10:.4g}"),round(math.log10(max(hs['p'],1e-300)),2)])
        pa,ba=mk_ess(ann[a-y0:b-y0+1]); out['m'][3].append([float(f"{ba*10:.4g}"),round(math.log10(max(pa,1e-300)),2)])
    return out

def decoy_false_positive(anom, slope_dec, r1, n_decoys=400, seed=7):
    """Share of trend-free block-bootstrap decoys that each test calls significant (same recipe as the page)."""
    y=np.asarray(anom,float); n=len(y); sm=slope_dec/120; t=np.arange(n)
    v0=np.median(y-sm*t); res=y-(v0+sm*t)
    phi=max(0.0,r1); L=int(min(60,max(3,round(2*(1+phi)/(1-phi)))))
    rng=np.random.default_rng(seed); careless=careful=0
    for _ in range(n_decoys):
        starts=rng.integers(0,n,size=math.ceil(n/L))
        d=res[((starts[:,None]+np.arange(L)[None,:]).ravel()[:n])%n]
        if stats.linregress(t,d).pvalue<0.05: careless+=1
        if mk_ess(d)[0]<0.05: careful+=1
    return dict(n=n_decoys,careless=careless/n_decoys,careful=careful/n_decoys,block=L)
