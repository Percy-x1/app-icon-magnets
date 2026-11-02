from pathlib import Path
import json,math
import numpy as np
from svgpathtools import Document,Line,CubicBezier,QuadraticBezier,Arc
from shapely.geometry import Polygon
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parent.parent

def make(file,width,color,name,indices=None,fixed=False,frame=None):
 paths=Document(str(ROOT/'assets'/file)).paths()
 if indices is not None:paths=[paths[i]for i in indices]
 paths=[s for path in paths for s in path.continuous_subpaths()]
 boxes=[p.bbox()for p in paths];xmin=min(b[0]for b in boxes);xmax=max(b[1]for b in boxes);ymin=min(b[2]for b in boxes);ymax=max(b[3]for b in boxes)
 if frame is not None:xmin,xmax,ymin,ymax=frame
 scale=width/(xmax-xmin);cx=(xmin+xmax)/2;cy=(ymin+ymax)/2
 if fixed:scale=40/1024;cx=cy=512
 def pt(z):return [(z.real-cx)*scale,-(z.imag-cy)*scale]
 loops=[];polys=[]
 for path in paths:
  segs=[];points=[]
  for seg in path:
   if isinstance(seg,Arc):parts=list(seg.as_cubic_curves(max(1,math.ceil(abs(seg.delta)/30))))
   elif isinstance(seg,QuadraticBezier):parts=[CubicBezier(seg.start,seg.start+(seg.control-seg.start)*2/3,seg.end+(seg.control-seg.end)*2/3,seg.end)]
   else:parts=[seg]
   for s in parts:
    if abs(s.end-s.start)*scale<.000001 and isinstance(s,Line):continue
    if isinstance(s,Line):segs.append({'type':'line','points':[pt(s.start),pt(s.end)]})
    else:segs.append({'type':'cubic','points':[pt(s.start),pt(s.control1),pt(s.control2),pt(s.end)]})
    for t in np.linspace(0,1,100,endpoint=False):points.append(pt(s.point(t)))
  if not segs:continue
  if np.linalg.norm(np.array(segs[-1]['points'][-1])-np.array(segs[0]['points'][0]))>.000001:segs.append({'type':'line','points':[segs[-1]['points'][-1],segs[0]['points'][0]]})
  else:segs[-1]['points'][-1]=segs[0]['points'][0]
  poly=Polygon(points)
  if not poly.is_valid:
   repaired=poly.buffer(0)
   if repaired.geom_type=='MultiPolygon':
    largest=max(repaired.geoms,key=lambda q:q.area)
    assert repaired.area-largest.area<1e-8,(file,'nontrivial extra SVG region')
    repaired=largest
   assert repaired.geom_type=='Polygon' and len(repaired.interiors)==0,(file,len(polys),'invalid SVG contour')
   assert abs(repaired.area-poly.area)<.005,(file,'significant source self intersection')
   poly=repaired
  if poly.area<.01:continue
  loops.append(segs);polys.append(poly)
 parents=[]
 for i,p in enumerate(polys):
  candidates=[j for j,q in enumerate(polys)if i!=j and q.area>p.area and q.contains(p.representative_point())]
  parents.append(min(candidates,key=lambda j:polys[j].area)if candidates else None)
 def depth(i):return 0 if parents[i]is None else 1+depth(parents[i])
 parts=[]
 for i,p in enumerate(polys):
  if depth(i)%2:continue
  holes=[j for j in range(len(polys))if parents[j]==i]
  geom=p
  for j in holes:geom=geom.difference(polys[j])
  simple=geom.simplify(.004,preserve_topology=True)
  fallback=[]
  for ring in [simple.exterior]+list(simple.interiors):
   coords=list(ring.coords);fallback.append([{'type':'line','points':[list(a),list(b)]}for a,b in zip(coords[:-1],coords[1:])])
  parts.append({'fallback_loops':fallback,'name':name+'_'+str(len(parts)+1),'color':color,'loops':[loops[i]]+[loops[j]for j in holes],'area_mm2':geom.area,'bounds_mm':list(geom.bounds),'source':file,'clip_to_tile':fixed})
 return parts
