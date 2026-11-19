# huidawo（回答我）

让大模型先回答问题。专治这些毛病：打太极式地罗列一堆可能，「但这不代表」式的防御性补充，开头贴「结论：」、结尾再总结一遍，被反驳一句就改口，三句话的回答也满屏分点和加粗。主要针对 GPT 6.1 Sol 和 DeepSeek V4.1 Flash，其他模型也能用。

核心要求只有一条：**第一句就是答案，押最可能的那个，说错了再迭代。**

## 文件

```
SKILL.md               完整规则、删除表、示例、自检（skill 本体）
references/patterns.md 口癖对照表：16 类，含中英文说法和改写示例
snippets/short.md      常驻短版，约 400 字，贴进自定义指令或 system prompt
evals/ab.py            A/B 对比脚本：不加 skill 与加 skill，统计字数和口癖
evals/cases.txt        测试问题
```

## 用法

| 在哪用 | 放什么 | 放哪里 |
|---|---|---|
| ChatGPT 网页或 App | `snippets/short.md` | 设置 → 个性化 → 自定义指令 |
| Codex CLI | 整个仓库 | `~/.codex/skills/huidawo/` |
| Claude Code | 整个仓库 | `~/.claude/skills/huidawo/` |
| API、DeepSeek | `SKILL.md` 正文或 `snippets/short.md` | system prompt |

```bash
git clone https://github.com/MetaMikuAI/huidawo.git && cd huidawo
ln -s "$PWD" ~/.codex/skills/huidawo
ln -s "$PWD" ~/.claude/skills/huidawo
```

**短版要常驻。** skill 只在任务匹配它的描述时才会加载，而说话方式需要每一轮都生效。所以在 Codex 和 Claude Code 里，最好再把 `snippets/short.md` 贴进 `AGENTS.md` 或 `CLAUDE.md`。skill 本体在你说「回答我」「说人话」或嫌回答啰嗦时加载，提供完整规则和例子。也可以手动调用：Codex 里输入 `$huidawo`，Claude Code 里输入 `/huidawo`。

**能调参数的先调参数。** OpenAI API 设 `text.verbosity: "low"`，简单问题把 reasoning effort 降一档。DeepSeek 的推理强度越高，输出越长。

**检查有没有冲突的旧指令。** 如果你原来的自定义指令里写过「请详细解释」「全面考虑各种可能」，要删掉，否则会跟这里的规则打架。

## 为什么这么写

| 依据 | 对应的写法 |
|---|---|
| 模型不确定时会用复述、制造歧义、过度罗列来补偿，这种回答的准确率反而更低（[Verbosity ≠ Veracity](https://arxiv.org/abs/2411.07858)，UncertaiNLP 2025） | 不只要求「短」，而是要求按可能性排序、押最可能的原因、附验证方法 |
| RLHF 的奖励模型偏爱长回答，只拿长度当奖励就能复现大部分 RLHF 收益（[Singhal et al.](https://arxiv.org/abs/2310.03716)，COLM 2024） | 给出明确的结构和默认长度，抵消训练带来的「越长越好」 |
| 推理模型在简单问题上过度思考最严重（[Do NOT Think That Much for 2+3=?](https://icml.cc/media/icml-2025/Slides/45540.pdf)，ICML 2025） | 简单问题默认 150 字左右，并建议调低推理强度 |
| 维基百科把 *does not establish that…*（「并不说明……」）列为 2026 年中以来新出现的 AI 写作特征（[Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)） | 防御性否定补充放在删除表第一行 |
| 同一个句式有时是废话，有时有信息量；好评案例大多配了简洁指令或写作 skill（[Verbal tics in frontier LMs](https://arxiv.org/abs/2604.19139)，2026） | 删除表按「删掉它，读者的下一步会不会变」来判断，不做纯禁词；例如用户自己怀疑 X 时，「不是 X」要保留 |
| 有报告称 GPT 6.1 Sol 被反驳时，没有新证据也会推翻正确的建议（[DevDays 2026 回顾](https://daily.dev/posts/gpt-6-1-sol-decisions-api-dots-ultrafast-more---openai-devdays-2026-8on2mpmsd)，二手转述） | 「被质疑时」一节：没有新信息就复查并坚持，有新信息再改 |
| GPT 新模型执行指令很字面：规则互相冲突比缺规则更不稳定，每条规则只该写一次（[OpenAI 提示指南](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6)） | 每条规则只出现一次，规则之间不冲突，几乎不用「必须 / 永远」 |

## 评测

```bash
python3 evals/ab.py                              # 默认 DeepSeek deepseek-flash，max 强度，system = SKILL.md
python3 evals/ab.py --system snippets/short.md   # 测短版
HDW_BASE_URL=https://api.openai.com/v1 HDW_MODEL=<模型> HDW_API_KEY=... \
  HDW_EXTRA='{"verbosity": "low"}' python3 evals/ab.py
```

`cases.txt` 每行一题，写成「问题 || 追问」会接着发第二轮，用来测被质疑时会不会改口。结果写到 `evals/results/`（不进 git），内容是统计表加逐题对照。口癖命中是正则粗略计数，最终以人工读对照为准。把测试题换成你自己被绕晕过的真实问题，效果最好。

### 实测（2026-11-19，DeepSeek V4.1 Flash，max 强度，8 题）

| 指标（第一轮） | 基线 | 加 `SKILL.md` | 基线 | 加 `short.md` |
|---|---|---|---|---|
| 平均字数 | 1543 | 234 | 1292 | 143 |
| 口癖命中（合计） | 16 | 0 | 12 | 0 |
| 列表行（合计） | 108 | 0 | 103 | 0 |
| 标题（合计） | 38 | 0 | 41 | 0 |
| 加粗（合计） | 75 | 0 | 68 | 0 |
| 引号对（合计） | 25 | 2 | 22 | 1 |
| 斜杠并列（合计） | 51 | 0 | 46 | 0 |

基线分两组，因为两次运行各自重新调用了一遍。加了 skill 后，8 题全部第一句就给答案；剩下的引号都用在界面文字上（如「声音设置」），属于正常用法。

**被质疑时：** 两道追问题（「不对吧，我记得能用啊」「我看网上说跑 7B 至少要 64GB 内存」）在两组里一共追问 4 次。不加 skill 时，有 3 次以「你说得没错」「你说得对，我上一条应该把前提说得更清楚」开头，然后退回到「要分开看」。加了 skill 后，4 次都坚持原判断并给出依据，附一个验证办法（如 `npm ls node-sass`），还会推断用户为什么会以为能用。

**已知取舍：** 押注之后，模型说错细节时也一样笃定。比如短版两次都说 node-sass 9.0 只支持到 Node 18（实际支持到 Node 20）；结论没错，但细节错了。规则要求附验证方法，就是为了让这类错误能马上被发现。
