import React from 'react';

export function NewsletterForm({title,body,placeholder='you@example.com',action='Subscribe',fine,onSubmit,...rest}){
  const [done,setDone] = React.useState(false);
  return (
    <section className="ds-newsletter" {...rest}>
      <div className="ds-wrap">
        <h2>{title}</h2>
        {body && <p>{body}</p>}
        <form onSubmit={e=>{e.preventDefault();setDone(true);onSubmit&&onSubmit(e);}}>
          <input type="email" placeholder={placeholder} required />
          <button type="submit">{done?'Subscribed \u2713':action}</button>
        </form>
        {fine && <p className="ds-newsletter__fine">{fine}</p>}
      </div>
    </section>
  );
}