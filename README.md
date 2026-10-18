# 个人主页 / 作品展示网站

一个响应式、现代简洁风格的静态个人主页，使用 Docker + Nginx，可部署到连接 GitHub 仓库的 Orkestr 项目。

## 页面包含

- 响应式首页与个人介绍
- 技能标签
- 作品展示卡片
- 联系方式与社交链接占位符
- `/healthz` 健康检查接口
- Nginx 静态资源缓存
- 容器通过 `PORT` 环境变量监听端口，默认 `8080`

## 部署到 GitHub + Orkestr

### 1. 上传代码到 GitHub

1. 下载并解压项目 ZIP。
2. 打开你的 GitHub 仓库。
3. 建议先为当前状态页面创建一个备份分支，或新建仓库保存作品集。
4. 将解压后的项目文件上传到仓库根目录，确保根目录直接包含 `Dockerfile`、`nginx.conf.template`、`README.md` 和 `site/` 文件夹。
5. 提交（Commit）并推送（Push）更改。

如果使用 Git 命令行，可以在解压后的项目目录执行：

```bash
git init
git add .
git commit -m "Create personal portfolio website"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

如果本地目录已经是一个 Git 仓库，请不要重复执行 `git init` 或 `git remote add origin`；改用现有仓库的常规 `git add`、`git commit`、`git push` 流程。

### 2. 配置 Orkestr

1. 在 Orkestr 中创建新项目，或将现有项目指向这个仓库。
2. 选择 Dockerfile 构建方式。
3. 如果平台允许配置应用监听端口，设置为 `8080`；如果 Orkestr 注入了 `PORT` 环境变量，容器会使用它。
4. 部署成功后，使用 Orkestr 分配的 HTTPS 域名访问主页。

### 3. 后续更新

修改 `site/index.html`、`site/styles.css` 或 `site/script.js`，然后提交并推送到已连接的 GitHub 分支。若 Orkestr 已启用 Git 自动部署，平台会触发重新构建与部署。

## 自定义内容

编辑 `site/index.html`，把示例中的姓名、介绍、项目、邮箱和社交链接替换成你自己的信息。项目卡片中的链接默认是占位链接，发布前请替换。

## 本地预览

有 Docker 的电脑可以在项目目录运行：

```bash
docker build -t orkestr-portfolio .
docker run --rm -p 8080:8080 orkestr-portfolio
```

浏览器访问 `http://localhost:8080`。健康检查地址为 `http://localhost:8080/healthz`。

## 注意

- 这是静态网站，不包含登录系统、数据库或表单后端。
- HTTPS 由 Orkestr 的 HTTPS 入口提供；容器内部只提供 HTTP 服务。
- 这个包不会自动修改你现有的 GitHub 仓库或 Orkestr 项目。请先备份现有状态页面，再决定是新建仓库还是替换现有项目。
