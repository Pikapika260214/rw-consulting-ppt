# Examples

这个 release candidate 不包含真实业务 deck、历史测试 deck 或私有素材。

建议用户自己准备一个最小测试文件：

```text
examples/input/sample-image-only.pptx
```

要求：
- `.pptx` 文件；
- 每页是一张铺满页面的 PNG；
- 先用 1-3 页测试，再扩大到更多页；
- 不要用包含隐私、客户信息或版权不明素材的 deck 做公开测试。

建议测试命令：

```powershell
python ../skills/ppt-to-editable/scripts/deck_controller.py input/sample-image-only.pptx --probe --ocr-python ../.venv-ocr-3-0/Scripts/python.exe
python ../skills/ppt-to-editable/scripts/deck_controller.py input/sample-image-only.pptx --run-dir runs/sample --gates-file gates.json --all-slides --ocr-python ../.venv-ocr-3-0/Scripts/python.exe
python ../skills/ppt-to-editable/scripts/deck_controller.py input/sample-image-only.pptx --run-dir runs/sample --finalize
```

输出：

```text
examples/runs/sample/output/final-deck.pptx
examples/runs/sample/output/deck-level-qa-report.json
```
