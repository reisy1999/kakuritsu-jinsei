import sys
t=open(sys.argv[1],encoding="utf-8").read()
js=t[t.index('<script>')+8:t.rindex('</script>')].rstrip()
assert js.endswith('newLife();'); js=js[:-10]
stub='''const el=()=>({innerHTML:"",textContent:"",hidden:false,classList:{toggle(){},add(){}},onclick:null,prepend(){},appendChild(){},querySelectorAll(){return[]},scrollIntoView(){}});
const els={};globalThis.document={getElementById:id=>els[id]||(els[id]=el()),createElement:()=>el()};
globalThis.matchMedia=()=>({matches:true});globalThis.window={scrollTo(){}};
'''
open('sim.js','w').write(stub+js+open('harness.js').read())
