#!/usr/bin/env python3
"""Copy a new local project scaffold; never replace an existing directory."""
import argparse,json,shutil,zipfile,hashlib
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 skill=Path(__file__).resolve().parents[1];out=a.output.expanduser().resolve()
 if out.exists():p.error('Output already exists; choose a new project directory.')
 seed=skill/'assets/print-template.3mf';manifest=json.loads((skill/'assets/template-manifest.json').read_text())
 if hashlib.sha256(seed.read_bytes()).hexdigest()!=manifest['sha256']:p.error('Bundled reference seed hash mismatch.')
 with zipfile.ZipFile(seed)as z:
  if z.testzip():p.error('Invalid bundled reference archive.')
 out.mkdir(parents=True)
 for n in ['assets','scripts','reports','stl','fusion','individual']:(out/n).mkdir()
 for f in (skill/'assets/project-template/scripts').iterdir():
  if f.suffix=='.tpl':
   text=f.read_text(encoding='utf-8').replace('__PROJECT_ROOT__',json.dumps(str(out),ensure_ascii=True))
   (out/'scripts'/f.stem).write_text(text,encoding='utf-8')
  else:shutil.copy2(f,out/'scripts'/f.name)
 for n in ['ios60_outline.json','print-template.3mf']:shutil.copy2(skill/'assets'/n,out/'assets'/n)
 shutil.copy2(skill/'assets/project-template/requirements.txt',out/'requirements.txt')
 print(json.dumps({'project':str(out),'next':'Add original SVG assets, source provenance, and assets/design_vectors.json; see references/scripts.md.'},ensure_ascii=False))
if __name__=='__main__':main()
