import sys, json, glob, math, os
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
ROOT=os.path.dirname(HERE)
import numpy as np, pandas as pd
from scipy import stats
from load import read_giovanni, to_monthly
from engine import deseasonalize
from extra import hamed_rao, hirsch_slack, hinge, mk_plain, robustness, decoy_false_positive

UP=os.path.join(ROOT,'data','raw')+os.sep
_tri={}
def tri(n):
    if n not in _tri: _tri[n]=np.triu_indices(n,1)
    return _tri[n]

def mk(y, ci=False):
    """Mann-Kendall + Sen slope, p corrected with an effective sample size from lag-1 autocorrelation."""
    y=np.asarray(y,float); n=len(y); t=np.arange(n)
    i,j=tri(n); dy=y[j]-y[i]; sl=dy/(j-i)
    S=np.sign(dy).sum()
    _,cnt=np.unique(y,return_counts=True)
    var=(n*(n-1)*(2*n+5)-np.sum(cnt*(cnt-1)*(2*cnt+5)))/18
    slope=float(np.median(sl))
    res=y-slope*t; res=res-np.median(res)
    r1=float(np.corrcoef(res[:-1],res[1:])[0,1]) if n>3 else 0.0
    r1=max(0.0,r1)
    n_eff=n*(1-r1)/(1+r1); infl=n/n_eff
    vc=var*infl
    z=(S-np.sign(S))/math.sqrt(vc) if S!=0 else 0.0
    p=2*(1-stats.norm.cdf(abs(z)))
    out=dict(slope=slope,p=float(p),r1=r1,n_eff=float(n_eff),n=n,resid_sd=float(np.std(res)))
    if ci:
        N=len(sl); C=1.96*math.sqrt(vc); srt=np.sort(sl)
        lo=srt[max(int(math.floor((N-C)/2)),0)]; hi=srt[min(int(math.ceil((N+C)/2)),N-1)]
        out['lo']=float(lo); out['hi']=float(hi)
    return out

def naive_p(y):
    y=np.asarray(y,float); t=np.arange(len(y))
    return float(stats.linregress(t,y).pvalue)

def lp(p): return round(math.log10(max(p,1e-300)),2)

SERIES=[
 dict(key='no2_china',files=['A1_part1.csv','A1_part2.csv','A1_part3.csv'],y0=2005,y1=2025,scale=1e-15,off=0,min_days=10,
      units='10¹⁵ molecules/cm²',decimals=2,pct=True),
 dict(key='no2_india',files=['A2_part1.csv','A2_part2.csv','A2_part3.csv'],y0=2005,y1=2025,scale=1e-15,off=0,min_days=10,
      units='10¹⁵ molecules/cm²',decimals=2,pct=True),
 dict(key='t2m_alaska',files=['A3_merra2_t2m_alaska.csv'],y0=1980,y1=2025,scale=1,off=-273.15,min_days=1,units='°C',decimals=2,pct=False),
 dict(key='precip_uscentral',files=['A4_merra2_precip_uscentral.csv'],y0=1980,y1=2025,scale=86400,off=0,min_days=1,units='mm/day',decimals=3,pct=True),
 dict(key='precip_alaska',files=['B1_precip_alaska.csv'],y0=1980,y1=2025,scale=86400,off=0,min_days=1,units='mm/day',decimals=3,pct=True),
 dict(key='snow_land_alaska',files=['B2_snow_alaska_1.csv'],y0=1980,y1=2025,scale=1,off=0,min_days=1,units='kg/m²',decimals=1,pct=True),
 dict(key='snow_glacier_alaska',files=['B2_snow_alaska.csv'],y0=1980,y1=2025,scale=1,off=0,min_days=1,units='kg/m²',decimals=1,pct=True),
 dict(key='soilwet_alaska',files=['B3_soilwet_alaska.csv'],y0=1980,y1=2025,scale=1,off=0,min_days=1,units='fraction (0 to 1)',decimals=4,pct=True),
 dict(key='aod_alaska',files=['B4_aod_alaska.csv'],y0=1980,y1=2025,scale=1,off=0,min_days=1,units='AOD (unitless)',decimals=4,pct=True),
]
MINLEN=8

def sig(v,d=4):
    if v==0: return 0
    return float(f"{v:.{d}g}")

