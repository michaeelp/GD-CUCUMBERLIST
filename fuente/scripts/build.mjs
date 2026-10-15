import {build} from 'vite';
import react from '@vitejs/plugin-react';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {mkdir,symlink,lstat,copyFile,rm,readdir} from 'node:fs/promises';
const source=resolve(dirname(fileURLToPath(import.meta.url)),'..'),root=resolve(source,'..'),out=resolve(root,'../cucumber-build-output');
await mkdir(resolve(source,'public'),{recursive:true});
try{await lstat(resolve(source,'public/assets'));}catch{await symlink(resolve(root,'assets'),resolve(source,'public/assets'),'junction');}
const result=await build({configFile:false,base:'./',root:source,publicDir:resolve(source,'public'),resolve:{alias:{'@':source}},plugins:[react()],build:{outDir:out,emptyOutDir:true,rollupOptions:{input:resolve(source,'index.html')}}});
const builds=Array.isArray(result)?result:[result];
const current=new Set(builds.flatMap(b=>(b.output||[]).map(entry=>entry.fileName)));
for(const name of await readdir(resolve(root,'assets')))if(/\.(?:js|css)$/.test(name)&&!current.has('assets/'+name))await rm(resolve(root,'assets',name));
for(const b of builds)for(const entry of b.output||[])if(entry.fileName.startsWith('assets/'))await copyFile(resolve(out,entry.fileName),resolve(root,entry.fileName));
await copyFile(resolve(out,'index.html'),resolve(root,'index.html'));
await rm(out,{recursive:true,force:true});
console.log('Carpeta de GitHub Pages actualizada.');
