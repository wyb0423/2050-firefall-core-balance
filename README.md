# 2050 Firefall — Core Balance Adapter

面向 `2050: The Fire Falls` 与 `[1.13] Tech & Res` 的个人核心平衡适配。该 Mod 从 `2050 Firefall — Personal Preferences Adapter` 中独立拆出，只拥有统一战争、殖民塑形和通用平衡三组功能。

## 依赖与加载顺序

必需依赖：

- `2050: The Fire Falls`
- `[1.13] Tech & Res`

推荐完整加载顺序：

1. `[1.13] Tech & Res`
2. `Auto-Apply PMs`
3. `Auto-Apply Automation PMs`
4. `2050: The Fire Falls`
5. `2050 Firefall — Core Balance Adapter`
6. `2050 Firefall — Personal Preferences Adapter`

本 Mod 本身不依赖两个 Auto-Apply Mod 或 Personal Preferences Adapter。将本 Mod 放在 Firefall 与 Tech & Res 之后，是为了让覆盖和注入针对完整上游数据库生效。

## 统一战争 10% 恶名

- 为 Firefall 的 `uw_infamy_cost` 增加 10% 规则选项。
- 新增 `dp_union_war_tenth` 与 `ffpa_union_war_annex_country_tenth`。
- 把 10% 分支接入 Firefall 的 AI 恶名估值和四种统一战争开战流程。
- 不修改 Firefall 原有的 0%、25%、50% 与 100% 分支。

## 殖民塑形

- AI 优先首都区域、正在发展的殖民地和已有本国或附属国存在的区域。
- 相邻区域不获得额外倍率，但不会受到无落脚点远洋区域的 3% 惩罚。
- 殖民地内部扩张强烈偏好相邻省份，并降低非相邻扩张与随机选点。
- 殖民事务制度每级殖民增长从原版 0.1 调整为 0.2。

殖民 define 同时影响 AI 和玩家。本 Mod 不改变同时发展的殖民地数量上限。

## 通用平衡

- 所有国家在新游戏开始时获得持续 50 年、逐渐衰减的战后人口恢复。
- 动态镜像完整的未修正创新力上限，使最终创新力上限保持为两倍。
- 永久提高 100% 科技扩散速度。
- 贸易中心每个充分就业等级提供 100 贸易容量。
- 各档贸易数量生产方式的商船投入为上游基础值的五倍，并覆盖 Tech & Res 的 Ultra 档。
- 保留项目原有的七个制度顶层定义，其中殖民事务具有上述实际数值调整。

## 存档兼容

拆分没有改变任何游戏规则、事件、modifier、scripted effect 或持久变量 ID。旧存档若要维持拆分前的完整功能，需要同时启用本 Mod 与拆分后的 Personal Preferences Adapter。

`ffpa_innovation_cap_mirror_value` 是持久存档接口。创新上限刷新会读取旧镜像值、移除旧 modifier、计算新镜像并重新添加动态 modifier；不得改成无状态的简单 remove/add。

## 覆盖风险

以下对象针对最终加载数据库工作，更新原版或上游 Mod 后需要重新比较：

- `REPLACE:uw_infamy_cost`
- `REPLACE:uw_estimated_union_war_infamy`
- `REPLACE:uw_start_union_war`
- `INJECT:ai_strategy_default`
- `NDiplomacy`
- 七个 `institution_*` 顶层定义
- 七个贸易中心 PM 注入

文件名前缀只提供加载顺序，不代表冲突已经解决。
# 2050-firefall-core-balance
