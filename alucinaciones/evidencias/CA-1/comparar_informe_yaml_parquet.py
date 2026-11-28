"""CA-1 verificación: informe (§2 y §3.3) -> YAML -> parquet. Uso: .venv/bin/python alucinaciones/evidencias/CA-1/comparar_informe_yaml_parquet.py"""
import re, sys, pandas as pd, yaml
from datetime import date, timedelta
from pathlib import Path; R=str(Path(__file__).resolve().parents[3])+'/'
df=pd.read_parquet(R+'data/processed/m1/calendario.parquet')
print(df.shape, df.fecha.min(), df.fecha.max()); print(df.dtypes)
fest=df[df.festivo][['fecha','festivo_nombre']]
print('n festivos',len(fest), fest.groupby(pd.to_datetime(fest.fecha).dt.year).size().to_dict())
# informe tables
txt=open(R+'docs/investigacion/CA-1_fuentes_calendario.md').read()
sec=txt.split('## 2.')[1].split('## 3.')[0]
inf={(m.group(1)):m.group(2).strip() for m in re.finditer(r'^\| (\d{4}-\d\d-\d\d) \| \w+ \| ([^|]+) \|',sec,re.M)}
pq={str(r.fecha):r.festivo_nombre for r in fest.itertuples()}
print('informe',len(inf),'parquet',len(pq))
print('solo informe',set(inf)-set(pq)); print('solo parquet',set(pq)-set(inf))
print('nombre distinto',[(k,inf[k],pq[k]) for k in inf if k in pq and inf[k]!=pq[k]])
# weekday in informe
dias=['lun','mar','mié','jue','vie','sáb','dom']
bad=[m.group(0) for m in re.finditer(r'^\| (\d{4}-\d\d-\d\d) \| (\w+) \|',sec,re.M) if dias[date.fromisoformat(m.group(1)).weekday()]!=m.group(2)]
print('dia semana mal en informe',bad)
# yaml vs informe 3.3
y=yaml.safe_load(open(R+'data/externos/m1/calendario_fuentes.yaml'))
blk=txt.split('### 3.3')[1].split('### 3.4')[0]
infr=set((m.group(1),m.group(2),m.group(3)) for m in re.finditer(r'^(\w+),(\d{4}-\d\d-\d\d),(\d{4}-\d\d-\d\d)',blk,re.M))
yr=set()
for k,c in y['ciudades'].items():
  for b in c['bloques']:
    for a,z in b['rangos']: yr.add((k,a,z))
print('rangos informe',len(infr),'yaml',len(yr)); print('solo informe',sorted(infr-yr)); print('solo yaml',sorted(yr-infr))
# yaml vs parquet
for k,c in y['ciudades'].items():
  col='vacaciones_escolares_'+c['divipola']
  s=set()
  for b in c['bloques']:
    for a,z in b['rangos']:
      d=date.fromisoformat(a)
      while d<=date.fromisoformat(z): s.add(d); d+=timedelta(1)
  ci,cf=(date.fromisoformat(x) for x in c['cobertura'])
  exp=[pd.NA if (d<ci or d>cf) else (d in s) for d in df.fecha]
  got=df[col].tolist()
  diff=[(d,e,g) for d,e,g in zip(df.fecha,exp,got) if not ((e is pd.NA and g is pd.NA) or (e is not pd.NA and g is not pd.NA and bool(e)==bool(g)))]
  print(col,'true',int(df[col].fillna(False).sum()),'nulos',int(df[col].isna().sum()),'difs',len(diff))
  out=sorted(d for d in s if d<ci or d>cf); print('  receso fuera de cobertura:',out[:3], len(out))
print((df.vacaciones_escolares.fillna(False)==df.vacaciones_escolares_11001.fillna(False)).all())
# semanas por anio lectivo
for k,c in y['ciudades'].items():
  for b in c['bloques']:
    n=sum((date.fromisoformat(z)-date.fromisoformat(a)).days+1 for a,z in b['rangos'])
    print(k,b['anio_lectivo'],n,'dias',round(n/7,2),'sem')