def build(sp):
    s=read_giovanni([UP+f for f in sp['files']])
    m,_=to_monthly(s,sp['min_days'])
    m=m*sp['scale']+sp['off']
    m=m[f"{sp['y0']}-01":f"{sp['y1']}-12"]
    assert m.isna().sum()==0 and len(m)==(sp['y1']-sp['y0']+1)*12,(sp['key'],m.isna().sum(),len(m))
    d=deseasonalize(m)
    clim=m.groupby(m.index.month).mean()
    mean=float(m.mean()); n=len(m); yrs=n/12
    raw_mk=mk(m.values,ci=True); des=mk(d.values,ci=True)
    raw_np=naive_p(m.values); des_np=naive_p(d.values)
    half=n//2
    h1=mk(d.values[:half]); h2=mk(d.values[half:])
    sd=des['resid_sd']
    # --- verdict
    sl=des['slope']*120; lo=des['lo']*120; hi=des['hi']*120
    ci_excl=(lo>0 or hi<0)
    consistent=(np.sign(h1['slope'])==np.sign(h2['slope']))
    # Weatherhead et al. (1998) style estimates
    phi=des['r1']; infl=math.sqrt((1+phi)/(1-phi))
    omega=abs(des['slope'])*12
    nstar=((3.3*sd/omega)*infl)**(2/3) if omega>0 else None
    mindet_yr=3.3*sd*infl/(yrs**1.5)
    detect=dict(record_years=round(yrs,1),nstar=None if nstar is None or nstar>300 else round(nstar,1),
                min_detect_dec=sig(mindet_yr*10,3),noise_sd=sig(sd,3),r1=round(phi,2))
    if des['p']<0.05:
        if not consistent: verdict='UNSTEADY'
        elif des['p']<0.01 and ci_excl: verdict='CONFIRMED'
        else: verdict='WEAK'
    else:
        verdict='NO TREND DETECTED' if abs(sl)<0.15*mindet_yr*10 else 'INCONCLUSIVE'
    # --- second opinions and extra questions
    hr=hamed_rao(d.values); hs=hirsch_slack(m.values)
    ym=m.values.reshape(-1,12); months=[]
    for g in range(12):
        pg,bg=mk_plain(ym[:,g]); months.append([sig(bg*10),lp(pg)])
    hg=hinge(d.values,sp['y0'])
    clear=(hg['hi']-hg['lo'])<=0.4*yrs
    extra=dict(hr=dict(lp=lp(hr['p']),ratio=round(hr['ratio'],1)),
               hs=dict(lp=lp(hs['p']),slope_dec=sig(hs['slope_yr']*10)),
               months=months,
               hinge=dict(year=hg['year'],lo=hg['lo'],hi=hg['hi'],before_dec=sig(hg['before_dec']),after_dec=sig(hg['after_dec']),k=hg['k'],clear=bool(clear),v0=sig(hg['v0']),vk=sig(hg['vk']),vn=sig(hg['vn'])))
    # --- window grid (fixed climatology, deseasonalised once)
    dv=d.values; cells=[]
    for a in range(sp['y0'],sp['y1']+1):
        for b in range(a+MINLEN-1,sp['y1']+1):
            seg=dv[(a-sp['y0'])*12:(b-sp['y0']+1)*12]
            r=mk(seg)
            cells.append([a,b,sig(r['slope']*120,4),lp(r['p']),lp(naive_p(seg))])
    cells_arr=np.array(cells)
    fp=decoy_false_positive(d.values,sl,des['r1'])
    rob=robustness(m.values,d.values,sp['y0'],sp['y1'],{(c[0],c[1]):c for c in cells})
    out=dict(key=sp['key'],units=sp['units'],decimals=sp['decimals'],pct=sp['pct'],
        y0=sp['y0'],y1=sp['y1'],n=n,mean=sig(mean,5),
        raw=[sig(v,5) for v in m.values],anom=[sig(v,5) for v in d.values],clim=[sig(v,5) for v in clim.values],
        stats=dict(
          raw=dict(slope_dec=sig(raw_mk['slope']*120),lo_dec=sig(raw_mk['lo']*120),hi_dec=sig(raw_mk['hi']*120),lp=lp(raw_mk['p']),lp_naive=lp(raw_np),r1=round(raw_mk['r1'],2),n_eff=round(raw_mk['n_eff'])),
          des=dict(slope_dec=sig(sl),lo_dec=sig(lo),hi_dec=sig(hi),lp=lp(des['p']),lp_naive=lp(des_np),r1=round(des['r1'],2),n_eff=round(des['n_eff'])),
          resid_sd=sig(sd,4),season_range=sig(float(clim.max()-clim.min()),4),
          half=dict(first=dict(slope_dec=sig(h1['slope']*120),lp=lp(h1['p'])),second=dict(slope_dec=sig(h2['slope']*120),lp=lp(h2['p']))),
          verdict=verdict,consistent=bool(consistent),ci_excludes_zero=bool(ci_excl),
          std_dec=sig(sl/sd,3),std_lo=sig(lo/sd,3),std_hi=sig(hi/sd,3)),
        detect=detect,extra=extra,rob=rob,fp=fp,
        grid=cells)
    return out

res={}
for sp in SERIES:
    res[sp['key']]=build(sp)
    st=res[sp['key']]['stats']
    e=res[sp['key']]['extra'];print(sp['key'],'HR 10^',e['hr']['lp'],'HS 10^',e['hs']['lp'],'hinge',e['hinge']['year'],e['hinge']['lo'],e['hinge']['hi'],e['hinge']['clear']);print(sp['key'],st['verdict'],'slope/dec',st['des']['slope_dec'],'p_corr 10^',st['des']['lp'],'raw p 10^',st['raw']['lp'],'half',st['half']['first']['slope_dec'],st['half']['second']['slope_dec'],'nstar',res[sp['key']]['detect']['nstar'],'mindet',res[sp['key']]['detect']['min_detect_dec'],flush=True)
OUT=os.path.join(ROOT,'web','data.json')
json.dump(res,open(OUT,'w'),separators=(',',':'),ensure_ascii=False)
print('wrote',OUT,os.path.getsize(OUT),'bytes')
