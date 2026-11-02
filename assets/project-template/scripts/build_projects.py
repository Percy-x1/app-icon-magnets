from pathlib import Path
from copy import deepcopy
import zipfile,json,xml.etree.ElementTree as E,uuid,hashlib,io,math
from datetime import date
import numpy as np,trimesh
from PIL import Image
R=Path(__file__).resolve().parent.parent
SRC=R/'assets/print-template.3mf'
C='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';P='http://schemas.microsoft.com/3dmanufacturing/production/2015/06';REL='http://schemas.openxmlformats.org/package/2006/relationships'
E.register_namespace('',C);E.register_namespace('p',P);E.register_namespace('BambuStudio','http://schemas.bambulab.com/package/2021')
with zipfile.ZipFile(SRC)as z:template={n:z.read(n)for n in z.namelist()}
settings0=json.loads(template['Metadata/project_settings.config']);assert len(settings0['filament_colour'])==20 and len(settings0['filament_self_index'])==39,'Adapt reference material schema before using this packager';cfg0=E.fromstring(template['Metadata/model_settings.config']);model0=E.fromstring(template['3D/3dmodel.model'])
neg0=E.fromstring(template['3D/Objects/object_1.model']).find(f'{{{C}}}resources/{{{C}}}object[@id="4"]')
negpart0=cfg0.find("object/part[@subtype='negative_part']");negcomponent0=model0.find(f'{{{C}}}resources/{{{C}}}object/{{{C}}}components/{{{C}}}component[@objectid="4"]')
order={s['name']:i for i,s in enumerate(json.loads((R/'assets/design_vectors.json').read_text()))}
specs=sorted(json.loads((R/'reports/fusion_validation.json').read_text()),key=lambda s:order[s['name']]);assert len(specs)>=1
IDENTITY='1 0 0 0 1 0 0 0 1 0 0 0'
MATRIX='1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'
def uid():return str(uuid.uuid4())
def xml(e):
 if e.tag=='{'+REL+'}Relationships':
  E.register_namespace('',REL);b=E.tostring(e,encoding='UTF-8',xml_declaration=True);E.register_namespace('',C);return b
 if e.tag=='{'+C+'}model':e.set('xmlns:BambuStudio','http://schemas.bambulab.com/package/2021')
 return E.tostring(e,encoding='UTF-8',xml_declaration=True)
def meta(e,k,v):return E.SubElement(e,'metadata',key=k,value=str(v))
def getmeta(e,k):return e.find(f'metadata[@key="{k}"]')
# Material arrays in this Bambu version have three different index layouts.
# Remap those indices without changing their physical/material parameter values.
variant_groups=[[j for j,v in enumerate(settings0['filament_self_index'])if int(v)==i+1]for i in range(20)]
remap_keys=[]
def settings(colors,nplates):
 out=deepcopy(settings0);sel=[1 if co=='#FFFFFF'else 3 if co=='#000000'else 0 for co in colors];changed=[]
 for k,v in settings0.items():
  if not isinstance(v,list):continue
  if k in ['flush_volumes_matrix','different_settings_to_system','filament_self_index']:continue
  if len(v)==20:out[k]=[v[i]for i in sel];changed.append(k)
  elif len(v)==39:out[k]=[v[j]for i in sel for j in variant_groups[i]];changed.append(k)
  elif len(v)in [40,80]and k.startswith('filament_'):
   size=len(v)//20;out[k]=[v[j]for i in sel for j in range(i*size,(i+1)*size)];changed.append(k)
 out['filament_self_index']=[str(j+1)for j,i in enumerate(sel)for _ in variant_groups[i]];changed.append('filament_self_index')
 out['different_settings_to_system']=settings0['different_settings_to_system'][:2]+[settings0['different_settings_to_system'][i+2]for i in sel];changed.append('different_settings_to_system')
 out['filament_colour']=colors;out['filament_multi_colour']=colors
 out['flush_volumes_matrix']=[settings0['flush_volumes_matrix'][i*20+j]for i in sel for j in sel];changed.append('flush_volumes_matrix')
 # The selected source plate uses these same tower coordinates on each new plate.
 for k in ['wipe_tower_x','wipe_tower_y']:out[k]=[settings0[k][0]]*nplates;changed.append(k)
 for k in settings0:
  if k not in changed:assert out[k]==settings0[k],k
 return out,sel,changed

