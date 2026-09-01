# 2050 Firefall Core Balance Adapter — Agent 开发指南

## 1. 适用范围

本文件适用于本 Mod 根目录及全部子目录。本 Mod 是加载在 `[1.13] Tech & Res` 和 `2050: The Fire Falls` 之后的个人适配层，只拥有统一战争 10% 恶名、AI 宣称收复、殖民塑形和通用平衡功能。

判断定义是否正确时，必须以“Victoria 3 原版 + Tech & Res + Firefall + 本 Mod”的实际加载顺序形成的最终数据库为准。

项目身份以 `.metadata/metadata.json` 为准：

- Mod ID：`com.wyb.2050-firefall-core-balance`
- Victoria 3：`1.13.*`
- 依赖：`2050: The Fire Falls`、`[1.13] Tech & Res`
- 推荐顺序：Tech & Res → Firefall → 本 Mod

## 2. 开工前检查

1. 运行 `git status --short --branch`，保留用户已有修改。
2. 用 `rg --files -uu -g '!/.git/**'` 盘点文件，用 `rg -n` 同时搜索定义、引用、本地化和持久变量。
3. 确认游戏根目录、Workshop 根目录、依赖版本和真实加载顺序，不把机器绝对路径写入实现。
4. 对要改的顶层键依次检查原版、Tech & Res、Firefall 和本 Mod 的最终定义。
5. 在当前安装版本的相同目录、脚本类别和 scope 中寻找已工作的语法先例。

## 3. 模块所有权

### 3.1 统一战争 10% 恶名

所有文件：

- `common/game_rules/ffpa_union_war_rules.txt`
- `common/script_values/ffpa_union_war_values.txt`
- `common/diplomatic_plays/ffpa_union_war_plays.txt`
- `common/war_goal_types/ffpa_union_war_goal.txt`
- `common/scripted_effects/ffpa_union_war_effects.txt`
- 两份本地化中的统一战争键

三个 `REPLACE:` 定义必须在 Firefall 更新后逐段比较，只允许保留 10% 分支这一项差异。`uw_infamy_cost` 的选项顺序就是 UI 顺序。

### 3.2 殖民塑形

所有文件或定义：

- `common/ai_strategies/zzzz_ffpa_colonial_region_stances.txt`
- `common/defines/zzzz_ffpa_colonial_shape_defines.txt`
- `common/institutions/00_institutions.txt` 中的 `institution_colonial_affairs`

AI 地区评分只控制殖民区域；`NDiplomacy` 只控制殖民地内部省份选择；殖民制度只控制增长速度。define 同时影响 AI 和玩家。本 Mod 不拥有同时发展的殖民地数量上限。

### 3.3 通用平衡与生命周期

所有文件或定义：

- `common/history/global/zzz_ffpa_global.txt`
- `common/static_modifiers/ffpa_modifiers.txt`
- `common/scripted_effects/ffpa_innovation_effects.txt`
- `common/on_actions/ffpa_balance_on_actions.txt`
- `common/institutions/00_institutions.txt` 中其余六个制度
- `common/production_methods/ffpa_trade_center.txt`
- 两份本地化中的人口恢复和科研键

创新上限动态 modifier 图的读取旧值、移除旧 modifier 和重建镜像顺序属于逻辑本身。`ffpa_innovation_cap_mirror_value` 是存档接口，改变含义必须创建版本化新键并迁移。

贸易 PM 使用 `INJECT:`，只能增加指定字段，不复制完整 PM，也不接管自动 PM 选择逻辑。

### 3.4 AI 宣称收复

所有文件或定义：

- `common/scripted_triggers/ffpa_ai_claim_triggers.txt`
- `common/ai_strategies/zzzz_ffpa_claim_reclamation_strategy.txt`
- 两份本地化中的 `ai_strategy_uw_reclaim_homelands_desc`

