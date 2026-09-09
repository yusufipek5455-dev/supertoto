const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('>>> [SüperToto Build] Running next build...');
execSync('npx next build', { stdio: 'inherit' });

const rootNext = path.resolve('.next');
const frontendNext = path.resolve('frontend', '.next');

if (fs.existsSync(rootNext)) {
  fs.mkdirSync(path.resolve('frontend'), { recursive: true });
  fs.cpSync(rootNext, frontendNext, { recursive: true });
  console.log('>>> [SüperToto Build] Mirrored .next -> frontend/.next');
}

if (fs.existsSync(frontendNext) && !fs.existsSync(rootNext)) {
  fs.cpSync(frontendNext, rootNext, { recursive: true });
  console.log('>>> [SüperToto Build] Mirrored frontend/.next -> .next');
}
