A step-by-step job search skill for students, new grads and early-career people in the US, for Codex and Claude Code.

# Miao Career

一个带你一步步找工作的 skill。你打开 AI，说一句 `$miao-career`，它一题一题问你，从盘点自己问到投递跟踪。

适合：在美国找工作的人，方向不限，不需要懂技术。开场会问你是新人还是有几年经验，找岗位和查资料都按这个来。有些部分主要按新人写的，会告诉你。

## 它带你做什么

一共 11 步，哪步都能跳过，也可以从中间开始：

1. 盘点自己
2. 选方向（打分标准全部公开给你看，都能改）
3. 看大环境
4. 找岗位（有脚本批量抓公开招聘接口）
5. 简历
6. 平台资料（定位句、LinkedIn、Handshake）
7. Networking（查你学校的渠道、列名单、AI 写话术、你自己发）
8. 投递节奏和跟踪表
9. 面试（这块还不完善，会指给你现成的 skill）
10. 签证身份（你需要才讲）
11. 现成 skill 推荐

你答过的都记在你电脑上的 `我的求职设置.md`，下次打开接着做。

## 开始之前先选

1. **用哪个 AI**：Codex 优先，Claude Code 也能用。
2. **用桌面版还是命令行**：要 AI 帮你在网页上改 LinkedIn、Handshake，要桌面版 Codex 加浏览器扩展；定时提醒也要桌面版。命令行版其他都能用。
3. **模型和查多少**：开场时会给你一张用量表。不想花额度，就选“不查”（不上网搜索）。批量抓岗位的脚本几乎不费额度，会单独问你。

## 怎么装

**Codex**

在 Codex 里说：

```
$skill-installer 安装 https://github.com/Miaomiaomeowmeow/miao-career/tree/main/skills/miao-career
```

或者手动：把 `skills/miao-career` 这个文件夹放到 `$HOME/.agents/skills/miao-career/`。

没出现的话，重启 Codex。

**Claude Code**

把 `skills/miao-career` 这个文件夹放到 `~/.claude/skills/miao-career/`。

找岗位的脚本要 Python 3，不用装别的。没有 Python 也能用其他步骤。

## 怎么开始

1. 建一个文件夹，比如 `miao-career`，在 AI 里打开它。求职的东西都存这里。
2. 说 `$miao-career`（Claude Code 说 `/miao-career`）。
3. 回答问题。觉得麻烦就说“跳过”。

做完开场，你的文件夹里会有 `我的求职设置.md`。下次还从这个文件夹打开。

## 费用提醒

这个 skill 不收钱，但查资料会用你的 AI 额度，**一次搜索可能用掉很多**，别等搜完才看用量。

Codex 的大致比例（占 Plus 一周额度，2026-11 用一个账号估算，没在 Plus 上实测，不是保证）：


| 查多少 | Luna | Terra | Sol |
|---|---:|---:|---:|
| 不查（实测一次：走 6 步、脚本抓 3 家） | 约 0.2% | 约 1% | 约 2% |
| 部分（默认） | 约 0.5～1% | 约 2～5% | 约 5～10% |
| 全面 | 约 2～20% | 约 11%～1 周多 | 约 23%～2 周多 |

Astra 不要用来搜索。Pro $100 约 5 倍、$200 约 20 倍额度。详情在开场时给你看。

## 有什么做不到

- **不替你投递、发消息、加好友。** 话术它写，你自己发。
- **不输密码。** 要登录的你自己登。
- **不给法律意见。** 签证的事问学校国际生办公室或律师。
- **不抓取 LinkedIn。** LinkedIn 协议禁止脚本和插件自动访问，账号有风险。默认用官方插件查人、好友列表你自己翻。你明确选了 AI 代翻，它会先讲风险。
- **翻不了所有人的好友列表。** 一度好友对方能关，二度默认看不了。
- **保证不了结果。** 数字是某一天的样本，只看量级。
- **面试这块还不完善。**
- **按美国写的。** 其他国家的渠道和规矩没查过。

里面的现成数据是 2026-10 按另一个人的方向抓的，只统计了新人岗，多半不对你的情况。你要就用，不要就重查。

你的设置文件、简历、联系人名单都有个人信息，别放进公开仓库。

## 作者

Miaomiao Yang。GitHub：[Miaomiaomeowmeow](https://github.com/Miaomiaomeowmeow)

仓库：github.com/Miaomiaomeowmeow/miao-career

MIT 许可，见 [LICENSE](LICENSE)。
