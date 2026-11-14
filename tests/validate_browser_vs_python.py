"""Feed every raw Giovanni file to the built page's in-browser analysis and compare with the Python results.
Requires: pip install playwright && playwright install chromium"""
import json, math, os, pathlib
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=json.load(open(os.path.join(ROOT,'web','data.json')))
U=os.path.join(ROOT,'data','raw')+os.sep
PAGE=pathlib.Path(os.path.join(ROOT,'docs','index.html')).as_uri()
cases={'no2_china':(['A1_part1.csv','A1_part2.csv','A1_part3.csv'],'none',1e-15),
 'no2_india':(['A2_part1.csv','A2_part2.csv','A2_part3.csv'],'none',1e-15),
 't2m_alaska':(['A3_merra2_t2m_alaska.csv'],'k2c',1),'precip_uscentral':(['A4_merra2_precip_uscentral.csv'],'s2d',1),
 'precip_alaska':(['B1_precip_alaska.csv'],'s2d',1),'snow_land_alaska':(['B2_snow_alaska_1.csv'],'none',1),
 'snow_glacier_alaska':(['B2_snow_alaska.csv'],'none',1),'soilwet_alaska':(['B3_soilwet_alaska.csv'],'none',1),'aod_alaska':(['B4_aod_alaska.csv'],'none',1)}
def rel(a,b): return abs(a-b)/max(abs(b),1e-12)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); errs=[]
    pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto(PAGE); pg.wait_for_timeout(400)
    worst={}
    for k,(files,conv,sc) in cases.items():
        texts=[{'name':f,'text':open(U+f).read()} for f in files]
        r=pg.evaluate("""async ([texts,conv])=>{const T=window.__TN;const rec=T.mergeParsed(texts.map(x=>T.parseGiovanni(x.text,x.name)));
            const mo=T.toMonthly(rec);const t0=performance.now();const res=await T.analyzeMonthly(mo,conv,()=>{});res.ms=performance.now()-t0;return res;}""",[texts,conv])
        P=D[k]; ps=P['stats']; js=r['stats']
        chk=[]
        chk.append(('years', (r['y0'],r['y1'])==(P['y0'],P['y1'])))
        chk.append(('verdict', js['verdict']==ps['verdict']))
        d=[]
        d.append(rel(js['des']['slope_dec']*sc,ps['des']['slope_dec']))
        d.append(rel(js['des']['lo_dec']*sc,ps['des']['lo_dec'])); d.append(rel(js['des']['hi_dec']*sc,ps['des']['hi_dec']))
        d.append(rel(js['raw']['slope_dec']*sc,ps['raw']['slope_dec']))
        lpd=[abs(js['des']['lp']-ps['des']['lp']) if ps['des']['lp']>-15 else 0, abs(js['raw']['lp']-ps['raw']['lp']),
             abs(r['extra']['hr']['lp']-P['extra']['hr']['lp']) if P['extra']['hr']['lp']>-15 else 0,
             abs(r['extra']['hs']['lp']-P['extra']['hs']['lp']) if P['extra']['hs']['lp']>-15 else 0,
             abs(js['half']['first']['lp']-ps['half']['first']['lp']), abs(js['half']['second']['lp']-ps['half']['second']['lp'])]
        naive=abs(js['des']['lp_naive']-ps['des']['lp_naive']) if ps['des']['lp_naive']>-15 else 0
        months=max(abs(a[1]-b_[1]) for a,b_ in zip(r['extra']['months'],P['extra']['months']))
        hk=(r['extra']['hinge']['k']==P['extra']['hinge']['k'])
        g1={(c[0],c[1]):c for c in P['grid']}
        gs=max(rel(c[2]*sc,g1[(c[0],c[1])][2]) for c in r['grid'] if abs(g1[(c[0],c[1])][2])>1e-9)
        gl=max(abs(c[3]-g1[(c[0],c[1])][3]) for c in r['grid'] if g1[(c[0],c[1])][3]>-15)
        L5=math.log10(0.05); ra=r['rob']; rp=P['rob']
        same_w=(ra['a']==rp['a'] and ra['b']==rp['b'])
        agree=sum(1 for mi in range(4) for x,y in zip(ra['m'][mi],rp['m'][mi]) if (x[1]<L5)==(y[1]<L5) and ((x[0]>=0)==(y[0]>=0) or abs(y[0])<1e-9))
        totr=sum(len(m) for m in rp['m'])
        nfmt=lambda x:f"{x:.1e}"
        print(f"{k:20s} {'OK' if all(v for _,v in chk) else 'MISMATCH '+str(chk)} slopes rel.err {nfmt(max(d))} | log10 p diff {max(lpd):.3f} | naive {naive:.3f} | months {months:.3f} | hinge same: {hk} | grid slope rel {nfmt(gs)} p {gl:.3f} | rob windows same {same_w}, rob agree {agree}/{totr} | {r['ms']/1000:.1f}s")
    print('errors',errs); b.close()
