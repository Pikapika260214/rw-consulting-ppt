# RW Consulting PPT Skills

这个仓库包含两个互相独立的 Codex Skills：

- `rw-consulting-ppt`：把行业报告、会议纪要、访谈笔记和半成品 bullet，转成 `proof-object-first` 的图片版咨询 PPT。
- `ppt-to-editable`：把单张 slide 图片、PNG/JPG 或截图转换成单页可编辑 PPTX。

两者平级放在 `skills/` 目录下，需要分别安装、分别触发，互不覆盖。`rw-consulting-ppt` 默认交付 PNG + `image-only PPTX`；如果少数关键页面需要后续编辑，可以再用 `ppt-to-editable` 逐页转换。

![RW Consulting PPT 工作流](skills/rw-consulting-ppt/assets/readme-hero.png)

> From rough business inputs to proof-object-first consulting slides.

## 效果展示

下面是两个 6 页 deck 的高清 3×2 overview。点击图片可以打开原图查看细节。

### 示例 1：AI 陪伴玩具行业判断

从行业研究材料生成 6 页管理层判断 deck，重点展示需求成立条件、留存逻辑、玩家格局、价值链迁移、信任风险和赢家逻辑。

<p>
  <a href="skills/rw-consulting-ppt/examples/ai-companion-toys-management-deck/overview-3x2.png"><img src="skills/rw-consulting-ppt/examples/ai-companion-toys-management-deck/overview-3x2.png" alt="AI 陪伴玩具 6 页高清 overview"></a>
</p>

### 示例 2：AI 眼镜行业研究

从半成品行业判断生成 6 页咨询页，重点展示需求验证、入口路线分化、价格带、真实需求矩阵、Google Glass 风险桥和未来赢家能力栈。

<p>
  <a href="skills/rw-consulting-ppt/examples/ai-glasses-market-deck/overview-3x2.png"><img src="skills/rw-consulting-ppt/examples/ai-glasses-market-deck/overview-3x2.png" alt="AI 眼镜 6 页高清 overview"></a>
</p>

## 它解决什么问题？

很多 PPT 难做，不是因为不会排版，而是因为输入材料本身还很粗糙：

- 多份行业报告读完了，但还没有 synthesis。
- 会议纪要很长，但没有变成一组清晰的汇报页。
- 研究判断有了，但不知道每页应该证明什么。
- 大纲里全是 bullet，但缺少管理层能读懂的 `storyline` 和证据结构。

RW Consulting PPT Skill 的重点不是“美化 PPT”，而是把粗糙材料先变成可交付的咨询表达：

```text
粗糙材料 -> 目标对齐 -> storyline -> 页面 brief -> 样页确认 -> PNG / image-only PPTX -> 可选关键页 editable conversion
```

## 30 秒开始

把需要的 skill 目录放到你的 Codex skills 目录里。两个 skill 是平级目录，需要分别安装，互不覆盖。

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills\rw-consulting-ppt" | Out-Null
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills\ppt-to-editable" | Out-Null
Copy-Item -Recurse -Force .\skills\rw-consulting-ppt\* "$env:USERPROFILE\.codex\skills\rw-consulting-ppt"
Copy-Item -Recurse -Force .\skills\ppt-to-editable\* "$env:USERPROFILE\.codex\skills\ppt-to-editable"
```

```bash
# macOS / Linux
mkdir -p ~/.codex/skills/rw-consulting-ppt ~/.codex/skills/ppt-to-editable
cp -R ./skills/rw-consulting-ppt/. ~/.codex/skills/rw-consulting-ppt/
cp -R ./skills/ppt-to-editable/. ~/.codex/skills/ppt-to-editable/
```

然后在 Codex 里这样触发：

生成图片版咨询 deck：

```text
请使用 rw-consulting-ppt，把这些行业研究材料整理成 6 页中文管理层汇报。

目标受众：业务负责人
交付模式：独立阅读型报告页
信息密度：标准咨询密度
视觉风格：管理层报告风，白底，深绿作为强调色
输出格式：PNG + image-only PPTX
```

转换单张图片为 editable PPTX：

```text
请使用 ppt-to-editable，把这张单页 slide 图片转换成单页可编辑 PPTX。

