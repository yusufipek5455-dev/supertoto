const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('>>> [SüperToto Build] Running next build...');
execSync('npx next build', { stdio: 'inherit' });

const rootDir = path.resolve(__dirname, '..');
const frontendDir = path.join(rootDir, 'frontend');

if (!fs.existsSync(frontendDir)) {
  fs.mkdirSync(frontendDir, { recursive: true });
}

// 1. Mirror .next -> frontend/.next
const rootNext = path.join(rootDir, '.next');
const frontendNext = path.join(frontendDir, '.next');
if (fs.existsSync(rootNext)) {
  fs.cpSync(rootNext, frontendNext, { recursive: true });
  console.log('>>> [SüperToto Build] Mirrored .next -> frontend/.next');
}

// 2. Mirror package.json -> frontend/package.json
const rootPkg = path.join(rootDir, 'package.json');
const frontendPkg = path.join(frontendDir, 'package.json');
if (fs.existsSync(rootPkg)) {
  fs.copyFileSync(rootPkg, frontendPkg);
  console.log('>>> [SüperToto Build] Copied package.json -> frontend/package.json');
}

// 3. Mirror next.config.js -> frontend/next.config.js
const rootNextConfig = path.join(rootDir, 'next.config.js');
const frontendNextConfig = path.join(frontendDir, 'next.config.js');
if (fs.existsSync(rootNextConfig)) {
  fs.copyFileSync(rootNextConfig, frontendNextConfig);
  console.log('>>> [SüperToto Build] Copied next.config.js -> frontend/next.config.js');
}

// 4. Link node_modules -> frontend/node_modules for trace resolution
const rootNodeModules = path.join(rootDir, 'node_modules');
const frontendNodeModules = path.join(frontendDir, 'node_modules');
if (fs.existsSync(rootNodeModules) && !fs.existsSync(frontendNodeModules)) {
  try {
    fs.symlinkSync(rootNodeModules, frontendNodeModules, 'junction');
    console.log('>>> [SüperToto Build] Linked node_modules -> frontend/node_modules');
  } catch (err) {
    console.warn('>>> [SüperToto Build] Could not create node_modules symlink, attempting cp:', err.message);
    try {
      fs.cpSync(rootNodeModules, frontendNodeModules, { recursive: true });
    } catch (e2) {
      console.warn('>>> [SüperToto Build] Copy node_modules failed:', e2.message);
    }
  }
}