def mesh_resource(path,id):
 m=trimesh.load_mesh(path,process=True);assert m.is_watertight and m.is_winding_consistent
 ob=E.Element('{'+C+'}object',id=str(id),type='model');mesh=E.SubElement(ob,'{'+C+'}mesh');vs=E.SubElement(mesh,'{'+C+'}vertices');ts=E.SubElement(mesh,'{'+C+'}triangles')
 for v in m.vertices:E.SubElement(vs,'{'+C+'}vertex',**{a:format(float(x),'.9g')for a,x in zip('xyz',v)})
 for f in m.faces:E.SubElement(ts,'{'+C+'}triangle',v1=str(f[0]),v2=str(f[1]),v3=str(f[2]))
 return ob,len(m.faces)
# Generate product previews directly from the Fusion mesh sections.
def previews(s):
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.patches import PathPatch
 from matplotlib.path import Path as MP
 from shapely.geometry import Polygon
 from shapely.geometry.polygon import orient
 def draw(ax,g,color):
  if g.is_empty:return
  if g.geom_type!='Polygon':
   for p in g.geoms:draw(ax,p,color)
   return
  g=orient(g);vs=[];cs=[]
  for ring in [g.exterior]+list(g.interiors):
   q=list(ring.coords);vs+=q;cs+=[MP.MOVETO]+[MP.LINETO]*(len(q)-2)+[MP.CLOSEPOLY]
  ax.add_patch(PathPatch(MP(vs,cs),facecolor=color,edgecolor='none'))
 fig,ax=plt.subplots(figsize=(5.12,5.12),dpi=100);fig.subplots_adjust(0,0,1,1)
 for b in s['bodies']:
  m=trimesh.load_mesh(R/'stl'/s['name']/(b['name']+'.stl'));z=1 if b['name'].startswith('Base')else 3.5
  sec=m.section([0,0,1],[0,0,z]);polys=[Polygon(p[:,:2]).buffer(0)for p in sec.discrete];g=polys[0]
  for p in polys[1:]:g=g.symmetric_difference(p)
  draw(ax,g,b['color'])
 ax.set_xlim(-23,23);ax.set_ylim(-23,23);ax.set_aspect('equal');ax.axis('off');buf=io.BytesIO();fig.savefig(buf,format='png',transparent=True);plt.close(fig)
 return buf.getvalue()

