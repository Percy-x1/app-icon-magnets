# 脚手架使用

初始化器创建独立目录并复制脚本和精确轮廓，拒绝覆盖现有目录。不要把工作文件写回安装的 skill 目录。

## 环境和输入

项目根目录建立虚拟环境，按 requirements.txt 安装。可复用已验证的环境，但先验证依赖可导入；临时目录中的旧 venv 可能只剩 python 链接，不一定还是有效虚拟环境。不要意外安装到系统或用户全局 Python。

把原 SVG 放到 assets，另写 prepare.py 生成 assets/design_vectors.json。示例（实际图形需先核对来源、路径、填充和颜色）：

```python
from pathlib import Path
import json
from vector_utils import make
R = Path(__file__).resolve().parent.parent
parts = make('Approved.svg', 28, '#FFFFFF', 'White_Mark')
specs = [{'name':'Example', 'label':'示例', 'base_color':'#1752FF',
          'parts':parts, 'center':[0,0], 'strict_svg':True}]
(R/'assets/design_vectors.json').write_text(json.dumps(specs,indent=2))
```

`vector_utils.make` 支持 `indices=[...]` 和 `frame=[xmin,xmax,ymin,ymax]`。多路径多色应共享 frame，以同一 scale 映射，按真实绘制顺序组织 parts。它把每个填充外环与洞生成一项，含 `loops`、`area_mm2` 和 `bounds_mm`。每个 loop 包含 `line` 的两个端点或 `cubic` 的四个控制点，坐标为 mm、Y 已翻成 CAD 向上。面积为采样估算，Fusion profile 以合适容差比对。请勿未经核对用于开放描边、非零复合填充或复杂遮罩。

`clip_to_tile: true` 可用于确需裁到板边的图案。`join_color: '#RRGGBB'` 仅合并该颜色的相连/重叠路径；不应拿来合并互不相连且会报错的工具体。端点退化等问题按 geometry.md 处理。来源报告保存在 reports，保留原文件，不能只保存已改色的 SVG。

## 构建和验证

1. 运行 prepare.py；确认 design_vectors 的实际图形、颜色和款数。
2. 使用当前连接的 Fusion MCP 运行生成的 `scripts/build_fusion.py`。本地 HTTP 辅助器用法：

```sh
FUSION_MCP_URL=http://127.0.0.1:27182/mcp python scripts/mcp_call.py script scripts/build_fusion.py
```

工具名/协议变化时先发现当前接口，不凭旧工具名推测。脚本执行结果应为 success，且 reports/fusion_validation.json 覆盖全部指定款式，不能只看进程退出码。Fusion SDK 只存在于 Fusion 进程内，不能用普通 Python 直接运行该脚本。

3. `python scripts/verify_geometry.py` 检查正实体网格；颜色还需与 design_vectors 对照。原生报告会按已完成 name 跳过，修改某一款设计时先从校验报告中移除该款记录再重建；保留此前成品到另一输出目录，避免以旧验证结果跳过新版。
4. `MPLCONFIGDIR=<可写缓存目录> python scripts/build_projects.py`：生成每款独立 3MF 和 product preview。此脚手架默认不自动合并合集。需要合集时在同一构建器中调用 `build(specs, path)` 并加入 manifest，保持一图标一盘。
5. 适配/发现 BambuStudio CLI 路径，可通过 `BAMBU_STUDIO_PATH` 指定（macOS 默认 `/Applications/BambuStudio.app/Contents/MacOS/BambuStudio`），运行 `python scripts/readback_validate.py`，确认原生 info、负件和参数差异检查。
6. 另存切片验证文件，检查 result.json 的结果/警告/盘数/每盘实际耗材；仅在通过后交付 individual 中相应 3MF。

脚手架的 4 mm、负零件变换以及模板索引是这套系列的具体验证条件；用户修改尺寸或打印模板后要同时更新几何、打包与验证依据。不要为了让检查“通过”而移除真实不匹配的断言。

## 本地打印模板

随包 `print-template.3mf` 是用户这套系列的个人配置种子，包含用于参考的中性板件几何；构建器只继承配置、负零件与包结构，生成交付时应替换正实体和缩略图。模板不代表要把旧图标加入新任务，也不隐含上传模板或连接打印机的授权。初始化时校验 template-manifest.json 哈希。

使用另一个用户提供的配置时应重新读取真实元数据和索引结构，再适配脚本；不要直接覆盖这个随包模板而保留旧哈希或旧索引假设。
