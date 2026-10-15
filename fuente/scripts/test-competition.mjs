import {build} from 'vite';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
await build({configFile:false,publicDir:false,resolve:{alias:{'@':process.cwd()}},build:{ssr:resolve('tests/competition.test.ts'),outDir:'.test-competition',rollupOptions:{output:{entryFileNames:'competition.test.mjs'}}}});
const result=spawnSync(process.execPath,['--test','.test-competition/competition.test.mjs'],{stdio:'inherit'});
process.exitCode=result.status??1;
