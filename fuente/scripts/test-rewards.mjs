import {build} from 'vite';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
await build({configFile:false,publicDir:false,resolve:{alias:{'@':process.cwd()}},build:{ssr:resolve('tests/rewards.test.ts'),outDir:'.test-rewards',rollupOptions:{output:{entryFileNames:'rewards.test.mjs'}}}});
const result=spawnSync(process.execPath,['--test','.test-rewards/rewards.test.mjs'],{stdio:'inherit'});
process.exitCode=result.status??1;
