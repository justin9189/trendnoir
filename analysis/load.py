import pandas as pd, numpy as np, glob, io

def read_giovanni(paths):
    frames=[]
    for p in paths:
        lines=open(p).read().splitlines()
        i=[k for k,l in enumerate(lines) if l.startswith('time')][0]
        df=pd.read_csv(io.StringIO("\n".join(lines[i:])),skipinitialspace=True)
        df.columns=['time','value']
        df['time']=pd.to_datetime(df['time'])
        frames.append(df)
    df=pd.concat(frames).drop_duplicates('time').sort_values('time')
    df.loc[df['value']<-1e29,'value']=np.nan
    return df.set_index('time')['value']

def to_monthly(s, min_days=10):
    g=s.resample('MS')
    m=g.mean()
    n=g.count()
    m[n<min_days]=np.nan
    return m, n
