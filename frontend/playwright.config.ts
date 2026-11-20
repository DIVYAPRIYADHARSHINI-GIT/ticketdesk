import { defineConfig } from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
process.env.TMPDIR=path.resolve('../.cache/browser');
fs.mkdirSync(process.env.TMPDIR,{recursive:true});
export default defineConfig({testDir:'./tests',fullyParallel:false,workers:1,retries:0,timeout:45000,expect:{timeout:10000},reporter:[['list'],['json',{outputFile:`../evidence/${process.env.TD_RUN||'local-browser'}-results.json`}]],use:{baseURL:'http://localhost:5174',channel:'chrome',viewport:{width:1440,height:1000},trace:'off',screenshot:'off',video:'off'},webServer:[{command:'cd ../backend && DATABASE_URL=sqlite:///./e2e.db ../.venv/bin/python -m alembic upgrade head && DATABASE_URL=sqlite:///./e2e.db ../.venv/bin/python -m app.seed && DATABASE_URL=sqlite:///./e2e.db DEMO_ENABLED=true FRONTEND_ORIGIN=http://localhost:5174 ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --no-access-log',url:'http://127.0.0.1:8001/health',reuseExistingServer:false,timeout:60000},{command:'API_ORIGIN=http://127.0.0.1:8001 npm run preview -- --port 5174',url:'http://localhost:5174',reuseExistingServer:false,timeout:60000}]});
