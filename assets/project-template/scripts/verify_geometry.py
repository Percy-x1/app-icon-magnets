from pathlib import Path
import json,trimesh,numpy as np
R=Path(__file__).resolve().parent.parent
specs=json.loads((R/'reports/fusion_validation.json').read_text());reports=[]
for s in specs:
 meshes=[]
 for b in s['bodies']:
  p=R/'stl'/s['name']/(b['name']+'.stl');m=trimesh.load_mesh(p,process=True)
  assert m.is_watertight and m.is_winding_consistent and m.volume>0,(s['name'],b['name'])
  assert abs(m.volume-b['volume_mm3'])<max(.05,b['volume_mm3']*.0002),(s['name'],'volume')
  assert all(abs(x-y)<.004 for x,y in zip(m.bounds.flatten(),np.array(b['bounds_mm']).T.flatten())),(s['name'],'bbox')
  if b['name'].startswith('Inlay'):assert np.allclose(m.bounds[:,2],[3,4],atol=1e-5)
  meshes.append(m)
 bounds=np.array([m.bounds for m in meshes]);dims=bounds[:,1].max(axis=0)-bounds[:,0].min(axis=0);assert np.allclose(dims,[40,40,4],atol=1e-5)
 reports.append({'name':s['name'],'dimensions_mm':dims.tolist(),'positive_parts':len(meshes),'all_meshes_watertight':True,'inlays_at_z_mm':[3,4],'surface_flush':True,'filament_colors':list(dict.fromkeys(b['color']for b in s['bodies']))})
 print(s['name'],'PASS',len(meshes),flush=True)
assert len(reports)==len(specs)
(R/'reports/mesh_validation.json').write_text(json.dumps(reports,indent=2))
