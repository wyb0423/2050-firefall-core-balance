# 地区战争目标恶名减免实施计划

日期：2026-09-03

设计依据：`docs/superpowers/specs/2026-09-03-state-wargoal-infamy-reduction-design.md`

1. 新建一个 `common/war_goal_types` 文件，以原版 1.13.11 为基线注入 `conquer_state.infamy` 与 `return_state.infamy`，只在原版最低值钳制前分别加入 `0.85` 与 `0.70` 倍率。
2. 在英文和简体中文本地化中加入相同的两个倍率说明键，保留 BOM 和现有格式。
3. 对比上游公式、检查脚本结构、本地化键、JSON、重复顶层键、空白错误与工作树状态；运行时测试留给游戏内验证。

不修改版本号、README、AI 战略、统一战争、全局恶名或存档接口，不执行 Git 暂存或提交。
