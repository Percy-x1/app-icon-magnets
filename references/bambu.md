# Bambu 3MF 与参数保留

## 继承和新增

将用户最新项目作为权威参考，先读 ZIP 内容、`Metadata/project_settings.config`、`Metadata/model_settings.config`、主 model 和外部 mesh 文件。不要依赖缩略图判断对象实际方向/结构。

新增分色体需要重排虚拟耗材索引时，同步处理所有相关索引，保留各耗材原参数：本模板 20 项普通耗材数组，39 项耗材变体数组（按 filament_self_index 分组），40/80 项的 2/4 元分组，以及 different_settings_to_system 的前两项和耗材项、flush_volumes_matrix 的行列索引。不要用“所有 list 都截前 N 项”或字符串替换 `==2` 连带改变 `==20`。不相关的速度、机器和流程数组完全不动。配色列表应仅含实际使用颜色，各 part 的 extruder 指向正确虚拟槽。

保留负零件的 mesh、component transform 和 `part subtype="negative_part"` 配置。随包模板的圆柱原始 mesh 是大尺寸通用体，实际孔尺寸来自缩放矩阵；不能用原始 mesh 包围盒直接认定孔径。不能只复制 subtype 而漏掉几何或相对变换。

正实体原生为 Z0..4、Logo 在 Z4 时，绕 X 轴 180°并平移 Z=4：3MF 12 值为 `1 0 0 0 -1 0 0 0 -1 X Y 4`。保证是旋转而非镜像，变换后正实体 Z 最小为 0。负零件保留局部变换，与装配整体一起旋转。不同原始朝向需计算实际矩阵，不机械套这个值。

多盘坐标按实际布局计算。历史本机 plate pitch 为 307.2 mm；行列数和当前软件布局需验证，不能把固定 4 列套给所有盘数。底片/清料塔的每盘位置要映射到相应盘；单盘文件需把选中原盘的塔坐标放到 index 0。

## 拆分用户合集，打印配置完全保留

这是独立路径，不应重新建模或套个人模板：
1. 从 plate 的 model_instance 找出 assembly/build 实例和 object 配置；保留选中图标所有正/负 part。
2. 从主 assembly 追踪所有 component 的 `p:path` 和 objectid，保留传递依赖。不同图标可能共用一个外部 mesh 文件内的同一负零件，不得按文件编号猜依赖。
3. 过滤其他对象/盘，保留原 ID、局部 component transform、part 配置及 mesh；仅做必要的盘编号、全局 X/Y 平移和盘索引资源映射。不能改变旋转、Z、相对孔位。
4. project_settings 尽量原样复制；若需要选中盘的清料塔坐标重映射，仅修改该索引。切片序列、cut_information、关系文件、缩略图依赖一致。保留未使用的耗材定义，避免为“清理”而改配置。
5. 对比 mesh/part 的规范化 XML、参数差异、源文件哈希，再做原生读取。不能仅凭 ZIP 可打开就宣布保留配置。

## 序列化与验证

- 3MF core 和 production 命名空间正确，BambuStudio namespace 声明保留。
- 包关系 XML 使用无前缀 `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">` 和 `<Relationship>`。本机 Bambu 曾对 `ns0:Relationship` 读取为 0 个对象；XML 语法合法不代表应用兼容。
- 生成时注意重名/ID 引用、负零件 subtype、实例数量及所有 part 的颜色。
- 正实体整体必须 40×40×4；负体可能略越过背面，不把负体包围盒误当正体尺寸。
- `--info` 是只读检查；检查实际正 part 数、facets、manifold 等。它可能不把负零件计入 number_of_parts，负体需要另读 XML 验证。
- 用隔离 datadir 保存 CLI 状态。发现当前 BambuStudio 可执行路径，不固定软件版本。切片示意：

```sh
BambuStudio --datadir <project>/.bambu-check --info <delivery.3mf>
BambuStudio --datadir <project>/.bambu-slice --slice 0 --export-3mf Check.3mf --outputdir <project>/reports/sliced <delivery.3mf>
```

`--outputdir` 配合 `--export-3mf` 使用 basename，避免路径重复拼接。确认 result.json return_code=0、盘数正确、每盘实际耗材数与方案一致、warning_message 已处理。标准 0.20 mm/4 mm 组合应为 20 层，但新配置下不要硬编码层数。

切片测试项目不是交付源。保留原交付 SHA，对比测试前后未改变文件。默认不导出 G-code 给用户，也不连接打印机或发起打印。
