import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Badge, Empty, ErrorBox, Loading, PageHead, Stat, Logo } from './components';
import { duration, fileError, initials } from './api';

describe('readable states and semantics',()=>{
 it.each(['On track','At risk','Breached','Resolved','Waiting for requester','Urgent'])('badge explains %s without colour alone',value=>{render(<Badge value={value}/>);expect(screen.getByText(value)).toBeVisible()});
 it('loading announces its state',()=>{render(<Loading/>);expect(screen.getByRole('status')).toHaveTextContent('Getting your workspace ready')});
 it('errors are announced',()=>{render(<ErrorBox message="A test connection failed"/>);expect(screen.getByRole('alert')).toHaveTextContent('A test connection failed')});
 it('empty states have a heading',()=>{render(<Empty title="No results"/>);expect(screen.getByRole('heading',{name:'No results'})).toBeVisible()});
 it('page uses a single top heading',()=>{render(<PageHead title="My tickets" description="Your requests"/>);expect(screen.getByRole('heading',{level:1})).toHaveTextContent('My tickets')});
 it('stat shows a zero rather than missing data',()=>{render(<Stat label="Total" value={0}/>);expect(screen.getByText('0')).toBeVisible()});
 it('original wordmark names the product',()=>{render(<Logo/>);expect(screen.getByText('TicketDesk')).toBeVisible()});
});
describe('formatting and upload prechecks',()=>{
 it.each([[null,'—'],[120,'2 min'],[3600,'1.0 h'],[172800,'2.0 days']] as const)('formats %s', (value,result)=>expect(duration(value)).toBe(result));
 it('uses at most two initials',()=>expect(initials('Avery Test Lane')).toBe('AT'));
 it.each([['test.png','image/png'],['test.jpg','image/jpeg'],['test.jpeg','image/jpeg'],['test.webp','image/webp'],['test.pdf','application/pdf']])('accepts matching %s', (name,type)=>expect(fileError(new File(['test'],name,{type}))).toBeNull());
 it('rejects empty file',()=>expect(fileError(new File([],'test.pdf',{type:'application/pdf'}))).toContain('non-empty'));
 it('rejects oversized file',()=>expect(fileError(new File([new Uint8Array(1048577)],'test.pdf',{type:'application/pdf'}))).toContain('1 MB'));
 it('rejects mismatched extension',()=>expect(fileError(new File(['x'],'test.png',{type:'application/pdf'}))).toContain('matching'));
 it('rejects SVG',()=>expect(fileError(new File(['<svg/>'],'test.svg',{type:'image/svg+xml'}))).toContain('matching'));
});