输入：我上传的 PNG / JPG / 截图图片
目标：尽量恢复可编辑文字和简单原生形状，同时保持原图版式
路线：先 OCR 和 OCR review，再判断 clean-background、hybrid 或 reconstruction
约束：不要做可见文字覆盖；不要额外添加 PowerPoint 阴影、发光、浮雕、反射等效果
交付：editable PPTX + editability_report.json
```

## 适合什么场景？

### 1. 行业报告分析 PPT

当你手里有多份行业报告、访谈纪要、公开资料和研究笔记，但还没有清晰的 deck 结构时，可以让这个 skill 先帮你完成 synthesis，再压缩成几页管理层可读的行业判断页。

它会把材料拆成：

- 核心问题：这套 deck 到底要回答什么？
- working thesis：目前最重要的判断是什么？
- storyline：页面之间如何递进？
- 页面级 claim：每页要证明哪一个结论？
- proof object：用什么结构承载证据，而不是堆 bullet？
- evidence boundary：哪些事实已支持，哪些还需要补证？

### 2. 会议 recap PPT

当你刚开完客户会议、老板 brainstorm 或项目 catch-up，只拿到一份长纪要 / 逐字稿时，可以让这个 skill 帮你整理成 recap deck。

它适合把会议材料转成：

- 本次讨论的核心议题；
- 已形成共识的判断；
- 仍然有分歧或需要确认的问题；
- 下一次讨论前需要补齐的证据；
- 面向管理层或客户的简洁 recap 页面。

## 它不是普通 PPT 模板

这个 skill 有意选择图片版咨询 PPT 路线。

它会做：

- 生成一张完整 16:9 PNG 作为一页 slide；
- 用 `proof object` 承载每页论证，比如漏斗、路径图、玩家格局、能力栈、风险桥；
- 先生成 1-2 页样页，让你确认风格、密度和表达逻辑；
- 在样页通过后，再批量生成完整 deck；
- 如果需要 PPTX，则把每张 PNG 打包成 `image-only PPTX`；
- 如果少数关键页面需要后续编辑，可再用 `ppt-to-editable` 逐页转换成单页 editable PPTX。

`rw-consulting-ppt` 本身不会直接做：

- 从粗糙材料一步生成整套全页、全对象原生可编辑 PPTX；
- 用 HTML / CSS / React 截图伪装成 PPT 页面；
- Python / Pillow / SVG / canvas 绘制的伪 PPT；
- 普通模板套壳或三栏卡片堆叠。

如果你已经有一张成品 slide 图片，并希望恢复部分编辑能力，可以使用同仓库的 `ppt-to-editable`。两个 skill 的分工是：`rw-consulting-ppt` 先把复杂业务材料变成咨询级图片页；`ppt-to-editable` 再对选中的单张图片页做可编辑化转换。

## 同仓库的另一个 Skill：ppt-to-editable

`ppt-to-editable` 当前支持：将单张图片输入转换为单页可编辑 PPTX。

它适合已经有一张成品 slide 图片，但希望恢复一部分可编辑能力的场景。当前公开稳定能力聚焦在“单张图片输入”，而不是限制图片来源：

- 单页 PNG slide；
- 单张截图导出的 PNG / JPG；
- 其他单张 16:9 slide image。

当前输出是一页 editable PPTX，核心能力包括：

- OCR 辅助文字恢复；
- `clean-background + editable text`；
- 对结构简单的页面，可使用 `hybrid / reconstruction` 重建部分原生对象；
- 输出 `editability_report.json`，用于验证文字框、原生形状、图片裁剪等结构；
- 默认不额外添加 PowerPoint 阴影、发光、浮雕、反射等效果，除非原图明确需要复刻。

它不是从材料生成 deck 的工具，也不承诺任意图片都能全对象原生重建。当前重点不是限制图片来源，而是限制输入粒度：只承诺单张图片到单页 editable PPTX；多页 PDF、PPTX 或 deck 需要先拆成单张图片后逐页处理。

以下能力目前不作为公开稳定能力承诺：

- PDF 多页自动拆页输入；
- image-only PPTX 自动拆页输入；
- 多页 deck 自动路由与组装；
- 批量页面一致性处理；
- 任意页面的 fully native all-object reconstruction。

## 工作流

![RW Consulting PPT 对话式工作流图解](skills/rw-consulting-ppt/assets/workflow-dialogue.png)

### 1. Preference alignment

开始前先确认 6 件事：

- 受众 / 使用场景；
- live presentation 还是 standalone report deck；
- 页数或图片数；
- 信息密度：简洁、标准、密集；
- 视觉风格 / 主题色；
- 输出格式：PNG、PNG + `image-only PPTX`，或是否需要少数关键页 editable conversion。

### 2. Inputs for PPT Production

把粗糙材料整理成一份生产输入包：

- Context
- Core Question
- Working Thesis
- Storyline
- Page-Level Inputs
- Open Questions

这一步的目标不是直接出图，而是先把要讲的事想清楚。

### 3. Deck Blueprint

为整套 deck 定义：

- 每页标题；
- 每页 governing message；
- 每页 proof object；
- 每页 visual mode；
- 需要补齐或标注的不确定证据。

这一版需要用户确认。没有 blueprint approval，不进入样页。

### 4. Sample brief

先为 1-2 页代表性页面写详细 brief：

- 页面角色；
- page claim；
- proof object；
- visual mother concept；
- must-keep text / number；
- bottom synthesis policy；
- source note / caveat 处理方式。

### 5. Sample gate

先生成样页，再判断是否可以批量。

如果样页看起来像普通 PPT 模板、信息太空、结论太多、证据和图形关系不清楚，应该先改 brief 或 prompt，而不是直接批量生成。

### 6. Batch generation and packaging

样页确认后，才批量生成剩余页面。最后可以用 `skills/rw-consulting-ppt/scripts/package_image_deck.py` 把 PNG 打包成 `image-only PPTX`。

### 7. Selective editable conversion

如果某些页面需要后续频繁改字、改数字、改标签、改表格，可以从最终 PNG 中选取少数关键页面，交给 `ppt-to-editable` 逐页转换成单页 editable PPTX。

这一步是可选的关键页转换，不是整套 deck 自动全量可编辑化。每张图片仍按 `ppt-to-editable` 的稳定能力独立处理：单张图片输入，输出单页 editable PPTX，并附带 `editability_report.json` 说明可编辑文本、原生形状、原生表格、图片裁剪和限制。

## 输出物

默认图片版输出通常包含：

```text
slides/
  slide_01.png
  slide_02.png
  ...
