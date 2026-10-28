# 手机 / 平板安装说明

## 方案 A：PWA（iPhone、iPad、Android 通用，推荐）

打开：

**https://jonhate.github.io/probability-exam-sprint/**

首次打开后：

- **iPhone / iPad Safari**：底部分享按钮 → “添加到主屏幕”
- **Android Chrome**：右上角菜单 → “安装应用 / 添加到主屏幕”
- **Edge**：菜单 → “应用” → “安装此站点为应用”

安装后会以独立窗口启动，有 ExamSprint 图标；首次联网加载后，学习内容可离线使用。

注意：PWA 是**概率统计静态版**，不包含上传新资料、重新生成、AI 问教练。多课程要用完整版（本地或 Render）。

## 方案 B：Android APK

下载：

**https://github.com/jonhate/probability-exam-sprint/releases/download/v1.0-android/ExamSprint.apk**

或打开 release 页面：

**https://github.com/jonhate/probability-exam-sprint/releases/tag/v1.0-android**

安装：

1. 在安卓手机浏览器下载 APK；
2. 系统提示“未知来源/外部来源应用”时，允许当前浏览器安装；
3. 打开 ExamSprint。

这是个人学习用的 **debug 签名 APK**，不是 Google Play 上架版本。只从上面的仓库链接下载，不要从陌生站点下载同名文件。

APK 目前内置的是《概率统计》静态冲刺包，离线可用；不包含上传新资料和多课程。需要多课程时用本地完整版，或部署 Render 后端后在手机浏览器访问。

## 方案 C：iPhone/iPad 原生 App

Windows 无法直接编译 iOS IPA，需要 Mac + Xcode + Apple 开发者签名。当前最实用的是方案 A 的 PWA；添加到主屏幕后体验接近原生 App。

## 数据与进度

- PWA：进度保存在当前浏览器的 `localStorage`；清理浏览器数据会丢失。
- APK：进度保存在 Android WebView 的本地存储；卸载 App 会丢失。
- 多设备之间不同步。
