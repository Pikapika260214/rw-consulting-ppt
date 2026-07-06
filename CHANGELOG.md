# Changelog

## v3 Two-Mode Preview

- `ppt-to-editable` 合并回 `rw-consulting-ppt` 仓库，仍作为 `skills/ppt-to-editable` 下的独立 skill 发布；不会覆盖 `skills/rw-consulting-ppt`。
- README 和 `UPGRADE.md` 新增老用户单独升级 `ppt-to-editable` 的可复制 prompt。
- 发布入口收敛为两种：单页省 token 模式、多页多 Agent 高质量模式。
- 多页多 Agent 高质量模式的用户提示已强化：非常消耗 token，建议仅限 Codex Pro 订阅用户使用。
- 多页顺序省 token 模式已下线：`multi-page-sequential-token-saving` 和 `worker_mode=sequential` 不再作为正式发布能力接受。
- 保留多页多 Agent 高质量模式：`conversion_mode_gate.user_choice = "multi-agent-high-quality"`，适合质量优先、能接受更高 token 消耗的用户。
- 保留 `WORKER_COMPACT_PROTOCOL.md`：多页任务默认读取短协议、slide job manifest、page conversion contract、crop manifest contract，长 reference 只在卡住或 QA 失败时按需读取。
- `deck_controller.py` 现在会为每个 run 复制本次专用 `WORKER_COMPACT_PROTOCOL.md`，并在 `deck_manifest.json` 记录 compact-first reference policy。
- 多 Agent 模式仍强制每页独立 worker，避免高质量模式被 controller 线程偷跑。
- `qa_summary.json` 新增 `fallback_references_read`，用于记录是否读取过长 reference；没有读取时应为空列表。
- README、UPGRADE、SKILL.md 更新为两种入口：单页省 token、多页多 Agent 高质量。

## v3.1 Preview

- 新增共享视觉策略规则 `visual_strategy_rules.py`，统一 high-risk visual type 判断。
- 扩展 high-risk 类型：复杂流程卡、渐变/纹理箭头条、复杂矩阵背景、产品图/复杂图标、source-specific process matrix 等。
- `check_reconstruction_visual_strategy.py` 不再允许 `override_reason` 绕过 high-risk native redraw warning。
- `write_slide_qa_summary_from_single_page.py` 不再用 `not-reported` 填补缺失的 `region_crop_plan`。
- `deck_controller.py` 在 finalize 收页时会反查 `source_reconstruction_plan.json`、`visual_strategy_report.json` 和 `packaging_report.json`，阻止 high-risk 区域 native 重建后伪装成通过。
- `region_crop_plan` 成功页必须使用结构化对象，并包含 `source_bbox_px` 和 `reason`。
- 文档强化：`reconstruction-first != all-native`，复杂视觉优先 crop/textless crop，再叠加可编辑文字。

## v3.0 Preview

- 新增 image-only `.pptx` 多页 deck controller。
- 集成成熟单页 reconstruction / mixed reconstruction 脚本链路。
- 支持 per-slide Agent 工作流，每页独立转换后合并 final deck。
- 新增 OCR runtime setup/check 流程。
- 新增 `UPGRADE.md`，给已安装旧版 skill 的用户说明如何更新和验证。
- 新增转换前确认状态机：`deck_controller.py --probe` 先只读检查 deck/OCR 状态，输出 `gates_file_template`。
- 新增 Conversion Mode Gate，避免默认跑完整 deck 造成不必要 token 消耗。
- `deck_controller.py` 新增 `--gates-file` 和 `--slides`，支持记录用户 conversion mode、OCR、范围、worker、token 确认，只为指定页生成任务并合成指定页 deck。
- `gates.json` 升级为 `ppt-to-editable-gates-v3`：新增 `conversion_mode_gate`；OCR 已可用时自动记录通过；页码范围、worker 授权、token 成本确认、内容共享确认合并为 `scope_and_worker_gate`。
- 新增 `prepare_worker_dispatch.py`：初始化后先生成 worker 派发报告，未明确授权时阻止外部 Codex worker。
- 优化 Scope + Worker Gate 用户提问：用户看到的是“转几页、页数越多 token 越多、每页会由独立转换任务读取页面内容”，不再要求用户理解 `app-native worker` 或 `Codex worker runtime`。
- `deck_controller.py` 新增硬约束：初始化时必须显式传 `--gates-file`，并传 `--all-slides` 或 `--slides`；OCR 未达到 `passed-text-usable` 时默认拒绝创建质量转换任务。
- `setup_ocr_runtime.py --yes` 新增硬约束：必须传入已记录用户确认的 `--gates-file`，避免未授权安装依赖或下载 OCR 模型。
- 新增 deck-level QA、失败页 fallback sticker、PowerPoint render QA。
- 强化复杂视觉策略：复杂图标、路径、阴影、照片、渐变模块优先 crop/textless crop，不强行 native 重建。
- 强化非文字结构保护：textless crop 不应抹掉箭头、路线、步骤编号、卡片边缘、图标等结构元素。
