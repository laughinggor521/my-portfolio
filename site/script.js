const $=s=>document.querySelector(s);let csrfToken="";
async function csrf(){const r=await fetch("/api/csrf",{credentials:"same-origin"});csrfToken=(await r.json()).csrf_token;}
async function api(url,opt={}){if(!csrfToken)await csrf();const headers=new Headers(opt.headers||{});headers.set("X-CSRFToken",csrfToken);if(opt.body&&!(opt.body instanceof FormData))headers.set("Content-Type","application/json");const r=await fetch(url,{...opt,headers,credentials:"same-origin"});let d={};try{d=await r.json()}catch{}if(!r.ok)throw Error(d.error||`请求失败 (${r.status})`);return d;}
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const date=v=>v?new Date(v).toLocaleDateString("zh-CN"):"";
async function load(){
 const y=$("#year");if(y)y.textContent=new Date().getFullYear();
 await csrf().catch(()=>{});
 try{const {projects}=await api("/api/projects");$("#project-list").innerHTML=projects.length?projects.map(p=>`<article class="project-card">${p.image_path?`<img src="${esc(p.image_path)}" alt="" loading="lazy" style="width:100%;max-height:170px;object-fit:cover;border-radius:12px">`:""}<h3>${esc(p.title)}</h3><p>${esc(p.description)}</p>${p.url?`<a class="card-link" href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">查看项目 ↗</a>`:""}</article>`).join(""):`<div class="empty">作品正在整理中。</div>`}catch{$("#project-list").innerHTML='<div class="empty">暂时无法加载作品。</div>'}
 try{const {posts}=await api("/api/posts");$("#post-list").innerHTML=posts.length?posts.map(p=>`<article class="post-card"><div><h3>${esc(p.title)}</h3><p>${esc(p.summary||p.body.slice(0,160))}</p><details><summary class="card-link">阅读全文</summary><p style="white-space:pre-wrap;overflow-wrap:anywhere;margin-top:12px">${esc(p.body)}</p></details></div><time>${esc(date(p.published_at||p.created_at))}</time></article>`).join(""):`<div class="empty">还没有公开文章。</div>`}catch{$("#post-list").innerHTML='<div class="empty">暂时无法加载文章。</div>'}
 try{const {messages}=await api("/api/messages");$("#message-list").innerHTML=messages.map(m=>`<article class="message-item"><div class="message-meta"><strong>${esc(m.nickname)}</strong><time>${esc(date(m.created_at))}</time></div><p>${esc(m.content)}</p></article>`).join("")}catch{}
 $("#message-form")?.addEventListener("submit",async e=>{e.preventDefault();const f=e.currentTarget,feedback=$("#message-feedback");feedback.textContent="正在提交…";try{const d=await api("/api/messages",{method:"POST",body:JSON.stringify(Object.fromEntries(new FormData(f).entries()))});feedback.textContent=d.message||"留言已提交。";f.reset()}catch(err){feedback.textContent=err.message}});
}
document.addEventListener("DOMContentLoaded",load);
