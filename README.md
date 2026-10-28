# ExamSprint · 概率统计期中冲刺

**在线网页：** https://jonhate.github.io/probability-exam-sprint/

# ExamSprint 静态网页版

这是给“手机/平板/任何浏览器打开”的版本：

- 不需要 Python；
- 不需要 API Key；
- 已预装当前《概率统计》60→80→100 冲刺包；
- 学习进度保存在浏览器 `localStorage`；
- 不支持上传新资料、重新生成、修改模型（这些用本地完整版）。

## 本地预览

直接双击 `index.html` 也能打开。  
如果浏览器限制本地文件，执行：

```powershell
python -m http.server 8770
```

然后打开 `http://127.0.0.1:8770/`。

## 部署到 GitHub Pages

在 `web/` 目录执行：

```bash
git init
git add .
git commit -m "ExamSprint probability midterm web"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库.git
git push -u origin main
```

然后：

1. 打开 GitHub 仓库 → Settings → Pages
2. Source 选 `Deploy from a branch`
3. Branch 选 `main`，目录选 `/ (root)`
4. 保存，等待 1–2 分钟
5. 地址是 `https://你的用户名.github.io/你的仓库/`

> 公开仓库 + GitHub Pages 意味着**课程内容和题目摘录公开可见**。如果不想公开，用本地版，或使用带访问控制的托管（Cloudflare Access / Netlify password）。

## 部署到 Netlify / Cloudflare Pages

把整个 `web/` 文件夹拖到：

- https://app.netlify.com/drop
- 或 Cloudflare Pages 的 “Upload assets”

不需要构建命令，发布目录就是 `web/`。

## 想保留完整功能

需要 Python 后端（上传、重新生成、DeepSeek 问答）时，不要把 `app.py` 放 GitHub Pages，Pages 只能托管静态文件。可以用 Render / Railway / 一台云服务器运行 `app.py`，或者继续在本机双击 `启动概率统计冲刺.bat`。
