import type { FormEvent } from 'react';
import { Icon } from './components';
import type { SavedReply } from './types';

type Props = {
  staff: boolean;
  busy: boolean;
  internal: boolean;
  body: string;
  replies: SavedReply[];
  onInternal: (internal: boolean) => void;
  onBody: (body: string) => void;
  onSubmit: (event: FormEvent) => void;
};

export function ReplyComposer({staff,busy,internal,body,replies,onInternal,onBody,onSubmit}: Props) {
  return <form className="reply-form" onSubmit={onSubmit}>
    {staff && <div className="reply-controls">
      <div className="segmented">
        <button type="button" disabled={busy} aria-pressed={!internal} onClick={() => onInternal(false)}>Public reply</button>
        <button type="button" disabled={busy} aria-pressed={internal} onClick={() => onInternal(true)}>Internal note</button>
      </div>
      <label><span className="sr-only">Use a saved reply</span>
        <select value="" disabled={busy || !replies.length} onChange={event => {
          const id = Number(event.currentTarget.value);
          const reply = replies.find(item => item.id === id);
          if (reply) onBody(reply.body);
        }}>
          <option value="">Use a saved reply</option>
          {replies.map(reply => <option key={reply.id} value={reply.id}>{reply.title}</option>)}
        </select>
      </label>
    </div>}
    <label><span className="sr-only">{internal ? 'Internal note' : 'Your reply'}</span>
      <textarea value={body} disabled={busy} onChange={event => onBody(event.target.value)} rows={4} required minLength={1} maxLength={5000} placeholder={internal ? 'Add a note only support staff can see…' : 'Write a helpful reply…'}/>
    </label>
    <div className="reply-footer">
      <span><Icon name="shield" size={15}/>{internal ? 'Visible to support staff only' : 'Visible to the requester and support team'}</span>
      <button className="button primary" disabled={busy || !body.trim()}>{busy ? 'Sending…' : internal ? 'Add internal note' : 'Send reply'}<Icon name="arrow" size={17}/></button>
    </div>
  </form>;
}
