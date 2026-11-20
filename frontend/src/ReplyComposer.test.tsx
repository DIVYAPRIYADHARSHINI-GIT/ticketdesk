import { useState } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ReplyComposer } from './ReplyComposer';
const replies=[{id:1,title:'TEST saved reply',body:'TEST helpful reply body.'}];
function Harness({busy=false,staff=true}:{busy?:boolean;staff?:boolean}){const [body,setBody]=useState('');const [internal,setInternal]=useState(false);return <ReplyComposer staff={staff} busy={busy} internal={internal} body={body} replies={replies} onBody={setBody} onInternal={setInternal} onSubmit={e=>e.preventDefault()}/>}
describe('saved reply composer regression',()=>{
 it('copies a saved reply and allows choosing the same template again',()=>{render(<Harness/>);const select=screen.getByRole('combobox',{name:'Use a saved reply'});fireEvent.change(select,{target:{value:'1'}});expect(screen.getByLabelText('Your reply')).toHaveValue('TEST helpful reply body.');expect(select).toHaveValue('');fireEvent.change(screen.getByLabelText('Your reply'),{target:{value:'Changed draft'}});fireEvent.change(select,{target:{value:'1'}});expect(screen.getByLabelText('Your reply')).toHaveValue('TEST helpful reply body.');expect(screen.getByRole('button',{name:'Send reply'})).toBeEnabled()});
 it('protects the draft and reply mode while a send is pending',()=>{render(<Harness busy/>);expect(screen.getByLabelText('Your reply')).toBeDisabled();expect(screen.getByRole('combobox')).toBeDisabled();expect(screen.getByRole('button',{name:'Public reply'})).toBeDisabled();expect(screen.getByRole('button',{name:'Internal note'})).toBeDisabled()});
 it('never offers employees internal notes or saved replies',()=>{render(<Harness staff={false}/>);expect(screen.queryByRole('combobox')).toBeNull();expect(screen.queryByRole('button',{name:'Internal note'})).toBeNull()});
 it('keeps a selected template when switching between public and internal modes',()=>{render(<Harness/>);fireEvent.click(screen.getByRole('button',{name:'Internal note'}));fireEvent.change(screen.getByRole('combobox'),{target:{value:'1'}});expect(screen.getByLabelText('Internal note')).toHaveValue('TEST helpful reply body.');fireEvent.click(screen.getByRole('button',{name:'Public reply'}));expect(screen.getByLabelText('Your reply')).toHaveValue('TEST helpful reply body.')});
});
