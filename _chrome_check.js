const fs = require('fs');
const path = require('path');
const appDir = process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application';
const files = fs.readdirSync(appDir);
const exeFiles = files.filter(f => f.endsWith('.exe'));
console.log('Chrome executables found:', exeFiles.length);
exeFiles.forEach(f => {
  const fullPath = path.join(appDir, f);
  const stat = fs.statSync(fullPath);
  console.log(f, '- size:', (stat.size / 1024 / 1024).toFixed(2), 'MB');
});
