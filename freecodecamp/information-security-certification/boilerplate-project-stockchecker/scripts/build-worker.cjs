'use strict';

const fs = require('node:fs');
const path = require('node:path');
const project = path.resolve(__dirname, '..');
const assets = path.join(project, '.deploy', 'assets');
if (!assets.startsWith(project + path.sep)) throw new Error('Unexpected output directory');
fs.rmSync(assets, { recursive: true, force: true });
fs.mkdirSync(assets, { recursive: true });
fs.copyFileSync(path.join(project, 'views', 'index.html'), path.join(assets, 'index.html'));
fs.cpSync(path.join(project, 'public'), path.join(assets, 'public'), { recursive: true });
console.log('Prepared public page and assets.');
