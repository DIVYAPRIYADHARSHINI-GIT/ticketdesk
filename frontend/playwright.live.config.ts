import { defineConfig } from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
process.env.TMPDIR=path.resolve('../.cache/browser');fs.mkdirSync(process.env.TMPDIR,{recursive:true});
export default defineConfig({testDir:'./live-tests',workers:1,retries:0,timeout:90000,expect:{timeout:30000},reporter:[['list'],['json',{outputFile:`../evidence/${process.env.TD_RUN||'live'}-results.json`}]],use:{baseURL:process.env.LIVE_URL||'https://ticketdesk-frontend-psi.vercel.app',channel:'chrome',viewport:{width:1440,height:1000},trace:'off',video:'off',screenshot:'off',launchOptions:{args:['--test-third-party-cookie-phaseout']}}});
