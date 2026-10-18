# my-portfolio CMS staging build

此项目包是独立的测试版本，不会自动修改你现有的 GitHub `main` 分支或线上 Orkestr 服务。先部署到新分支/新服务验证，确认后再切换。

## 功能
- Flask + Gunicorn 后端，与静态前端运行在同一容器。
- PostgreSQL 单独部署；SQLAlchemy + Flask-Migrate/Alembic 管理数据库版本。
- 管理员登录、文章新增/编辑/删除、作品新增/编辑/删除、留言审核、图片上传。
- CSRF 保护、密码哈希、HttpOnly/SameSite/Secure Cookie、基础安全响应头、简单的登录/留言频率限制。

## 环境变量（在 Orkestr Web 服务中设置）
- `DATABASE_URL`（必填）：Orkestr PostgreSQL 的私有连接 URL，使用平台给出的真实值。
- `SECRET_KEY`（必填）：随机长密钥。可本地运行 `python -c "import secrets; print(secrets.token_urlsafe(48))"` 生成。
- `ADMIN_USERNAME`、`ADMIN_PASSWORD`：首次创建管理员。密码至少 14 位且独立使用；已有管理员不会在重部署时被重置。
- `PORT=8080`：若 Orkestr 手动要求配置端口。
- `UPLOAD_DIR=/data/uploads`：图片上传目录。
- `MAX_CONTENT_LENGTH_MB=8`、`COOKIE_SECURE=true`、`WEB_CONCURRENCY=2`：可选配置。生产 HTTPS 环境保留 `COOKIE_SECURE=true`。

`.env.example` 只有占位符，不要把真实密码或连接 URL 提交到 GitHub。

## Orkestr 部署步骤
1. 在 Orkestr 创建独立 PostgreSQL 数据库，优先使用内部/私有连接 URL。
2. 在 GitHub 建新分支 `cms-staging` 或新仓库上传此项目；先不要覆盖现有 `main`。
3. 在 Orkestr 新建一个测试 Web 服务，连接测试分支/新仓库，使用 Dockerfile 构建。
4. 设置以上环境变量，端口为 `8080`。
5. 若启用图片上传，给 Web 服务挂载持久化卷到 `/data`。容器文件系统不是永久存储；未挂载持久卷时，重建容器可能丢图。如果 Orkestr 没有适用的持久卷，请先改用 S3 兼容对象存储，再开放上传功能。
6. 部署后测试 `/healthz`、`/api/status`、`/admin.html`；创建文章、作品，提交留言并审核，上传图片并重部署确认图片仍在。
7. 测试通过前不要更改原有生产服务的仓库/分支/域名。

## 数据库迁移方案
- `migrations/versions/0001_initial_schema.py` 创建 `admins`、`posts`、`projects`、`messages` 四张表。
- 容器启动前执行 `flask --app wsgi:app db upgrade`，仅应用仓库中已提交的版本化迁移，不用 `create_all()` 自动猜测结构。
- 后续开发环境生成迁移：`flask --app wsgi:app db migrate -m "describe change"`；仔细检查生成文件，测试后提交。
- 对生产数据库做任何迁移前先创建备份/快照。不要修改或删除已应用的迁移文件。降级不是备份的替代品。
- 初次启动后会尝试按 `ADMIN_USERNAME`/`ADMIN_PASSWORD` 创建管理员；如果账号已存在，不会自动改密码。

## 安全与限制
- 不要把 `DATABASE_URL`、`SECRET_KEY`、`ADMIN_PASSWORD` 写入前端或 Git。
- 上传图片限制扩展名、尝试实际解码、限制尺寸；上传文件以 `application/octet-stream` 和 `nosniff` 提供。数据库备份不包含图片文件，需单独备份 `/data/uploads`。
- 留言默认待审核；前端以文本方式转义展示，不能直接把用户留言当 HTML 渲染。
- 频率限制是单进程内存实现，重启会重置，多副本不共享。正式公网使用建议加平台层限流/WAF。
- 当前为可部署的起步版，不含密码重置、富文本编辑器、分页、图片删除/替换界面或完整安全审计。正文以纯文本显示，生产上线前请充分测试。

## 验收清单
- [ ] 首页与 `/healthz` 正常。
- [ ] `/admin.html` 可登录。
- [ ] 文章草稿/发布/编辑/删除正常。
- [ ] 作品新增/编辑/隐藏/删除正常。
- [ ] 留言默认不公开，审核通过后可见。
- [ ] 上传图片后容器重部署仍可访问。
- [ ] 数据库和图片分别有备份方案。
