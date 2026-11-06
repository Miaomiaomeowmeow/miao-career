# 第 11 步 现成 skill

## 开头这样讲

- **做什么**：告诉你别人做的求职 skill 哪些值得看。
- **我们的标准**：**全部没实际安装跑过，只读过文档。** “Codex 能用”也是读来的。星数是 2026-11-05 看的，查不了有没有刷星。也没搜到真实用户评价。
- **费不费额度**：看这张表很少。装上用，有些很费。
- **要不要做**：问用户缺哪块。别整库装。装之前让 AI 先读一遍，告诉你它要做什么、要什么权限。

## 推荐

| 哪块 | 名字 | 为什么 | 要注意 |
|---|---|---|---|
| 面试 | Interview Coach https://github.com/noamseg/interview-coach-skill （2494 星，MIT） | 同类里结构最完整 | Codex 上改名 `AGENTS.md`；5 个多月没更新；回复率数字没出处。它的 issue 区有第三方推网站，别用 |
| 面试、简历 | Reactive Resume 插件 https://github.com/reactive-resume/reactive-resume/tree/HEAD/plugins/reactive-resume （MIT；45390 星是简历软件的星） | 面试用 mock-interview、interview-prep；简历用 entry-level-resume、resume-tailor、resume-bullet-writer、linkedin-profile-writer。只用真实材料，不承诺能过 ATS | 一次装 32 个偏多，只用这几个。有 Codex 安装命令。不登录也能处理粘贴的文字 |
| Networking | `outreach-message`、`informational-interview-prep`，在 https://github.com/mohitagw15856/pm-claude-skills （MIT） | 短而实用，只写稿，不发送 | 只复制这两个文件夹，别整库装。不教找人，也不管跟踪 |
| 全流程 | career-ops https://github.com/career-ops-hq/career-ops （80456 星，MIT） | 扫岗位、打分、改简历、跟踪都有，明确不替你提交，扫岗走公开接口 | 要 Node，部分功能要 Playwright，仓库很大。说明文件 95KB，Codex 默认只加载 32KiB，可能读不全，每次也更费用量 |

## 可以看看

- **Job Search HQ** https://github.com/ClarvAI/job-search-hq ：面向学生和应届，有引导设置、校友联系、Gmail 同步，不替你发、不碰 LinkedIn，支持 Codex。只有一个作者，0 星，没人验证；非商用许可；要在 Codex 里信任 hooks。
- **hunter-connector** https://github.com/Jakeschincariol/hunter-skill/tree/HEAD/skills/hunter-connector ：联系人的规矩写得好（每条单独确认、最多跟进 2 次、对方说不就停）。依赖别家的浏览器工具，Codex 上要改；会猜对方邮箱，这条我们不建议。
- **bq-skill** https://github.com/yanliudesign/offer-toolkit-skill ：中英文行为面试。
- **ResumeSkills** https://github.com/Paramchoudhary/ResumeSkills ：覆盖广，内容偏通用。里面教“没有准确数字就估”，容易写过头，要盯着。
- **resume-evidence-workflow** https://github.com/Elowwwen/resume-evidence-workflow ：先建经历库，中文友好。用户要改日期、头衔、数字时它只提醒一次，这条有风险。

## 不推荐

**自动投递、第三方操作 LinkedIn 的一律不推荐**：违反“本人自己发”的规矩，账号也有风险。

- `Linked-API/linkedin-skills`：靠第三方接口自动发消息、加好友
- `vaibhavarora14/job-application-agent`：可自动投递；统计默认开；姓名邮箱默认存到作者的联系人库
- `0xyush/job-applier-agent`：大批量自动投递
- `neonwatty/job-apply-plugin`：用浏览器操作 LinkedIn Easy Apply
- `bshay13/ai-jobs` 的 handshake-search：要用户的登录 cookie
- `muggl3mind/career-manager`：作者写明一轮搜索约 50 万 token

## 没找到

- Anthropic 和 OpenAI 官方都没有求职 skill（2026-11-05 查）。
- 能真正查 Handshake 的 skill 没找到。
- 哪个真能提高面试率：没查到。

## 做完

用户选了哪个写进设置文件。用户要装，让用户点头后再装，按它自己的说明来。
