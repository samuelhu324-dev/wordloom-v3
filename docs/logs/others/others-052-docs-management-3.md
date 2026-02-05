A5. 建 Issue 模板（让你开卡不费脑）

在你的本地仓库里加两个文件（这一步是“仓库内配置”，很推荐）：

1) 创建目录

在 repo 根目录：

.github/ISSUE_TEMPLATE/

2) 新建模板：task.md

内容如下（你可以直接复制）：

---
name: Task
about: A unit of work with clear DoD
title: "[P?][module] <short description>"
labels: []
assignees: ""
---

## Background
<!-- What is happening? Why does it matter? 3-5 lines -->

## Definition of Done (DoD)
- [ ] 
- [ ] 
- [ ] 

## Plan / Notes
<!-- Optional: investigation notes, approach -->

## Links
- Logs:
- ADR:
- PR:
- Related issues:

提交到 main：

git add .github/ISSUE_TEMPLATE/task.md
git commit -m "chore: add issue template"
git push

以后你点 “New issue” 就能直接用这个模板，不会每次从零写。

