import {build} from 'vite';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
await build({configFile:false,publicDir:false,resolve:{alias:{'@':process.cwd()}},build:{ssr:resolve('tests/domain.test.ts'),outDir:'.test-build',rollupOptions:{output:{entryFileNames:'domain.test.mjs'}}}});
const result=spawnSync(process.execPath,['--test','.test-build/domain.test.mjs'],{stdio:'inherit'});
process.exitCode=result.status??1;
