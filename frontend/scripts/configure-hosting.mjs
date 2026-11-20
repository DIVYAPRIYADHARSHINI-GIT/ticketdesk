// Run BEFORE creating a frontend deployment. This writes only public routing configuration.
import fs from 'node:fs';
const origin=process.env.API_ORIGIN;
if(!origin)throw new Error('API_ORIGIN is required: the HTTPS origin of the deployed TicketDesk backend.');
const url=new URL(origin);
if(url.protocol!=='https:'||url.username||url.password||url.pathname!=='/'||url.search||url.hash)throw new Error('API_ORIGIN must be a plain HTTPS origin with no credentials, path or query.');
const config={buildCommand:'npm run build',outputDirectory:'dist',framework:'vite',rewrites:[{source:'/api/:path*',destination:url.origin+'/api/:path*'},{source:'/:path*',destination:'/index.html'}],headers:[{source:'/:path*',headers:[{key:'X-Content-Type-Options',value:'nosniff'},{key:'Referrer-Policy',value:'strict-origin-when-cross-origin'},{key:'X-Frame-Options',value:'DENY'},{key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'}]}]};
fs.writeFileSync('vercel.json',JSON.stringify(config,null,2)+'\n');
console.log('Frontend same-origin API rewrite configured (no secrets written).');
