import {build} from 'vite';
import react from '@vitejs/plugin-react';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
await build({configFile:false,publicDir:false,plugins:[react()],resolve:{alias:{'@':process.cwd()}},build:{ssr:resolve('tests/render.test.tsx'),outDir:'.test-render',rollupOptions:{output:{entryFileNames:'render.test.mjs'}}}});
const result=spawnSync(process.execPath,['.test-render/render.test.mjs'],{stdio:'inherit'});
process.exitCode=result.status??1;
