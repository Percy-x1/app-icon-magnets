import json,urllib.request,sys,os
URL=os.environ.get("FUSION_MCP_URL","http://127.0.0.1:27182/mcp")
SESSION=None
def call(name,args):
 global SESSION
 init={"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"codex","version":"1.0"}}}
 req=urllib.request.Request(URL,json.dumps(init).encode(),headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"})
 with urllib.request.urlopen(req,timeout=20)as r:
  SESSION=r.headers['MCP-Session-Id'];r.read()
 req=urllib.request.Request(URL,json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"}).encode(),headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream","MCP-Session-Id":SESSION})
 with urllib.request.urlopen(req,timeout=20)as r:r.read()
 data=json.dumps({"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":name,"arguments":args}}).encode()
 req=urllib.request.Request(URL,data,headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream","MCP-Session-Id":SESSION})
 with urllib.request.urlopen(req,timeout=240) as r: return json.load(r)
if __name__=="__main__":
 if sys.argv[1]=="script":
  args={"featureType":"script","object":{"script":open(sys.argv[2],encoding="utf-8").read(),"readOnly":"--read-only" in sys.argv}}
  result=call("fusion_mcp_execute",args)
 else: result=call(sys.argv[1],json.loads(sys.argv[2]))
 print(json.dumps(result,ensure_ascii=False))