`INJECT:ai_strategy_uw_reclaim_homelands` 完整接管 Firefall 战略的 `possible`、`weight`、`diplomatic_play_boldness`、`aggression`、`state_value`、`secret_goal_scores`、`wargoal_weights` 和 `wargoal_scores` 八个子表。Firefall 更新后必须逐段比较，其他顶层字段继续由上游拥有。

实际宣称优先于无宣称文化故土，但普通征服不得被写成绝对禁令。分权国家持有的宣称不属于可执行收复目标。本模块不拥有全局战略刷新 define，不使用周期 on_action 或持久变量强制 `set_strategy`。

## 4. 外部边界

本 Mod 不拥有：

- Tech & Res 自动 PM 兼容、生成器或生成产物；
- 低人力亏损建筑清理；
- TUR、GRE、BYZ 身份、日志、事件或地区建设；
- Auto-Apply PMs 的设置变量和日志。

不得调用 FFPA Firefall Flavor Pack 的 scripted effect、读取其临时变量或复制其定义。双方只分别向原版 on_action 数据库登记各自的模块包装入口。

## 5. 覆盖与存档接口

修改前必须检查：

| 对象 | 方式 | 必查上游 |
|---|---|---|
| `uw_infamy_cost` | `REPLACE:` | Firefall |
| `uw_estimated_union_war_infamy` | `REPLACE:` | Firefall |
| `uw_start_union_war` | `REPLACE:` | Firefall |
| `ai_strategy_default` | `INJECT:` | 原版、Tech & Res、Firefall |
| `ai_strategy_uw_reclaim_homelands` | `INJECT:` | Firefall |
| `NDiplomacy` | define 覆盖 | 原版及所有 define Mod |
| `institution_*` | 同名顶层定义 | 原版、Firefall |
| `pm_trade_center*` | `INJECT:` | 原版、Tech & Res、Firefall |

以下 ID 是稳定接口，不因文件移动、排序或重构而改名：

- `ffpa_innovation_cap_mirror_value`
- `ffpa_has_unowned_claimed_state`
- `ffpa_has_adjacent_unowned_claimed_state`
- `ai_strategy_uw_reclaim_homelands`
- 所有 `ffpa_*` modifier、effect、game rule、外交战和战争目标 ID
- 统一战争的 Firefall 上游 ID

## 6. 本地化与格式

- 玩家可见对象同步维护英文和简体中文，键集合必须一致。
- 本地化首行保持正确语言头和 UTF-8 BOM。
- 保留现有文件编码、换行、缩进和注释风格。
- 不在本地化或 README 中承诺脚本未实现的行为。

## 7. 最低验证

- `.metadata/metadata.json` 可解析。
- 修改脚本的括号、字符串、注释和顶层结构正常。
- 英文与简体中文键集合一致且无重复。
- 同一 Mod 内无意外重复自有顶层键。
- `git diff --check` 无新增空白错误。
- 统一战争复核 UI 顺序、AI 估值和四种开战分支。
- 殖民复核地区评分、内部省份形状以及玩家同受 define 影响。
- 新游戏、旧存档和月度刷新分别验证人口恢复与创新镜像。
- 贸易中心复核基础/External Trade II 容量以及五档船运投入。
- AI 宣称收复复核战略资格与权重、目标国家欲望、`return_state`/`conquer_state` 选择、分权国家排除以及超级大国切换。

运行时证据依次区分：文件加载、顶层解析、调度到达、trigger/effect 执行、最终状态未被后加载内容回写。

## 8. Git 与交付

- 开工和交付都运行 `git status --short --branch`。
- 未经明确要求，不执行 `git add`、`git commit`、`git reset`、`git checkout --`、`git clean`、rebase 或 force push。
- 不提交本机游戏路径、Workshop 路径、日志、存档、崩溃转储或发布压缩包。
- 交付说明修改文件、上游覆盖、存档接口、静态/运行时验证以及工作树状态。
