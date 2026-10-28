# ExamSprint · 概率统计期中冲刺

**在线静态网页：** https://jonhate.github.io/probability-exam-sprint/

这个仓库包含两部分：

- 根目录：零依赖静态网页（GitHub Pages 已上线）
- `server/`：完整 Python 后端（上传资料、重新生成、DeepSeek 问答、导出）

## 静态网页版

- 不需要 Python / API Key
- 已预装《概率统计》60→80→100 冲刺包
- 学习进度保存在浏览器 `localStorage`
- 不支持上传新资料、重新生成、修改模型

直接打开 `index.html`，或：

```powershell
python -m http.server 8770
```

## 多课程

完整后端支持课程库：点左上角课程名 → 新建课程。只有 PPT + 作业也能生成；没有真题时会按“作业重复 40% + PPT 强调 40% + 先修 20%”排序，并标记为低置信度推断。静态网页版只含当前概率统计课程。

## 完整后端部署到 Render（免费层）

**一键 Blueprint：** https://render.com/deploy?repo=https://github.com/jonhate/probability-exam-sprint

1. 用 GitHub 登录 [Render](https://render.com)。
2. New → Blueprint → 选择本仓库。
3. Render 会读取根目录的 `render.yaml`，构建 `server/Dockerfile`。
4. 设置环境变量 `EXAMSPRINT_ACCESS_TOKEN` 为你的访问密码。
5. 部署完成后，浏览器会弹 HTTP Basic Auth：用户名随便填，密码就是该 Token。

免费层注意：

- 一段时间无请求会休眠，首次打开会慢；
- 文件系统是临时的，上传文件、API Key、进度可能在重启/重新部署后丢失；
- 必须设置 `EXAMSPRINT_ACCESS_TOKEN`，否则任何拿到 URL 的人都能使用和改设置；
- 想长期稳定保存数据，需要持久磁盘或数据库。

## 静态页部署（已配置）

GitHub 仓库 → Settings → Pages → Deploy from a branch → `main` / root。

> 公开仓库 + 公开网页意味着整理后的课程内容可见；仓库不包含原始 PPT/PDF/作业图片。

## 本地完整版

根目录之外的 `启动概率统计冲刺.bat` 是本机完整版启动器。它使用本地 `data/`，不会因为云服务器休眠丢数据。
