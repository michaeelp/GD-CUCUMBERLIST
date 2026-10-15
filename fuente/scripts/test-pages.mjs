import {build} from 'vite';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
await build({configFile:false,publicDir:false,resolve:{alias:{'@':process.cwd()}},build:{ssr:resolve('tests/pages.test.ts'),outDir:'.test-pages',rollupOptions:{output:{entryFileNames:'pages.test.mjs'}}}});
const result=spawnSync(process.execPath,['--test','.test-pages/pages.test.mjs'],{stdio:'inherit'});
process.exitCode=result.status??1;
