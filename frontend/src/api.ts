import type { User } from './types';
let csrf = '';
export class APIError extends Error { constructor(message:string,public status:number){super(message)} }
export async function api<T>(path:string,method='GET',body?:unknown):Promise<T>{
  const form=body instanceof FormData;
  const response=await fetch('/api'+path,{method,credentials:'same-origin',headers:{...(form?{}:{'Content-Type':'application/json'}),...(method==='GET'?{}:{'X-CSRF-Token':csrf})},body:body===undefined?undefined:form?body:JSON.stringify(body)});
  const data=await response.json().catch(()=>({detail:'The server could not complete your request.'}));
  if(!response.ok)throw new APIError(typeof data.detail==='string'?data.detail:'Please check the supplied fields.',response.status);
  if(data.csrf)csrf=data.csrf;
  return data as T;
}
export async function bootstrap(){return api<{csrf:string;user:User|null}>('/auth/csrf')}
export function formatDate(value:number){return new Date(value*1000).toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}
export function duration(seconds:number|null){if(seconds===null)return '—'; if(seconds<3600)return `${Math.round(seconds/60)} min`; if(seconds<86400)return `${(seconds/3600).toFixed(1)} h`; return `${(seconds/86400).toFixed(1)} days`}
export function initials(name:string){return name.split(' ').map(p=>p[0]).slice(0,2).join('').toUpperCase()}
export function fileError(file:File):string|null{if(file.size===0||file.size>1048576)return 'Choose a non-empty file of at most 1 MB.';const matches:Record<string,string>={png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg',webp:'image/webp',pdf:'application/pdf'};return matches[file.name.split('.').pop()?.toLowerCase()||'']===file.type?null:'Choose a PNG, JPEG, WebP or PDF with a matching file type.'}
