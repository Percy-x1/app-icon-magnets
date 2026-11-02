from pathlib import Path
from copy import deepcopy
import os,json,zipfile,xml.etree.ElementTree as E,hashlib,subprocess,re
import numpy as np
R=Path(__file__).resolve().parent.parent
manifest=json.loads((R/'reports/project_manifest.json').read_text());SRC=Path(manifest['reference_project']);C='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';P='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
with zipfile.ZipFile(SRC)as z:
 original=json.loads(z.read('Metadata/project_settings.config'));negative=E.fromstring(z.read('3D/Objects/object_1.model')).find(f'{{{C}}}resources/{{{C}}}object[@id="4"]');sourcepart=E.fromstring(z.read('Metadata/model_settings.config')).find("object/part[@subtype='negative_part']")
def canonical(e):return E.canonicalize(E.tostring(e,encoding='unicode'))
for ent in manifest['files']:
 f=Path(ent['file']);before=hashlib.sha256(f.read_bytes()).hexdigest()
 with zipfile.ZipFile(f)as z:
  assert z.testzip()is None
  settings=json.loads(z.read('Metadata/project_settings.config'));cfg=E.fromstring(z.read('Metadata/model_settings.config'));root=E.fromstring(z.read('3D/3dmodel.model'))
  for k in original:
   if k not in ent['remapped_configuration_keys']:assert settings[k]==original[k],(f,k)
  assert settings['filament_colour']==ent['filament_colors']
  assert len(cfg.findall('object'))==len(cfg.findall('plate'))==len(ent['icons'])
  for icon,item in zip(ent['icons'],root.find('{'+C+'}build')):
   assert item.get('objectid')==str(icon['object_id']);v=list(map(float,item.get('transform').split()));assert v[:9]==[1,0,0,0,-1,0,0,0,-1]and v[11]==4
   ob=cfg.find(f'object[@id="{icon["object_id"]}"]');negpart=ob.find("part[@subtype='negative_part']");assert negpart is not None
   p0=deepcopy(sourcepart);p1=deepcopy(negpart)
   for p in [p0,p1]:p.attrib.pop('id');p.attrib.pop('uuid')
   assert canonical(p0)==canonical(p1)
   ext=E.fromstring(z.read(f'3D/Objects/object_{icon["plate"]}.model'));neg=ext.find(f'{{{C}}}resources/{{{C}}}object[@id="{icon["negative_id"]}"]');a=deepcopy(negative);b=deepcopy(neg);a.set('id','1');b.set('id','1');assert canonical(a)==canonical(b)
   assembly=root.find(f'{{{C}}}resources/{{{C}}}object[@id="{icon["object_id"]}"]');comp=assembly.find(f'{{{C}}}components/{{{C}}}component[@objectid="{icon["negative_id"]}"]');assert comp.get('transform')=='0.236328121 0 0 0 -0.236328121 -2.89418477e-17 0 9.51971521e-18 -0.0777343738 0 2.60237445e-16 0.88'
   # All positive volumes are on the bed after the requested X-axis flip.
   bounds=[]
   for mid in icon['part_ids']:
    vv=ext.findall(f'{{{C}}}resources/{{{C}}}object[@id="{mid}"]/{{{C}}}mesh/{{{C}}}vertices/{{{C}}}vertex');pts=np.array([[float(q.get(ax))for ax in 'xyz']for q in vv]);pts[:,1]*=-1;pts[:,2]=4-pts[:,2];bounds.append(np.array([pts.min(0),pts.max(0)]))
   bounds=np.array(bounds);low=bounds[:,0].min(0);high=bounds[:,1].max(0);assert np.allclose(high-low,[40,40,4],atol=1e-5)and abs(low[2])<1e-5
  assert all(len(icon['colors'])<=4 for icon in ent['icons'])
 log=R/'reports'/('readback_'+f.stem+'.log')
 with log.open('w')as out:r=subprocess.run([os.environ.get('BAMBU_STUDIO_PATH','/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'),'--datadir',str(R/'.bambu-info'),'--info',str(f)],stdout=out,stderr=subprocess.STDOUT)
 txt=log.read_text();assert r.returncode==0,(f,txt[-500:]);parts=re.findall(r'number_of_parts\s*=\s*(\d+)',txt);assert sorted(map(int,parts))==sorted(x['positive_count']for x in ent['icons']),(f,parts)
 assert hashlib.sha256(f.read_bytes()).hexdigest()==before
 ent['native_readback_passed']=True;ent['print_parameters_preserved']=True;ent['negative_geometry_and_transform_preserved']=True;ent['logo_face_down_verified']=True
 print('PASS',f.name,'icons',len(ent['icons']),flush=True)
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==manifest['source_sha256']
(R/'reports/final_validation.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('ALL PROJECTS PASS',flush=True)
