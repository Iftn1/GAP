# 验证状态（Validation）

本汉化**未在游戏内实机运行验证**（制作环境未安装可运行的 KSP/ContractConfigurator）。
为保证可信度，下面把"已用证据确认的"与"仍需你实机确认的"严格分开。

---

## 一、已取证确认（机制级，有据可查）

这些结论不是推测，每一条都有本机取证来源。

| 结论 | 取证依据 |
|---|---|
| `#loc_*` 键在**合同级**文本字段被解析 | 同一环境的 KUM 合同包（已跑通）的 CC 解析日志：`synopsis = 拦截敌方单位，以便…`，而其 cfg 里写的是 `#loc_KUM_..._synopsis` |
| `#loc_*` 键在**深层嵌套 PARAMETER** 字段被解析 | KUM 日志 `preWaitText = 前往会合点进行识别`，cfg 里为 `preWaitText = #loc_KUM_ident_preWaitText`（`Contracts/required_uav.cfg:317`） |
| `DATA` 变量 + `@/变量 + @/动态值` 拼接成立 | KUM 日志 dump 出 `title = @locTitle + " (" + @titlePeriod + ")"` 与 `locTitle = 荒地空中编队拦截` |
| `AGENT` 的 `title`/`description` 支持模组自带本地化键 | Contract Configurator 自带机构配置即如此：`Agencies/Explore.cfg:13` → `title = #cc.agency.Exploration.name` |
| `CONTRACT_GROUP` 的 `displayName` 支持本地化键 | KUM 日志：`KUM:displayName = 军械库作战合同` |
| 换行用 `\n` 而非 `&br;` | 官方英文词典自身即如此（`Squad` en-us 的 `#autoLOC_8005077`）；`Squad/Localization/dictionary.cfg` 亦用 `\n`；而 `&br;` 是 CC 的历史标记，其替换发生在配置解析期，文本移入本地化文件后有原样显示的风险 |
| 值内双引号写作 `\"` | `Squad/Localization/dictionary.cfg`：`导航点\"<<1>>\"已删除。` |
| 键空间**零冲突** | 扫描整机 GameData：78 个 `Localization` 目录、277 个 cfg、**19997 个键**，`loc_GAP` 前缀零命中；构建后复查与既有模组冲突为 **0** |
| 除文本外**结构未变** | 55 个 cfg 与原文件**逐节点结构比对**：意外差异 **0**（差异只出现在被本地化的字段与新增的 DATA 块） |
| 无残留硬编码、无孤儿键 | cfg 引用键 504 = 定义键 504；范围内残留英文 **0**；两种语言键集完全一致，重复定义 0 |

---

## 二、仍需你实机确认（无先例，属推断）

以下三类字段在可考证范围内**没有已跑通的前例**（KUM 未使用它们），
它们依赖 CC 对字符串字段的通用本地化处理。**若 CC 对某字段不做本地化，
该字段会直接显示成 `#loc_GAP_...` 原文**（这是最容易识别的失败症状）。

- [ ] `DIALOG_BOX` → `TEXT.text`（ATC 对话正文，56 处）
- [ ] `DIALOG_BOX` → `IMAGE.characterName`（说话者名称，56 处）
- [ ] `WaypointGenerator` → `PQS_CITY.name`（导航点名称，38 处）

另外建议顺带确认：

- [ ] `\n` 换行在合同**详细描述**与**完成提示**里的实际渲染（应为分段换行，而非显示 `\n` 字面量）
- [ ] 合同标题拼接是否自然：应显示为 `101 号航班 － 机组 1 人，乘客 4`
- [ ] 参数清单是否通顺：应显示为 `你的飞机必须 / 有机翼 / 有认证飞行员 / 载入全部 4 名乘客 / 在小岛机场着陆 …`
- [ ] 若你还装了**第三方 ModuleManager 补丁**，且其中有按 `name = Island Airfield` 之类匹配 GAP 导航点的写法，需确认未受影响（GAP 自身用 `index` 引用航点，不受影响）

---

## 三、验证步骤

1. **安装**：把 `GAP` 文件夹放到
   `Kerbal Space Program/GameData/ContractPacks/GAP/`
   （确认 `Localization/zh-cn.cfg` 存在），游戏语言设为简体中文。
2. **确保日志开启**：检查是否存在
   `GameData/ContractConfigurator/ContractConfigurator.cfg`；
   若没有，把同目录的 `ContractConfigurator.cfg.default` 复制并改名为
   `ContractConfigurator.cfg`（这一步只是打开详细日志，不影响游戏）。
3. **启动游戏到主菜单**即可（合同类型在主菜单阶段加载）。
4. **看日志**：`GameData/ContractConfigurator/log/GAP/*.log`
   每个合同类型一个文件，里面是**解析后的配置**。搜索：
   - `text = `、`characterName = `、`name = ` —— 若后面是中文，说明第二节那三类字段**支持**本地化；
   - 若出现 `#loc_GAP_` 字样，说明该字段**未**被解析。
5. **进游戏看**：载入存档 → 任务控制中心 → 筛 `GAP` / `KSC 航空`；
   看标题、描述、简报、备注、参数清单；接受一个飞行合同触发 ATC 对话框。
6. **全局兜底检查**：在 `KSP.log` 中搜索 `#loc_GAP`。若在**任何**界面看到
   `#loc_GAP_...` 原文，把对应的 `.log` 发来即可定位到具体字段。

---

## 四、如果发现问题

把下面任一文件发我，我可以直接定位到键与字段：

- `GameData/ContractConfigurator/log/GAP/<合同名>.log`（最有用：含解析后的整份配置）
- `KSP.log`

修复方式很轻：若是某字段不支持本地化，把该字段的值改回英文原文即可
（`Tools/localization/` 里的脚本有完整映射，可精准回退单个字段）。
