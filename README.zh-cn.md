# Contract Pack: Giving Aircraft a Purpose（GAP）简体中文汉化

本仓库是 **GAP** 的简体中文汉化分支：把原版散落在 55 个 `.cfg` 里的
**硬编码英文全部替换为 KSP 官方 Localization 键**（`#loc_GAP_*`），
并附带完整简体中文。

- 原版：<https://github.com/inigmatus/GAP>
- 玩法、数值、条件、奖励**完全未改动**，只改文本。

---

## 安装

1. 确保已安装依赖：
   - **Contract Configurator** 2.11 或更高
   - **Module Manager** 4.2.3 或更高
2. 把**本仓库的内容**放入一个名为 `GAP` 的文件夹：
   ```
   Kerbal Space Program/GameData/ContractPacks/GAP/
   ```
   > ⚠️ **文件夹名必须是 `GAP`**。合同与机构的图标路径写死了
   > `ContractPacks/GAP/Assets/Flags/...`，改名会导致图标丢失。
   > 若你的克隆目录叫 `GAP-zh`，请改名为 `GAP`（或复制一份并改名）再放入。

   最终应存在：
   ```
   GameData/ContractPacks/GAP/Localization/zh-cn.cfg
   GameData/ContractPacks/GAP/Localization/en-us.cfg
   ```
3. 游戏语言设为**简体中文**（Settings → General → Language → 中文）。

> 若游戏语言不是中文/英文，界面会回退显示为该键的英文——因为
> `en-us.cfg` 定义了全部键。想要别的语言？见 `LOCALIZATION.md` 第 5 节，
> 复制 `en-us.cfg` 改成对应语言代码即可，**无需改动任何合同文件**。

---

## 汉化范围

| 类别 | 内容 |
|---|---|
| 机构 | 让飞机有用武之地、莱特航空、SSI 航天、KSC 航空、KSC 海岸警卫队（名称 + 简介） |
| 合同组 | GAP、KSC 航空、KSC 海岸警卫队、原型市场（显示名 + 提示） |
| 合同文本 | 标题、通用标题、详细描述、通用描述、简报、备注、完成提示（51 个合同） |
| 参数文本 | 全部参数标题、等待前/进行中/完成文本（含动态数字拼接） |
| 对话框 | ATC 陆空通话正文 + 说话者名称（56 处） |
| 导航点 | 机场/跑道/机库等标记名称（38 处） |

共 **504 个本地化键**，覆盖原版 1161 处硬编码文本，无残留。

术语优先采用**游戏本体官方译名**：小岛机场（Island Airfield）、甜品机场
（Dessert Airfield）、乌墨瑞发射台（Woomerang）、海豚鱼发射台（Mahi Mahi）、
航天器机库（Spaceplane Hangar）、坎巴拉人（Kerbal）等。

---

## 技术要点（给维护者）

- 键命名空间：`#loc_GAP_*`，已对整机 GameData 的 19997 个键做过查重，**零冲突**。
- 含动态数字的文本用 `DATA` 变量 + 表达式拼接，**变量名 = 键名去掉 `#`**。
- 文件编码 **UTF-8 无 BOM**；值内换行用 `\n`，双引号用 `\"`。

完整说明与维护工具见 **[LOCALIZATION.md](LOCALIZATION.md)**；
实机验证状态与待确认清单见 **[VALIDATION.md](VALIDATION.md)**。

---

## 许可

沿用原版 GAP 的许可，见 [LICENSE.txt](LICENSE.txt)。本汉化仅改动文本，
不主张额外权利；欢迎把汉化合并回上游。
