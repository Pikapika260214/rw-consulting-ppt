# 工具接口

在构建脚本中将本 Skill 的 `scripts` 绝对路径加入 `sys.path`，然后 `from editable_ppt import Deck`。路径以本次读取的 Skill 位置为准，不依赖项目目录。Python 3.10+ 需要 `python-pptx` 和 `Pillow`；使用已安装依赖的运行时，缺失时再安装 `requirements.txt`。

```python
from editable_ppt import Deck
deck = Deck("input.png", "output")
deck.rect(20, 20, 400, 100, fill="#F4F6F8", line="#777777")
deck.text(30, 30, 380, 80, "示例文字", size_px=28,
          font="Microsoft YaHei", container_bbox=(20, 20, 400, 100))
result = deck.finish()
# 将 result["preview"] 交给当前环境的图片查看工具；先检查渲染状态。
```

几何与字号单位均为源图像素，映射为 96 px/in；这是内部换算约定，不是源图真实 DPI 判断。示例坐标与字体只示范调用方式。若需要特定物理页面尺寸，保持几何、字号同比例换算，或采用原生 API 构建。

| 接口 | 用法 |
|---|---|
| `Deck(source_png, out_dir)` | 新建与源图同宽高比的一页空白 PPT |
| `text(x,y,w,h,text,size_px=28,color,bold,align,font,line_spacing)` | 字符串支持换行；也接受 run 字典列表，字段为 `text/color/bold/font/size_px` |
| `text(..., container_bbox=(x,y,w,h))` | 可选：文本框超出指定容器时报警；不等于真实字形边界检测 |
| `rect(x,y,w,h,fill,line,radius=False)` | 矩形或圆角矩形；返回原生 shape，可继续调整 |
| `line(x1,y1,x2,y2,color,width,dash,arrow)` | `dash="dash"`；`arrow="start"/"end"/"both"` |
| `crop(source_bbox,target_bbox=None)` | bbox 为 `(x,y,w,h)`，源区域必须在图内；默认原位放置，内部像素不可编辑 |
| `finish(render=True)` | 写入 `deliverables/editable.pptx`、简短 JSON 报告；成功渲染时另有 `preview.png` 和 Office 验证记录 |

所有绘图函数返回对象。字体应根据源图和本机可用字体选择；适配估算不自动修改字号、文字或布局。估算无法代替真实 PowerPoint 字体回退、自动换行、粗体和复杂排版的检查。

直接使用 `deck.slide` / `deck.presentation` 可添加原生表格、图表、特殊形状和显式效果；这些对象不会在 `finish()` 时被批量清除主题样式。需要对新建直接对象去除意外继承效果时，显式调用 `deck.normalize_inherited_effects(shape)`，也可传对象列表；省略参数会处理当前页，含分组。它保留显式效果。

`text(..., font_path="<字体文件>")` 可为宽度估算指定本机字体文件，run 也支持此字段；它不改变 PPT 的字体名称。对象统计含分组及其子对象；文字计数不是文字准确率或完整可编辑性证明。

`finish(render=False)` 只构建，不能标为渲染通过。Office 不可用或失败时检查返回状态和报告中的原因；旧预览不能充当本次成功证据。渲染脚本随 Skill 附带，保留页面宽高比；它只关闭本次打开的文档。
