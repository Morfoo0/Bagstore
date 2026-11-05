import {spawnSync} from 'node:child_process';
import {existsSync,mkdirSync} from 'node:fs';
import path from 'node:path';
const root=process.cwd();
const executable=path.join(root,'backend','.venv',process.platform==='win32'?'Scripts':'bin',process.platform==='win32'?'python.exe':'python');
function run(exe,args,env=process.env){const result=spawnSync(exe,args,{cwd:root,env,stdio:'inherit'});if(result.error)throw result.error;if(result.status!==0)process.exit(result.status??1);}
const action=process.argv[2]||'dev';
if(action==='setup'){
  const python=process.env.PYTHON||'python';const temp=path.join(root,'backend','.runtime','tmp');mkdirSync(temp,{recursive:true});
  if(!existsSync(executable))run(python,['-m','venv','--without-pip','backend/.venv']);
  run(python,['-m','pip','--python',executable,'install','-r','backend/requirements.lock.txt'],{...process.env,TEMP:temp,TMP:temp});
  run(executable,['backend/bootstrap.py']);
}else{
  if(!existsSync(executable))throw Error('Primero ejecuta npm run setup:backend.');
  if(action==='test')run(executable,['-m','pytest','backend/tests','-q']);
  else run(executable,['backend/run.py']);
}
