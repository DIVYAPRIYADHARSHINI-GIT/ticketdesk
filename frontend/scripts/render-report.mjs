import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {chromium} from '@playwright/test';
const root=path.resolve('..');
process.env.TMPDIR=path.join(root,'.cache/browser');fs.mkdirSync(process.env.TMPDIR,{recursive:true});
const text=fs.readFileSync(path.join(root,'FINAL_REPORT.md'),'utf8');
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const inline=s=>escape(s).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\[([^\]]+)\]\(([^)]+)\)/g,(_,label,url)=>'<a href="'+url+'">'+label+'</a>');
const chunks=[];let table=false,code=false,list=false;
for(const line of text.split('\n')){
 if(line.startsWith('```')){if(list){chunks.push('</ul>');list=false}code=!code;chunks.push(code?'<pre>':'</pre>');continue}
 if(code){chunks.push(escape(line)+'\n');continue}
 if(line.startsWith('|')){if(!table){chunks.push('<table>');table=true}if(/^\|[\s:|-]+\|$/.test(line))continue;chunks.push('<tr>'+line.slice(1,-1).split('|').map(c=>'<td>'+inline(c.trim())+'</td>').join('')+'</tr>');continue}
 if(table){chunks.push('</table>');table=false}
 if(line.startsWith('- ')){if(!list){chunks.push('<ul>');list=true}chunks.push('<li>'+inline(line.slice(2))+'</li>');continue}
 if(list){chunks.push('</ul>');list=false}
 const image=line.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
 if(image){const filename=path.resolve(root,image[2]);if(!filename.startsWith(root+path.sep))throw new Error('Image outside project rejected');chunks.push('<figure><img src="'+pathToFileURL(filename).href+'" alt="'+escape(image[1])+'"/><figcaption>'+escape(image[1])+'</figcaption></figure>');continue}
 const heading=line.match(/^(#{1,4}) (.*)/);
 if(heading){const level=heading[1].length;chunks.push(`<h${level}>${inline(heading[2])}</h${level}>`);continue}
 if(line.trim())chunks.push('<p>'+inline(line)+'</p>');
}
if(table)chunks.push('</table>');if(list)chunks.push('</ul>');
const html='<!doctype html><html lang="en"><head><meta charset="utf-8"><title>TicketDesk — Final report</title><style>body{font:11px/1.65 Arial,sans-serif;color:#202438;margin:0}h1{font-size:30px;letter-spacing:-1px;color:#5146d9;margin-bottom:8px}h2{font-size:18px;border-bottom:1px solid #dce0ee;padding-bottom:7px;margin-top:28px;break-after:avoid}h3{font-size:13px;margin-top:19px;break-after:avoid}p{margin:9px 0}a{color:#5146d9;text-decoration:none;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;font-size:9px;margin:14px 0}td{border:1px solid #dce0ee;padding:7px;vertical-align:top}tr:first-child{background:#efedff;font-weight:bold}tr{break-inside:avoid}code{font:9px monospace;background:#f0f1f6;padding:2px 4px;overflow-wrap:anywhere}pre{background:#f5f6fb;padding:14px;white-space:pre-wrap;font:9px/1.5 monospace}figure{margin:20px 0;break-inside:avoid;border:1px solid #dce0ee;border-radius:7px;padding:10px;text-align:center}figure img{display:block;max-width:100%;max-height:320px;object-fit:contain;margin:auto}figcaption{font-size:9px;color:#535b73;margin-top:9px}li{margin-bottom:5px}h1+p{font-size:12px;color:#61677e}</style></head><body>'+chunks.join('\n')+'</body></html>';
const htmlPath=path.join(root,'.cache/final-report.html');fs.writeFileSync(htmlPath,html);
const browser=await chromium.launch({channel:'chrome',headless:true});
try{const page=await browser.newPage();await page.goto(pathToFileURL(htmlPath).href);await page.evaluate(()=>Promise.all([...document.images].map(i=>i.decode())));await page.pdf({path:path.join(root,'FINAL_REPORT.pdf'),format:'A4',printBackground:true,margin:{top:'16mm',bottom:'18mm',left:'17mm',right:'17mm'},displayHeaderFooter:true,headerTemplate:'<span></span>',footerTemplate:'<div style="font-size:8px;width:100%;text-align:center;color:#61677e">TicketDesk · Verified build report · <span class="pageNumber"></span> / <span class="totalPages"></span></div>'});const pdf=fs.readFileSync(path.join(root,'FINAL_REPORT.pdf'));const pages=(pdf.toString('latin1').match(/\/Type\s*\/Page\b/g)||[]).length;fs.writeFileSync(path.join(root,'evidence/pdf-verification.json'),JSON.stringify({signature:pdf.subarray(0,5).toString(),bytes:pdf.length,pages},null,2));console.log(`Report PDF exported: ${pages} pages, ${pdf.length} bytes.`)}finally{await browser.close()}
