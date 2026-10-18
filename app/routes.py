import os, re, time, uuid
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import urlparse
from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
from . import db
from .models import Admin, Post, Project, Message, now

api = Blueprint("api", __name__)
limits = defaultdict(deque)
ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

def rate_limited(key, maximum, seconds):
    q = limits[key]; t = time.monotonic()
    while q and t - q[0] > seconds: q.popleft()
    if len(q) >= maximum: return True
    q.append(t); return False

def bad(msg, code=400): return jsonify(error=msg), code
def data(): 
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else {}
def slugify(text):
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text.lower().strip()).strip("-")[:180]
    return text or uuid.uuid4().hex[:12]
def make_slug(title, exclude=None):
    base = slugify(title); candidate = base; i = 2
    while True:
        q = Post.query.filter_by(slug=candidate)
        if exclude: q = q.filter(Post.id != exclude)
        if not q.first(): return candidate
        candidate = f"{base}-{i}"; i += 1
def post_json(p):
    return dict(id=p.id,title=p.title,slug=p.slug,summary=p.summary,body=p.body,status=p.status,
      created_at=p.created_at.isoformat(),updated_at=p.updated_at.isoformat(),
      published_at=p.published_at.isoformat() if p.published_at else None)
def project_json(p):
    return dict(id=p.id,title=p.title,description=p.description,url=p.url,image_path=p.image_path,
      sort_order=p.sort_order,is_published=p.is_published)

@api.get("/status")
def status(): return jsonify(status="ok", service="my-portfolio")

@api.get("/posts")
def posts():
    q = Post.query
    if not current_user.is_authenticated: q = q.filter_by(status="published")
    items = q.order_by(Post.created_at.desc()).limit(100).all()
    return jsonify(posts=[post_json(p) for p in items])

@api.post("/login")
def login():
    remote = request.remote_addr or "unknown"
    if rate_limited("login:"+remote, 8, 300): return bad("登录尝试过多，请稍后再试。",429)
    d=data(); user=Admin.query.filter_by(username=str(d.get("username","")).strip()[:80]).first()
    if not user or not user.check_password(str(d.get("password",""))): return bad("用户名或密码错误。",401)
    from flask import session
    session.clear(); login_user(user, fresh=True)
    return jsonify(ok=True, username=user.username)

@api.post("/logout")
@login_required
def logout():
    logout_user()
    from flask import session
    session.clear()
    return jsonify(ok=True)

@api.get("/me")
def me():
    return jsonify(authenticated=bool(current_user.is_authenticated), username=current_user.username if current_user.is_authenticated else None)

@api.post("/posts")
@login_required
def add_post():
    d=data(); title=str(d.get("title","")).strip(); body=str(d.get("body","")).strip()
    summary=str(d.get("summary","")).strip(); status=d.get("status","draft")
    if not title or len(title)>180 or len(summary)>500 or len(body)>100000: return bad("请检查标题、摘要或正文长度。")
    if status not in ("draft","published"): return bad("文章状态无效。")
    p=Post(title=title,slug=make_slug(title),summary=summary,body=body,status=status,published_at=now() if status=="published" else None)
    db.session.add(p); db.session.commit()
    return jsonify(post=post_json(p)),201

@api.put("/posts/<int:pid>")
@login_required
def edit_post(pid):
    p=db.session.get_or_404(Post,pid); d=data()
    title=str(d.get("title",p.title)).strip(); summary=str(d.get("summary",p.summary)).strip(); body=str(d.get("body",p.body)).strip(); status=d.get("status",p.status)
    if not title or len(title)>180 or len(summary)>500 or len(body)>100000: return bad("请检查标题、摘要或正文长度。")
    if status not in ("draft","published"): return bad("文章状态无效。")
    was=p.status; p.title=title; p.slug=make_slug(title,p.id); p.summary=summary; p.body=body; p.status=status
    if status=="published" and was!="published": p.published_at=now()
    if status=="draft": p.published_at=None
    db.session.commit(); return jsonify(post=post_json(p))

@api.delete("/posts/<int:pid>")
@login_required
def del_post(pid):
    db.session.delete(db.session.get_or_404(Post,pid)); db.session.commit(); return jsonify(ok=True)

@api.get("/projects")
def projects():
    q=Project.query
    if not current_user.is_authenticated: q=q.filter_by(is_published=True)
    return jsonify(projects=[project_json(p) for p in q.order_by(Project.sort_order,Project.id.desc()).limit(100).all()])

