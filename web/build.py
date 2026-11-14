"""Build docs/index.html: the page template with the analysis results and two sample Giovanni files embedded."""
import json, os
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); RAW=os.path.join(ROOT,'data','raw')
t=open(os.path.join(HERE,'template.html'),encoding='utf-8').read()
d=open(os.path.join(HERE,'data.json'),encoding='utf-8').read()
s=json.dumps(open(os.path.join(RAW,'A3_merra2_t2m_alaska.csv'),encoding='utf-8').read())
s2=json.dumps({'A':[{'name':f'A1_part{i}.csv','text':open(os.path.join(RAW,f'A1_part{i}.csv'),encoding='utf-8').read()} for i in (1,2,3)],
               'B':[{'name':f'A2_part{i}.csv','text':open(os.path.join(RAW,f'A2_part{i}.csv'),encoding='utf-8').read()} for i in (1,2,3)]})
for k in ('__DATA__','__SAMPLE2__','__SAMPLE__'): assert k in t, k
out=t.replace('__DATA__',d).replace('__SAMPLE2__',s2).replace('__SAMPLE__',s)
os.makedirs(os.path.join(ROOT,'docs'),exist_ok=True)
open(os.path.join(ROOT,'docs','index.html'),'w',encoding='utf-8').write(out)
print('wrote docs/index.html',len(out),'characters')
