# ExamSprint 阶段总结（2026-11-08）

## 这轮做了什么

根据独立只读审计报告，先修 P1，再处理可落地的 P2：

- **R01 间隔复测**：只有同一道题两次独立成功且间隔 ≥30 分钟，才标记 retained；不同题只算 transfer。
- **R02 静态保存**：localStorage 写入失败返回 507 并回滚，不再假装保存成功；恢复后可重试且只追加一条。
- **R03 Android 漂移**：归档 Android assets 同步为 57 题；构建脚本自动同步；新增 `release-manifest.json` 与 `verify_release.py`。
- **R04 答案暴露**：最近 30 分钟内看过反馈后重答不形成独立证据；结果页显示“答案暴露后的纠错”，提示改排新题或间隔复测。
- **R05 内容版本**：静态 progress 带 `analysis_revision`；内容版本变化归档旧进度；无版本旧记录标记 legacy，不当作独立证据。
- **R06/R07 校验与防错**：静态桥补题目/评分点校验；后端进度写入强制课程与内容版本头。
- **R08 空状态**：过期、会话完成、每日休息、等待、短预算、无题各有独立动作。
- **R09 题干**：q007 改为精确 `6/13`；q008 补 `s,t≥0`。
- **R10 评分点/题族**：q010/s2q02 增加 `rubric_points` 和 `completed_point_ids`；新增 `analysis.question_families`，42 道题标注 10 个题族，`transfer` 只按不同题族计数。
- **R11 文档**：57 题、PWA v5、静态限制、Android 构建说明已更新。

## 验证结果

```text
python -m unittest discover -s tests -p "test_*.py"  → 33 tests OK
node tests/frontend_test.cjs                         → PASSED
node tests/static_bridge_test.cjs                    → PASSED
python tests/smoke_test.py                           → PASSED（57 题）
python tools/verify_release.py                       → ok: true, questions: 57
```

## 还没完成

- R04 的“立即纠错 / 独立验证”两个独立 UI 标签
- R05 无 meta 旧进度的真实旧包迁移验收
- O01 零基础先修工具纳入调度
- O02 用真实使用数据校准权重与阈值
- 真实手机/平板触控、完整浏览器流程、Render 实际部署

## 产物

- 审计报告：`ExamSprint_整改报告_2026-11-08.md`
- 整改对照表：`整改对照表_2026-11-08.md`
- 归档：`C:\Users\26357\Desktop\跨保\快速应试项目_归档_2026-11-02.zip`

审计结论不变：**当前可用，限个人辅助复习；不能验收为可靠的自动学习 Agent。** 现有测试通过不等于剩余审计项已完成。

## 小册子补录

- 用户指定作业集《概率统计小册子（高清）.pdf》38 页扫描版已用 RapidOCR 逐页识别并写入课程语料。
- 当前 9 份入课材料、语料约 51,550 字符；小册子 38/38 页已纳入。
- OCR 的公式和符号仍需人工校对。