contact_sheet.png
deck-name-image-only.pptx
run_notes.md
```

默认的 `deck-name-image-only.pptx` 里，每一页只有一张完整图片，不包含可编辑文本对象。

如果启用了关键页可编辑化，还会额外交付类似：

```text
editable-pages/
  slide_02-editable.pptx
  slide_02-editability_report.json
  slide_02-preview.png
```

这些 editable PPTX 只覆盖被选中的单页图片。实际可编辑范围以对应的 `editability_report.json` 为准。

## 质量护栏

### Alignment-first

没有确认目标、页数、信息密度、风格和输出格式之前，不开始生产。

### Storyline before design

先确认核心问题、working thesis 和页面逻辑，再写 slide brief。不要一上来就让模型“做几页好看的 PPT”。

### One slide, one claim

每页只有一个最高优先级结论。标题、subtitle、proof object、底部 takeaway 不能互相抢主结论。

### Proof-object-first

每页必须有一个能承载论证的视觉结构，而不是只有卡片、图标和 bullet。

常见 proof object：

- demand validation funnel
- retention funnel
- player landscape
- route map
- value-chain shift
- risk bridge
- capability stack
- decision matrix

### Density preservation

独立阅读型报告页不能为了“干净”而变成空海报。信息密度是管理层报告页的一部分：要减少阅读摩擦，但不能丢掉证据结构。

### Sample rejection

样页出现这些问题时，应拒绝并重写：

- 像普通可编辑 PPT 模板；
- 只有漂亮卡片，没有 proof object；
- 标题、数字、底部结论互相竞争；
- 文本太少，无法独立阅读；
- 全绿、全蓝、全灰等一色到底；
- 证据和结论的视觉连接不成立。

## 适合 / 不适合

适合：

- 行业分析、市场判断、玩家格局、机会评估；
- 客户会议、老板 brainstorm、项目 catch-up 的 recap deck；
- 需要从粗糙材料中提炼 `storyline` 的 PPT；
- 需要高质量图片版咨询页，并可选对少数关键页做后续可编辑化；
- 需要先看样页、再批量生成的工作流。

不适合：

- 需要整套 deck 全页、全对象原生可编辑，且不接受图片页或逐页转换；
- 大量数据表格的精确排版；
- 企业模板规范非常严格的内部汇报；
- 只需要一页视觉海报，不需要咨询论证；
- 已经有完整 PPT，只想简单换皮美化。

## 示例 prompt

### 图片版咨询 deck

### 行业报告分析 PPT

```text
请使用 rw-consulting-ppt，把我上传的行业资料整理成 6 页中文管理层汇报。

目标受众：业务负责人和战略团队
核心问题：这个市场是真需求，还是短期热点？
交付模式：独立阅读型报告页
信息密度：标准咨询密度
视觉风格：管理层报告风，白底，深绿作为强调色，不要互联网模板感
输出格式：PNG + image-only PPTX

如果我没有给出页面大纲，请先帮我提出 storyline 和页面列表，等我确认后再进入样页 brief。
```

### 会议 recap PPT

```text
请使用 rw-consulting-ppt，把这份会议纪要整理成 5 页 recap deck。

目标受众：客户项目组和内部负责人
交付模式：独立阅读型报告页
信息密度：标准
视觉风格：克制、清晰、适合会后对齐
输出格式：PNG

