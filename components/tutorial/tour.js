/* The tour changes presentation only. No input.value assignment or project events. */
(() => {
  const send=(type,extra={})=>parent.postMessage({isStreamlitMessage:true,type,...extra},'*');
  let D, W, isolated=false;
  try { D=parent.document; W=parent; void D.body; } catch { D=document; W=window; isolated=true; }
  let args, prefs={}, storageFailed=false, mode=null, step=0, targetKey=null, card=null, ring=null, modal=null;
  let focusBefore=null, priorTab=null, dirty=false, initialized=false, lastToken=null, queuedTour=false, pending=false;
  const KEY='geldoc.onboarding.v1', RUN='geldoc.tour.running.v1';
  const readRun=()=>{try{return JSON.parse(W.sessionStorage.getItem(RUN)||'null')}catch{return null}};
  const writeRun=()=>{try{W.sessionStorage.setItem(RUN,JSON.stringify({step,targetKey}))}catch{storageFailed=true}};
  const clearRun=()=>{try{W.sessionStorage.removeItem(RUN)}catch{}};
  const text=k=>args?.text[k]||'';
  const memory=()=>{try{const value=JSON.parse(W.localStorage.getItem(KEY)||'{}');return value&&typeof value==='object'&&!Array.isArray(value)?value:{}}catch{storageFailed=true;return {}}};
  const persist=patch=>{prefs={...prefs,...memory(),...patch};try{W.localStorage.setItem(KEY,JSON.stringify(prefs))}catch{storageFailed=true}};
  const node=(tag,content,cls)=>{const n=D.createElement(tag);if(content)n.textContent=content;if(cls)n.className=cls;return n};
  function button(label,fn){const b=node('button',label);b.type='button';b.onclick=fn;return b}
  function height(){send('streamlit:setFrameHeight',{height:isolated?Math.max(70,document.body.scrollHeight):document.body.scrollHeight+4})}
  function rememberFocus(){focusBefore=D.activeElement;if(focusBefore===window.frameElement)focusBefore=document.activeElement}
  function restoreFocus(){if(focusBefore?.isConnected)focusBefore.focus({preventScroll:true});else document.querySelector('button')?.focus()}
  function cleanup(){card?.remove();ring?.remove();modal?.remove();card=ring=modal=null}
  function style(){if(D.getElementById('gd-tour-style'))return;const s=node('style');s.id='gd-tour-style';s.textContent=`
.gd-tour{font:14px/1.5 system-ui,sans-serif;color:var(--lab-text,#17212e);--panel:var(--lab-panel,#fff);--border:var(--lab-border,#dce4ee);--button:var(--lab-soft,#eaf3ff);--muted:#64748b;--accent:var(--lab-accent-ink,#2563a6);box-sizing:border-box}
.gd-tour.dark{color:var(--lab-text,#e7eef8);--panel:var(--lab-panel,#182333);--border:var(--lab-border,#34465e);--button:var(--lab-soft,#253d5b);--muted:#a4b3c6;--accent:var(--lab-accent-ink,#93c5fd)}
.gd-tour button{font:inherit;color:inherit;background:var(--button);border:1px solid var(--border);border-radius:5px;padding:7px 11px;cursor:pointer}
.gd-tour button:focus-visible{outline:3px solid #60a5fa;outline-offset:2px}.gd-tour button:disabled{opacity:.45;cursor:default}
.gd-tour h2{font:600 18px/1.3 system-ui!important;color:inherit!important;margin:0 0 10px!important;padding:0!important}
.gd-tour p{color:inherit!important;font-size:14px!important;margin:8px 0!important}.gd-tour small{color:var(--muted)}
.gd-tour-card{position:fixed;z-index:999990;width:345px;max-width:calc(100vw - 24px);max-height:calc(100vh - 90px);overflow:auto;padding:18px;background:var(--panel);border:1px solid var(--border);border-top:4px solid #60a5fa;border-radius:12px;box-shadow:0 6px 25px #15213118}
.gd-tour-card.gd-tour-export{width:390px}
.gd-tour-nav,.gd-tour-links{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.gd-tour-links button{font-size:12px;padding:4px 8px}.gd-tour-links button[aria-pressed=true]{border-color:#60a5fa;color:var(--accent)}
.gd-tour-ring{pointer-events:none;position:fixed;z-index:999989;border:3px solid #60a5fa;border-radius:4px;box-shadow:0 0 0 3px #60a5fa33;box-sizing:border-box}
.gd-tour dialog,dialog.gd-tour{max-width:min(640px,calc(100vw - 32px));max-height:80vh;overflow:auto;padding:24px;background:var(--panel);border:1px solid var(--border);border-radius:10px;z-index:999999}dialog.gd-tour::backdrop{background:#0005}
.gd-tour section{border-top:1px solid var(--border);margin-top:16px;padding-top:14px}.gd-tour .gd-task{border-left:3px solid #60a5fa;padding-left:12px}.gd-tour .gd-warning{font-size:12px!important;color:var(--muted)!important}
`;D.head.append(s)}
  function theme(n){n.className='gd-tour'+(args.dark?' dark':'')}
  function warn(n){if(storageFailed)n.append(node('p',text('onboard_storage'),'gd-warning'));if(isolated)n.append(node('p',text('onboard_fallback'),'gd-warning'))}
  function close(completed=false){clearRun();if(completed)persist({onboarding_seen:true,tutorial_completed:true});else persist({onboarding_seen:true});cleanup();mode=null;targetKey=null;if(priorTab?.isConnected)priorTab.click();priorTab=null;restoreFocus();height()}
  function begin(){rememberFocus();priorTab=D.querySelector('[role="tab"][aria-selected="true"]');persist({onboarding_seen:true});step=0;mode='tour';targetKey=args.steps[0][0];writeRun();cleanup();showTour(true)}
  function makeCard(title){const c=node('section');theme(c);c.classList.add('gd-tour-card');c.setAttribute('role','region');c.setAttribute('aria-label',title);c.append(node('h2',title));D.body.append(c);card=c;return c}
  function welcome(){mode='welcome';rememberFocus();cleanup();const c=makeCard(text('onboard_welcome_title'));c.append(node('p',text('onboard_welcome')));const nav=node('div',null,'gd-tour-nav');nav.append(button(text('onboard_start'),begin),button(text('onboard_demo_tour'),()=>requestDemo(true)),button(text('onboard_later'),()=>close()));c.append(nav);warn(c);c.style.right='18px';c.style.top='90px';height()}
  function tabs(){return [...D.querySelectorAll('[data-testid="stTabs"] [role="tab"]')].slice(0,5)}
  function visible(n){return n&&n.getClientRects().length&&W.getComputedStyle(n).visibility!=='hidden'}
  function locate(switchTab=false){if(isolated)return null;const desc=args.targets[targetKey];if(!desc)return null;
    if(switchTab&&desc.sidebar)D.querySelector('button[aria-label="Expand sidebar"]')?.click();
    const ts=tabs();if(switchTab&&desc.tab!==undefined)ts[desc.tab]?.click();
    let scope=desc.sidebar?D.querySelector('[data-testid="stSidebar"]'):D.getElementById(ts[desc.tab]?.getAttribute('aria-controls'));
    if(!scope&&desc.tab!==undefined)scope=[...D.querySelectorAll('[role="tabpanel"]')][desc.tab];if(!scope)return null;
    let el;
    if(desc.selector)el=scope.querySelector(desc.selector);
    if(desc.heading){el=[...scope.querySelectorAll('h1,h2,h3,h4,h5,h6')].find(n=>n.textContent.trim()===desc.heading);if(el)el=el.closest('[data-testid="stElementContainer"]')||el;}
    if(desc.label){const label=[...scope.querySelectorAll('label,p')].find(n=>n.textContent.trim()===desc.label);el=label?.closest('[data-testid="stSelectbox"]')||label;}
    return visible(el)?el:null;
  }
  function position(){if(!card||mode!=='tour')return;const el=locate();const w=W.innerWidth,h=W.innerHeight;ring.hidden=!el;
    const sidebar=D.querySelector('[data-testid="stSidebar"]');const sb=sidebar?.getBoundingClientRect();
    const contentLeft=sb&&sb.left<w&&sb.right>0?Math.min(w-12,sb.right+12):12;
    const cardWidth=card.getBoundingClientRect().width;
    const rightEdge=Math.max(12,w-cardWidth-12);
    if(el){const r=el.getBoundingClientRect();Object.assign(ring.style,{left:Math.max(0,r.left-3)+'px',top:Math.max(0,r.top-3)+'px',width:Math.min(w,r.width+6)+'px',height:Math.min(h,r.height+6)+'px'});
      let left;
      if(step===4){left=rightEdge}
      else if(w-r.right>cardWidth+26){left=r.right+14}
      else if(r.left-cardWidth-14>=contentLeft){left=r.left-cardWidth-14}
      else {left=rightEdge}
      card.style.left=Math.max(12,Math.min(rightEdge,left))+'px';card.style.right='auto';
      const preferredTop=step===4?70:r.top;
      card.style.top=Math.max(12,Math.min(preferredTop,h-card.offsetHeight-12))+'px';
    }else{card.style.right='18px';card.style.left='auto';card.style.top='90px'}
    const msg=card.querySelector('[data-missing]');if(msg)msg.hidden=!!el||isolated;
  }
  function showTour(move=false){cleanup();const title=text('onboard_title_'+(step+1));const c=makeCard(title);if(step===4)c.classList.add('gd-tour-export');const counter=node('small',text('onboard_step').replace('{step}',step+1));c.prepend(counter);c.append(node('p',text('onboard_body_'+(step+1))));const task=node('div',null,'gd-task');task.append(node('strong',text('onboard_task')),node('p',text('onboard_task_'+(step+1))));c.append(task);
    const links=node('div',null,'gd-tour-links');for(const key of args.steps[step]){const b=button(text('onboard_target_'+key),()=>{targetKey=key;writeRun();showTour(true)});b.setAttribute('aria-pressed',String(key===targetKey));links.append(b)}c.append(links);
    const missing=node('p',text('onboard_missing'),'gd-warning');missing.dataset.missing='true';c.append(missing);warn(c);
    const nav=node('div',null,'gd-tour-nav');const back=button(text('onboard_back'),()=>{step--;targetKey=args.steps[step][0];writeRun();showTour(true);card.querySelector('button')?.focus()});back.disabled=step===0;
    nav.append(back,button(text(step===4?'onboard_finish':'onboard_next'),()=>{if(step===4){close(true);return}step++;targetKey=args.steps[step][0];writeRun();showTour(true);card.querySelector('button')?.focus()}),button(text('onboard_close'),()=>close()));c.append(nav);
    ring=node('div',null,'gd-tour-ring');ring.setAttribute('aria-hidden','true');D.body.append(ring);
    const el=locate(move);if(move&&el)el.scrollIntoView({block:'center',behavior:'instant'});position();W.requestAnimationFrame(()=>W.requestAnimationFrame(()=>{if(move&&mode==='tour'){const settled=locate(true);settled?.scrollIntoView({block:'center',behavior:'instant'})}position()}));height();
  }
  function dialog(title){cleanup();modal=node('dialog');theme(modal);modal.setAttribute('aria-label',title);modal.append(node('h2',title));D.body.append(modal);modal.addEventListener('cancel',e=>{e.preventDefault();closeDialog()});return modal}
  function closeDialog(){cleanup();mode=null;restoreFocus();height()}
  function help(){rememberFocus();mode='help';const m=dialog(text('onboard_help_title'));for(const section of ['mouse','keys','labels','color','save']){const s=node('section');s.append(node('h2',text('onboard_help_'+section+'_title')),node('p',text('onboard_help_'+section)));m.append(s)}warn(m);m.append(button(text('onboard_dismiss'),closeDialog));m.showModal();m.querySelector('button').focus();height()}
  function hasDraft(){if(dirty)return true;for(const f of D.querySelectorAll('iframe')){try{const s=f.contentDocument?.querySelector('#status');if(s&&/Noch nicht|Unsaved/.test(s.textContent))return true}catch{}}return false}
  function requestDemo(tour=false){if(pending)return;queuedTour=tour;rememberFocus();if(args.has_work||hasDraft()){mode='confirm';const m=dialog(text('onboard_confirm_title'));m.append(node('p',text('onboard_confirm')));const nav=node('div',null,'gd-tour-nav');nav.append(button(text('onboard_cancel'),closeDialog),button(text('onboard_demo'),loadDemo));m.append(nav);m.showModal();nav.firstChild.focus();height()}else loadDemo()}
  function loadDemo(){if(pending)return;clearRun();pending=true;persist({onboarding_seen:true});cleanup();mode=null;send('streamlit:setComponentValue',{value:{action:'load_demo',confirmed:true,tour:queuedTour,nonce:crypto.randomUUID()},dataType:'json'});document.querySelectorAll('button').forEach(b=>b.disabled=true);height()}
  function renderBar(){document.body.className=args.dark?'dark':'';document.documentElement.lang=args.lang;const bar=document.getElementById('bar');bar.replaceChildren();const add=(key,fn)=>{const b=document.createElement('button');b.type='button';b.textContent=text(key);b.onclick=fn;bar.append(b)};if(!args.compact)add('onboard_start',begin);add('onboard_demo',()=>requestDemo());if(!args.compact)add('onboard_help',help);height()}
  D.addEventListener('input',()=>{dirty=true},true);
  const escape=e=>{if(e.key==='Escape'&&mode&&!modal){e.preventDefault();close()}};D.addEventListener('keydown',escape);document.addEventListener('keydown',escape);
  W.addEventListener('scroll',position,true);W.addEventListener('resize',position);
  const observer=new MutationObserver(()=>{if(mode==='tour')W.requestAnimationFrame(position)});
  // Observe app children only; overlay mutations must not cause a feedback loop.
  const appRoot=D.querySelector('[data-testid="stApp"]')||D.querySelector('.stApp');if(appRoot)observer.observe(appRoot,{childList:true,subtree:true});
  window.addEventListener('pagehide',()=>{cleanup();observer.disconnect();W.removeEventListener('scroll',position,true);W.removeEventListener('resize',position);D.removeEventListener('keydown',escape)});
  window.addEventListener('message',e=>{if(e.source!==parent||e.data.type!=='streamlit:render')return;args=e.data.args;style();renderBar();
    if(!initialized){initialized=true;prefs=memory();lastToken=args.demo_token;if(!args.compact){const state=readRun();if(state&&Number.isInteger(state.step)&&state.step>=0&&state.step<5){step=state.step;targetKey=args.steps[step].includes(state.targetKey)?state.targetKey:args.steps[step][0];mode='tour';showTour(true)}else if(!prefs.onboarding_seen&&!prefs.tutorial_completed)begin()}}
    if(args.demo_token&&args.demo_token!==lastToken){lastToken=args.demo_token;pending=false;dirty=false;cleanup();mode=null;renderBar();if(!args.compact&&args.start_tour)begin()}
    if(mode==='tour')showTour(false);else if(mode==='welcome')welcome();else if(mode==='help')help();else if(mode==='confirm'){pending=false;requestDemo(queuedTour)}
  });
  send('streamlit:componentReady',{apiVersion:1});new ResizeObserver(height).observe(document.body);
})();