@api.post("/projects")
@login_required
def add_project():
    d=data(); title=str(d.get("title","")).strip(); desc=str(d.get("description","")).strip(); url=str(d.get("url","")).strip()
    if not title or len(title)>180 or len(desc)>1000: return bad("请填写有效标题和描述。")
    if url and (urlparse(url).scheme not in ("http","https") or not urlparse(url).netloc): return bad("链接必须是 http 或 https 地址。")
    image_path=str(d.get("image_path","")).strip()
    if image_path and not image_path.startswith("/uploads/"): return bad("图片地址必须来自本网站上传目录。")
    p=Project(title=title,description=desc,url=url,image_path=image_path,sort_order=int(d.get("sort_order",0) or 0),is_published=bool(d.get("is_published",True)))
    db.session.add(p); db.session.commit(); return jsonify(project=project_json(p)),201

@api.put("/projects/<int:pid>")
@login_required
def edit_project(pid):
    p=db.session.get_or_404(Project,pid); d=data()
    title=str(d.get("title",p.title)).strip(); desc=str(d.get("description",p.description)).strip(); url=str(d.get("url",p.url)).strip()
    if not title or len(title)>180 or len(desc)>1000: return bad("请填写有效标题和描述。")
    if url and (urlparse(url).scheme not in ("http","https") or not urlparse(url).netloc): return bad("链接必须是 http 或 https 地址。")
    image_path=str(d.get("image_path",p.image_path)).strip()
    if image_path and not image_path.startswith("/uploads/"): return bad("图片地址必须来自本网站上传目录。")
    p.title=title;p.description=desc;p.url=url;p.image_path=image_path;p.sort_order=int(d.get("sort_order",p.sort_order) or 0);p.is_published=bool(d.get("is_published",p.is_published))
    db.session.commit();return jsonify(project=project_json(p))

@api.delete("/projects/<int:pid>")
@login_required
def del_project(pid):
    db.session.delete(db.session.get_or_404(Project,pid));db.session.commit();return jsonify(ok=True)

@api.post("/messages")
def add_message():
    d=data(); nick=str(d.get("nickname","")).strip(); content=str(d.get("content","")).strip()
    if d.get("website"): return jsonify(ok=True),201
    if not nick or len(nick)>80 or len(content)<2 or len(content)>2000: return bad("请检查昵称和留言长度。")
    if rate_limited("msg:"+(request.remote_addr or "unknown"),5,600): return bad("提交过于频繁，请稍后再试。",429)
    m=Message(nickname=nick,content=content,is_approved=False);db.session.add(m);db.session.commit()
    return jsonify(ok=True,message="留言已提交，审核后显示。"),201

@api.get("/messages")
def messages():
    q=Message.query
    if not current_user.is_authenticated: q=q.filter_by(is_approved=True)
    items=q.order_by(Message.created_at.desc()).limit(200).all()
    return jsonify(messages=[dict(id=m.id,nickname=m.nickname,content=m.content,is_approved=m.is_approved,created_at=m.created_at.isoformat()) for m in items])

@api.patch("/messages/<int:mid>")
@login_required
def approve(mid):
    m=db.session.get_or_404(Message,mid);m.is_approved=bool(data().get("is_approved",False));db.session.commit()
    return jsonify(ok=True,is_approved=m.is_approved)

@api.delete("/messages/<int:mid>")
@login_required
def del_message(mid):
    db.session.delete(db.session.get_or_404(Message,mid));db.session.commit();return jsonify(ok=True)

@api.post("/upload")
@login_required
def upload():
    f=request.files.get("file")
    if not f or not f.filename: return bad("请选择图片。")
    ext=Path(secure_filename(f.filename)).suffix.lower()
    if ext not in ALLOWED: return bad("只允许 JPG、PNG、WEBP 或 GIF。")
    directory=Path(current_app.config["UPLOAD_DIR"]);directory.mkdir(parents=True,exist_ok=True)
    name=uuid.uuid4().hex+ext;target=directory/name
    try:
        im=Image.open(f.stream);im.verify();f.stream.seek(0);im=Image.open(f.stream)
        if im.width>8000 or im.height>8000: return bad("图片尺寸过大。")
        f.stream.seek(0);f.save(target)
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError):
        target.unlink(missing_ok=True);return bad("无法识别图片文件。")
    return jsonify(ok=True,path="/uploads/"+name),201

@api.get("/uploads/<path:name>")
def uploaded(name):
    base=Path(current_app.config["UPLOAD_DIR"]).resolve();target=(base/name).resolve()
    if not str(target).startswith(str(base)+os.sep) or not target.is_file(): return bad("Not found",404)
    # Serve untrusted uploads as attachment-like binary with nosniff to reduce script execution risk.
    mime={".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".webp":"image/webp",".gif":"image/gif"}.get(target.suffix.lower(),"application/octet-stream")
    return current_app.response_class(open(target,"rb"),mimetype=mime,headers={"X-Content-Type-Options":"nosniff","Cache-Control":"public,max-age=86400"})