请先梳理本次讨论的核心议题、已形成共识、仍需确认的问题和下一步需要补齐的证据。
不要直接生成图片，先给我 deck blueprint。
```

### 单张 slide 图片转 editable PPTX

```text
请使用 ppt-to-editable，把我上传的这张单页 slide 图片转换成单页 editable PPTX。

当前输入：单张 PNG / JPG / 截图图片
优先目标：让标题、正文、标签、数字等主要文字可编辑
版式目标：尽量贴近原图，不要把原图文字留在背景下再叠一层可编辑文字
处理路线：请先 OCR，保存 OCR 结果和 review；如果页面结构由卡片、表格、行列、流程、图标容器或简单线条组成，优先考虑 hybrid / reconstruction；复杂图片、照片、纹理或细节图标可以保留为紧裁剪图片
样式约束：默认使用扁平 PowerPoint 对象，不要额外添加阴影、发光、浮雕、反射、柔边或主题效果，除非原图明确有这个效果
交付物：单页 editable PPTX、预览图、editability_report.json，并说明哪些元素可编辑、哪些元素仍是图片裁剪
```

### 结构化页面优先 reconstruction

```text
请使用 ppt-to-editable，把这张结构化业务 slide 图片转换成单页 editable PPTX。

这页主要由表格、卡片、分隔线、标签和数字组成，请优先走 hybrid / reconstruction，而不是只做 clean-background + editable text。

要求：
- 文字尽量变成可编辑文本框；
- 表格或明显行列结构尽量重建为原生 PowerPoint table；
- 简单矩形、圆形、线条、分隔线尽量重建为原生 PowerPoint shape / line；
- 图标、照片、复杂纹理可以用紧裁剪图片保留；
- 不要使用整页背景伪装 reconstruction；
- 不要添加原图没有的阴影或 PowerPoint 特效；
- 输出 editability_report.json 证明 editable text、native shapes、native tables、source crops 的数量和限制。
```

## 目录结构

```text
rw-consulting-ppt/
  README.md
  LICENSE
  skills/
    rw-consulting-ppt/
      SKILL.md
      agents/
      assets/
      examples/
      references/
      scripts/
    ppt-to-editable/
      SKILL.md
      agents/
      references/
      scripts/
```

## FAQ

### 为什么默认不是 editable PPTX？

因为 `rw-consulting-ppt` 的核心不是从材料直接生成原生 PPT 组件，而是让 AI 先生成完整的咨询页图像。它优先保证咨询页的视觉完整度、信息密度和表达质量。

如果你已经有一张成品图片，并希望恢复部分编辑能力，可以使用同仓库的 `ppt-to-editable`。目前 `ppt-to-editable` 聚焦单张图片到单页 editable PPTX，不承诺多页 deck 自动转换或任意页面的全对象原生重建。

### 生成的 PPTX 还能修改吗？

分两种情况：

- `rw-consulting-ppt` 默认生成的是 `image-only PPTX`：每页是一张完整图片，可以整体移动、替换、插入，但不能逐字编辑文本。
- 如果你把某些关键页面再交给 `ppt-to-editable` 转换，那么这些页面会变成单页 editable PPTX；其中被恢复为 PowerPoint 文本框、原生形状、原生表格的部分可以修改，仍作为图片裁剪保留的复杂视觉元素不能逐对象编辑。

实际可编辑范围以 `editability_report.json` 为准。需要改大段内容时，通常仍建议回到 slide brief 或 prompt 层重生成；需要小范围改字、改数字、改标签时，适合使用 `ppt-to-editable`。

### 为什么一定要先确认样页？

图片生成一旦批量跑偏，返工成本很高。`sample gate` 用来先验证风格、信息密度、文本可读性和 proof object 是否成立。

### 可以只生成 PNG，不生成 PPTX 吗？

可以。默认图片版 PPTX 只是把已确认的 PNG 机械打包成演示文件；如果不需要演示文件，可以只交付 PNG。关键页 editable conversion 是额外步骤，只在你明确需要时再做。

### 可以用于英文 deck 吗？

可以，但默认示例和质量规则以中文管理层报告页为主。英文 deck 也应保留相同原则：alignment-first、storyline before design、proof-object-first。

## 交流与答疑

如果你下载并使用这个 skill，欢迎扫码加入微信群一起讨论 AI x Consulting 工作流、PPT 生成效果和使用问题。二维码可能会过期，过期后可以通过 GitHub issue 提醒更新。

<p>
  <img src="skills/rw-consulting-ppt/assets/wechat-group-qr.jpg" alt="AI X Consulting 讨论群二维码" width="320">
</p>