cached={s['name']:previews(s)for s in specs}
def build(ss,out):
 colors=list(dict.fromkeys(b['color']for s in ss for b in s['bodies']));settings_new,sel,changed=settings(colors,len(ss))
 model=deepcopy(model0);res=model.find('{'+C+'}resources');build=model.find('{'+C+'}build')
 for node in list(res):res.remove(node)
 for node in list(build):build.remove(node)
 for md in model.findall('{'+C+'}metadata'):
  if md.get('name')in ['CreationDate','ModificationDate']:md.text=date.today().isoformat()
  elif md.get('name')in ['Designer','DesignerUserId','ProfileCover','ProfileDescription','ProfileTitle']:md.text=''
 cfg=E.Element('config');assemble=E.Element('assemble');rels=E.Element('{'+REL+'}Relationships');data={n:template[n]for n in ['[Content_Types].xml','_rels/.rels','Metadata/slice_info.config']};nid=1;entry=[]
 for pi,s in enumerate(ss):
  path=f'3D/Objects/object_{pi+1}.model';external=E.Element('{'+C+'}model',unit='millimeter',**{'{http://www.w3.org/XML/1998/namespace}lang':'en-US'});ers=E.SubElement(external,'{'+C+'}resources')
  ids=[];facets=[]
  for b in s['bodies']:
   ob,fc=mesh_resource(R/'stl'/s['name']/(b['name']+'.stl'),nid);ers.append(ob);ids.append(nid);facets.append(fc);nid+=1
  negative=deepcopy(neg0);negative.set('id',str(nid));ers.append(negative);negid=nid;nid+=1;oid=nid;nid+=1
  asm=E.SubElement(res,'{'+C+'}object',id=str(oid),type='model',**{'{'+P+'}UUID':uid()});comps=E.SubElement(asm,'{'+C+'}components')
  obj=E.SubElement(cfg,'object',id=str(oid));meta(obj,'name',s['label']+' 40x40x4mm');meta(obj,'extruder',colors.index(s['base_color'])+1 if 'base_color'in s else colors.index(s['bodies'][0]['color'])+1);E.SubElement(obj,'metadata',face_count=str(sum(facets)))
  for vi,(b,mid,fc)in enumerate(zip(s['bodies'],ids,facets)):
   puid=uid();E.SubElement(comps,'{'+C+'}component',objectid=str(mid),transform=IDENTITY,**{'{'+P+'}path':'/'+path,'{'+P+'}UUID':puid})
   part=E.SubElement(obj,'part',id=str(mid),subtype='normal_part',uuid=puid)
   for k,v in [('name',s['label']+' '+b['name']),('matrix',MATRIX),('source_file',b['name']+'.stl'),('source_object_id',vi),('source_volume_id',0),('source_offset_x',0),('source_offset_y',0),('source_offset_z',0),('extruder',colors.index(b['color'])+1)]:meta(part,k,v)
   E.SubElement(part,'mesh_stat',face_count=str(fc),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
   E.SubElement(assemble,'assemble_item',object_id=str(oid),volume_id=str(vi),transform=IDENTITY)
  nc=deepcopy(negcomponent0);nc.set('objectid',str(negid));nc.set('{'+P+'}path','/'+path);nc.set('{'+P+'}UUID',uid());comps.append(nc)
  npart=deepcopy(negpart0);npart.set('id',str(negid));npart.set('uuid',nc.get('{'+P+'}UUID'));obj.append(npart)
  # Positive geometry is Z0..4; 180deg about X places its logo Z4 on the bed.
  columns=math.ceil(math.sqrt(len(ss)));x=128+(pi%columns)*307.2;y=128-(pi//columns)*307.2
  E.SubElement(build,'{'+C+'}item',objectid=str(oid),transform=f'1 0 0 0 -1 0 0 0 -1 {x:.8f} {y:.8f} 4',printable='1',**{'{'+P+'}UUID':uid()})
  E.SubElement(assemble,'assemble_item',object_id=str(oid),instance_id='0',transform=f'1 0 0 0 -1 0 0 0 -1 {x:.8f} {y:.8f} 4',offset='0 0 0')
  pl=deepcopy(cfg0.find('plate'));getmeta(pl,'plater_id').set('value',str(pi+1));getmeta(pl,'plater_name').set('value',f'{pi+1:02d} {s["label"]}')
  inst=pl.find('model_instance');getmeta(inst,'object_id').set('value',str(oid));getmeta(inst,'identify_id').set('value',str(1000+pi))
  for key,temp in [('thumbnail_file','Metadata/plate_{}.png'),('thumbnail_no_light_file','Metadata/plate_no_light_{}.png'),('top_file','Metadata/top_{}.png'),('pick_file','Metadata/pick_{}.png')]:
   filename=temp.format(pi+1);getmeta(pl,key).set('value',filename);data[filename]=cached[s['name']]
  png=Image.open(io.BytesIO(cached[s['name']]));png.thumbnail((128,128));buf=io.BytesIO();png.save(buf,format='PNG');data[f'Metadata/plate_{pi+1}_small.png']=buf.getvalue()
  cfg.append(pl);data[path]=xml(external)
  E.SubElement(rels,'{'+REL+'}Relationship',Target='/'+path,Id='rel-'+str(pi+1),Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
  entry.append({'name':s['name'],'label':s['label'],'object_id':oid,'positive_count':len(ids),'negative_count':1,'part_ids':ids,'negative_id':negid,'colors':list(dict.fromkeys(b['color']for b in s['bodies'])),'plate':pi+1,'logo_plane_print_z':0,'solid_dimensions_mm':[40,40,4]})
 cfg.append(assemble)
 data['3D/3dmodel.model']=xml(model);data['3D/_rels/3dmodel.model.rels']=xml(rels);data['Metadata/model_settings.config']=xml(cfg)
 data['Metadata/project_settings.config']=json.dumps(settings_new,ensure_ascii=False,indent=4).encode('utf-8')
 data['Metadata/filament_sequence.json']=json.dumps({f'plate_{i+1}':{'nozzle_sequence':[],'optimal_assignment':[],'sequence':[]}for i in range(len(ss))}).encode()
 cuts=E.Element('objects')
 for i in range(len(ss)):E.SubElement(E.SubElement(cuts,'object',id=str(i+1)),'cut_id',id='0',check_sum='1',connectors_cnt='0')
 data['Metadata/cut_information.xml']=xml(cuts)
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED)as z:
  for n,b in data.items():z.writestr(n,b)
 with zipfile.ZipFile(out)as z:assert z.testzip()is None
 return {'file':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'icons':entry,'filament_colors':colors,'material_source_indices':sel,'remapped_configuration_keys':changed,'all_other_print_parameters_identical':True}
manifest=[]
for s in specs:
 out=R/'individual'/(s['label']+'_40mm_负零件_Logo朝下.3mf');manifest.append(build([s],out));print('BUILT',s['label'],flush=True)
(R/'reports/project_manifest.json').write_text(json.dumps({'reference_project':str(SRC),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'files':manifest},ensure_ascii=False,indent=2))
print('ALL PROJECTS BUILT',len(manifest),flush=True)
