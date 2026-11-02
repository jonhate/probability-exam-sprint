# Repository map / 仓库完整性说明

这个仓库是 ExamSprint 的**可部署镜像**，不是原始课程资料仓库。

## 根目录：静态 PWA

- `index.html`
- `app.js`
- `styles.css`
- `data.js`：由当前课程生成的静态数据，不要手改
- `static_bridge.js`：无 Python 时的本地学习桥接
- `manifest.webmanifest` / `service-worker.js` / 图标
- `README.md` / `MOBILE.md` / `NOTICE.md` / `LICENSE`

## `server/`：完整 Python 后端

- `server/app.py`：HTTP 服务、鉴权、API
- `server/engine/`：解析、LLM 管线、课程库、学习任务调度
- `server/static/`：完整版前端
- `server/data/`：概率课程种子数据（不含 API Key）
- `server/tests/`：29 项回归/学习/前端测试
- `server/tools/`：课程种子、静态构建、零基础注入工具
- `server/docs/`：研究说明
- `server/Dockerfile` / `server/requirements.txt`

## Android

- `mobile/android/`：Android WebView 壳工程源码
- APK 资产来自根目录 PWA；`local.properties` 和构建缓存不提交
- 发布 APK 在 GitHub Release `v1.0-android`

## 明确不提交

- 原始 PPT / PDF / 作业截图 / 答案文件
- 用户上传资料、解析缓存、上传临时文件
- `data/settings.json` 中的 API Key（当前为空）
- `__pycache__`、`.gradle`、Android `build/`

## 说明

- 本地唯一主源码：`C:\Users\26357\Desktop\跨保\exam_sprint`
- 云端副本：`server/`
- 静态页是概率统计单课程；完整版支持课程库、上传和模型生成。
