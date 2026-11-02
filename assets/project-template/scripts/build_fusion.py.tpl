import adsk.core,adsk.fusion,json,math
from pathlib import Path
ROOT=Path(__PROJECT_ROOT__)
def run(_context:str):
 app=adsk.core.Application.get()
 doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);doc.name='App_Icon_Magnets_iOS60_40mm'
 d=adsk.fusion.Design.cast(app.activeProduct);d.designType=adsk.fusion.DesignTypes.ParametricDesignType;root=d.rootComponent
 d.unitsManager.distanceDisplayUnits=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
 for name,value,desc in [('TileWidth','40 mm','Overall tile width and height'),('CornerRadius','9 mm','Nominal radius of the iOS60 outline'),('TotalThickness','4 mm','Total thickness, flat top and back'),('InlayDepth','1 mm','Flush color inlay depth'),('BackingThickness','3 mm','Solid backing below the inlays')]:
  if not d.userParameters.itemByName(name):d.userParameters.add(name,adsk.core.ValueInput.createByString(value),'mm',desc)
 outline=json.loads((ROOT/'assets/ios60_outline.json').read_text(encoding='utf-8'))
 d.userParameters.add('CornerSmoothingPercent',adsk.core.ValueInput.createByReal(60),'','Reference smoothing used to generate the outline')
 specs=json.loads((ROOT/'assets/design_vectors.json').read_text(encoding='utf-8'))
 specs.sort(key=lambda s:0 if s['name'] in ['Taobao','MeipingMeiwu']else 1)
 appearance={}
 template=app.materialLibraries.item(0).appearances.itemById('Prism-374')
 def mat(hex):
  if hex not in appearance:
   a=d.appearances.addByCopy(template,'PLA_'+hex[1:]);rgb=[int(hex[i:i+2],16)for i in (1,3,5)]
   for prop in ['opaque_albedo','surface_albedo']:
    a.appearanceProperties.itemById(prop).value=adsk.core.Color.create(*rgb,255)
   appearance[hex]=a
  return appearance[hex]
 def p(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
 def ext(c,profiles,expr,name):
  obj=adsk.core.ObjectCollection.create()
  for pr in profiles:obj.add(pr)
  inp=c.features.extrudeFeatures.createInput(obj,adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
  inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(expr)),adsk.fusion.ExtentDirections.PositiveExtentDirection)
  f=c.features.extrudeFeatures.add(inp);f.name=name;return f
 report=json.loads((ROOT/'reports/fusion_validation.json').read_text(encoding='utf-8')) if (ROOT/'reports/fusion_validation.json').exists() else []
 specs=[s for s in specs if s['name']not in [x['name']for x in report]]
 errors=[]
 for spec in specs:
  try:
   occ=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());c=occ.component;c.name=spec['name']+'_40mm'
   s=c.sketches.add(c.xYConstructionPlane);s.name='01 iOS smooth square 40mm R9 smoothing60';s.isComputeDeferred=True
   for seg in outline['outline']:
    pts=[p(*xy)for xy in seg['points']]
    if seg['type']=='line':s.sketchCurves.sketchLines.addByTwoPoints(pts[0],pts[-1])
    elif seg['type']=='arc':s.sketchCurves.sketchArcs.addByThreePoints(pts[0],pts[1],pts[2])
    else:
     nurbs=adsk.core.NurbsCurve3D.createNonRational(pts,3,[0.,0.,0.,0.,1.,1.,1.,1.],False)
     s.sketchCurves.sketchFixedSplines.addByNurbsCurve(nurbs)
   s.isComputeDeferred=False
   assert s.profiles.count==1
   base=ext(c,[s.profiles.item(0)],'TotalThickness','02 Solid tile 4mm').bodies.item(0)
   base.name='Base_'+spec['base_color'][1:];base.appearance=mat(spec['base_color']);s.isVisible=False
   planeIn=c.constructionPlanes.createInput();planeIn.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString('BackingThickness'))
   plane=c.constructionPlanes.add(planeIn);plane.name='Inlay floor Z3mm'
   colors={base.name:spec['base_color']}
   for part in spec['parts']:
    sk=c.sketches.add(plane);sk.name='Vector '+part['name'];sk.isComputeDeferred=True
    for loop in part['loops']:
     for seg in loop:
      pts=[p(*xy)for xy in seg['points']]
      if pts[0].distanceTo(pts[-1])<1e-7 and seg['type']=='line':continue
      if seg['type']=='line':sk.sketchCurves.sketchLines.addByTwoPoints(pts[0],pts[-1])
      else:
       nurbs=adsk.core.NurbsCurve3D.createNonRational(pts,3,[0.,0.,0.,0.,1.,1.,1.,1.],False)
       sk.sketchCurves.sketchFixedSplines.addByNurbsCurve(nurbs)
    sk.isComputeDeferred=False
    # The intended filled profile(s) are the largest regions; holes remain empty.
    candidates=sorted(list(sk.profiles),key=lambda x:x.areaProperties().area,reverse=True)
    if not spec.get('strict_svg') and (not candidates or min(abs(x.areaProperties().area*100-part['area_mm2'])for x in candidates)>max(.2,part['area_mm2']*.003)):
     sk.deleteMe();sk=c.sketches.add(plane);sk.name='Clean contour '+part['name'];sk.isComputeDeferred=True
     for loop in part['fallback_loops']:
      for seg in loop:sk.sketchCurves.sketchLines.addByTwoPoints(p(*seg['points'][0]),p(*seg['points'][1]))
     sk.isComputeDeferred=False
     candidates=list(sk.profiles)
    assert candidates,(spec['name'],part['name'],'no closed profiles')
    selected=[min(candidates,key=lambda x:abs(x.areaProperties().area*100-part['area_mm2']))];area=sum(x.areaProperties().area*100 for x in selected)
    assert abs(area-part['area_mm2'])<max(.2,part['area_mm2']*.003),(spec['name'],part['name'],area,part['area_mm2'],[x.areaProperties().area*100 for x in candidates])
    f=ext(c,selected,'InlayDepth','Flush inlay '+part['name'])
    for i,b in enumerate(f.bodies):
     b.name=part['name']+('_'+str(i+1)if f.bodies.count>1 else '');b.appearance=mat(part['color']);colors[b.name]=part['color']
    sk.isVisible=False
    if part.get('clip_to_tile'):
     target=f.bodies.item(0)
     stencil=ext(c,[s.profiles.item(0)],'TotalThickness','Tile trimming boundary').bodies.item(0)
     trimtools=adsk.core.ObjectCollection.create();trimtools.add(stencil)
     ti=c.features.combineFeatures.createInput(target,trimtools)
     ti.operation=adsk.fusion.FeatureOperations.IntersectFeatureOperation;ti.isKeepToolBodies=False
     tr=c.features.combineFeatures.add(ti);tr.name='Trim '+part['name']+' to smooth tile'
     for trimmed in tr.bodies:trimmed.appearance=mat(part['color'])
   if spec.get('join_color'):
    same=[b for b in c.bRepBodies if b!=base and b.appearance.name=='PLA_'+spec['join_color'][1:]]
    joined_tools=adsk.core.ObjectCollection.create()
    for b in same[1:]:joined_tools.add(b)
    ji=c.features.combineFeatures.createInput(same[0],joined_tools);ji.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation;ji.isKeepToolBodies=False
    joined=c.features.combineFeatures.add(ji);joined.name='Union overlapping green SVG paths'
    for b in joined.bodies:b.appearance=mat(spec['join_color'])
   if spec.get('union_inlays'):

    inlays=[b for b in c.bRepBodies if b!=base]
    toolset=adsk.core.ObjectCollection.create()
    for b in inlays[1:]:toolset.add(b)
    ui=c.features.combineFeatures.createInput(inlays[0],toolset);ui.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation;ui.isKeepToolBodies=False
    c.features.combineFeatures.add(ui).name='Join continuous mark with 0.02mm contact bridges'
   # Resolve SVG painter-order overlaps using exact BRep cuts. All final
   # color volumes are disjoint and share the Z4 plane.
   bm=adsk.fusion.TemporaryBRepManager.get()
   inlays=[b for b in c.bRepBodies if b!=base]
   for ii,target in enumerate(inlays[:-1]):
    cutters=adsk.core.ObjectCollection.create()
    for other in inlays[ii+1:]:
     if not target.isValid or not other.isValid:continue
     tmp=bm.copy(target);tool=bm.copy(other)
     ok=bm.booleanOperation(tmp,tool,adsk.fusion.BooleanTypes.IntersectionBooleanType)
     if ok and tmp.volume>1e-10:cutters.add(other)
    if cutters.count:
     target_color=target.appearance
     ci=c.features.combineFeatures.createInput(target,cutters);ci.operation=adsk.fusion.FeatureOperations.CutFeatureOperation;ci.isKeepToolBodies=True
     resolved=c.features.combineFeatures.add(ci);resolved.name='Separate overlapping SVG color regions'
     # Keep cutter appearances; Fusion includes retained tools in feature.bodies.
     if target.isValid:target.appearance=target_color
   tools=adsk.core.ObjectCollection.create()
   for body in c.bRepBodies:
    if body!=base:tools.add(body)
   ci=c.features.combineFeatures.createInput(base,tools);ci.operation=adsk.fusion.FeatureOperations.CutFeatureOperation;ci.isKeepToolBodies=True
   cut=c.features.combineFeatures.add(ci);cut.name='Flush inlay pockets - retain color bodies'
   plane.isLightBulbOn=False
   # Validate and export each component in its own local coordinate system.
   dims=[(max(getattr(b.boundingBox.maxPoint,a)for b in c.bRepBodies)-min(getattr(b.boundingBox.minPoint,a)for b in c.bRepBodies))*10 for a in 'xyz']
   assert all(abs(x-y)<.001 for x,y in zip(dims,[40,40,4])),(spec['name'],dims)
   volume=sum(b.volume*1000 for b in c.bRepBodies)
   assert abs(volume-outline['area_mm2']*4)<.01,(spec['name'],volume,outline['area_mm2']*4)
   bodydata=[]
   (ROOT/'stl'/spec['name']).mkdir(exist_ok=True)
   for bi,b in enumerate(c.bRepBodies):
    assert b.isSolid
    color='#'+b.appearance.name.split('PLA_')[-1][:6]
    assert color in [spec['base_color']]+[p['color'] for p in spec['parts']],(b.name,b.appearance.name)
    b.name=('Base_' if b==base else 'Inlay_')+color[1:]+'_'+str(bi+1)
    colors[b.name]=color
    stl=d.exportManager.createSTLExportOptions(b,str(ROOT/'stl'/spec['name']/(b.name+'.stl')))
    stl.isBinaryFormat=True;stl.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    stl.surfaceDeviation=.0003;stl.normalDeviation=math.radians(1);stl.sendToPrintUtility=False
    assert d.exportManager.execute(stl)
    bb=b.boundingBox
    bodydata.append({'name':b.name,'color':colors[b.name],'volume_mm3':b.volume*1000,'bounds_mm':[[getattr(bb.minPoint,a)*10,getattr(bb.maxPoint,a)*10]for a in 'xyz'],'faces':b.faces.count})
   assert set(b['color']for b in bodydata)==set([spec['base_color']]+[p['color']for p in spec['parts']]),('Missing palette',spec['name'])
   health=[{'name':f.name,'state':int(f.healthState),'message':f.errorOrWarningMessage}for f in c.features]
   assert all(x['state']==0 for x in health),health
   assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(ROOT/'fusion'/(spec['name']+'_40mm.f3d')),c))
   assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(str(ROOT/'fusion'/(spec['name']+'_40mm.step')),c))
   report.append({'name':spec['name'],'dimensions_mm':dims,'bodies':bodydata,'features':health,'position_mm':spec['center'],'label':spec['label']})
   (ROOT/'reports/fusion_validation.json').write_text(json.dumps(report,indent=2))
   print('Finished',spec['name'],dims,'bodies',c.bRepBodies.count)
  except Exception as error:
   import traceback
   errors.append({'name':spec['name'],'error':str(error),'traceback':traceback.format_exc()})
   (ROOT/'reports/fusion_errors.json').write_text(json.dumps(errors,indent=2))
   print('FAILED',spec['name'],str(error),flush=True)
 print('COMPLETE',len(report),'ERRORS',len(errors),flush=True)
