# APP 图标冰箱贴 Skill

用 Codex 配合 Autodesk Fusion 和 Bambu Studio，制作可编辑、可分色打印的 APP 图标冰箱贴。

## 默认规格

- 40 × 40 × 4 mm，iOS 60% 平滑圆角。
- 图案与底板表面齐平，使用独立实体分色。
- 优先使用用户指定或核对过版本的 SVG；支持从官方可编辑矢量 PDF 提取原始曲线。
- 渐变根据要求转纯色；按实际 AMS 颜色数量安排。
- 沿用参考 3MF 的打印参数、负零件与孔位；Logo 面朝下。
- 每款独立 3MF，按要求制作一款一盘的合集；交付前进行网格检查、Bambu Studio 读取和切片验证。

用户的新要求和提供的参考图、SVG、3MF 优先于默认规格。无孔版按用户要求制作。

## 使用环境

1. 能加载本地 skills 的 Codex 环境。
2. Autodesk Fusion，用于执行原生建模并导出 F3D、STEP、STL。
3. 可连接的 Fusion MCP 服务，提供 `fusion_mcp_execute` 脚本执行能力。请按所使用的 Fusion 版本及 MCP 服务说明配置。默认地址为 `http://127.0.0.1:27182/mcp`，可通过 `FUSION_MCP_URL` 修改。
4. Bambu Studio，用于项目读取及切片验证。
5. Python 虚拟环境，以及脚手架 requirements.txt 中的依赖。

脚手架已在 macOS 上验证。其他系统需调整本机应用路径；Bambu Studio 路径可通过 `BAMBU_STUDIO_PATH` 配置。仅切片打印现成 3MF 时无需 Fusion；生成、修改图标及编辑 F3D 时需要 Fusion。

## 安装

将本仓库作为 `app-icon-magnets` 文件夹放到本地 skills 目录。例如：

```sh
git clone https://github.com/Percy-x1/app-icon-magnets.git "${CODEX_HOME:-$HOME/.codex}/skills/app-icon-magnets"
```

目录应直接包含 `SKILL.md`、`agents`、`assets`、`scripts`、`references`。已有同名目录时，请先自行备份并比较版本，避免覆盖个人修改。

## 调用示例

> 使用 $app-icon-magnets 制作一个陌陌图标冰箱贴，沿用默认规格，使用蓝白两色，交付独立 3MF。

> 使用 $app-icon-magnets 制作 XX 图标，同时交付每款独立的 3MF 和 F3D，保留可编辑草图、参数及建模时间线。

> 使用 $app-icon-magnets 拆分这份 3MF 合集，每款单独一个文件，保留所有负零件、孔位和打印参数。

默认只交付 3MF；F3D、STEP、STL 在建模过程中保存，要求源文件时再一并交付。

## 脚手架

```sh
python3 scripts/init_project.py --output /path/to/new-project
```

该命令创建新目录，复制建模、打包和验证脚本及参考模板。随后由智能体核对素材、准备 `assets/design_vectors.json` 并调用 Fusion。它拒绝覆盖已有目录。

详细步骤见 [SKILL.md](SKILL.md)、[数据格式与脚本](references/scripts.md)、[几何处理](references/geometry.md) 和 [3MF 参数保留](references/bambu.md)。

## 打印参考模板

随包模板包含中性参考板件、圆柱负零件与 P1S 0.4 mm / 0.20 mm / 3 层墙 / 15% 填充配置，不包含现成 APP 图标。精确的系列圆角轮廓单独保存在 assets/ios60_outline.json。

打包器目前针对模板的 20 耗材、39 变体索引结构。用户使用其他打印机、材料、孔位或新参考 3MF 时，应先读取真实配置并适配；不能用这个模板重置用户参数。品牌图形与素材按其各自来源和授权使用。
