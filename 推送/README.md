# 公考日报 · 每日推送

每天定时把「今日任务 + 知识点 + 每日一题 + 时政热点」推送到你的微信。

- **当日任务**：脚本按 [../计划/总体计划.md](../计划/总体计划.md) 的阶段 + 星期自动算出，零成本、与计划同步。
- **知识点 / 一题 / 时政**：调 LLM API 每日生成新内容。
- **推送渠道**：Server酱 或 PushPlus（推到微信）。
- **依赖**：仅 Python 3 标准库，**无需 pip 安装任何包**。

---

## 一、前置准备

服务器上确认有 Python 3：

```bash
python3 --version    # 需要 3.6+
```

确保服务器时区为北京时间（否则 `date.today()` 和推送日期会错位）：

```bash
sudo timedatectl set-timezone Asia/Shanghai
```

---

## 二、配置密钥

### 1. 推送渠道（二选一）

**Server酱**（推荐，推到个人微信）：
1. 浏览器打开 https://sct.ftqq.com ，微信扫码登录
2. 复制「SendKey」（形如 `SCT123456abcd...`）
3. 填入 config.json 的 `serverchan_key`，`push_channel` 设为 `"serverchan"`

**PushPlus**（备选，免费额度更大）：
1. 打开 https://www.pushplus.plus 登录
2. 复制首页的 `token`
3. 填入 `pushplus_token`，`push_channel` 设为 `"pushplus"`

### 2. LLM API（生成知识点/一题/时政）

**DeepSeek**（推荐，便宜好用，OpenAI 兼容）：
1. 打开 https://platform.deepseek.com 注册
2. 充值 ¥10（够用几个月，每日一次调用成本不到 1 分钱）
3. 「API Keys」创建 key（形如 `sk-...`）
4. config.json 保持默认：
   - `llm_base_url`: `https://api.deepseek.com`
   - `llm_model`: `deepseek-chat`
   - `llm_api_key`: 你的 key

**智谱 GLM**（备选，有免费额度）：
1. 打开 https://open.bigmodel.cn 注册
2. 「API Keys」创建 key
3. config.json 改为：
   - `llm_base_url`: `https://open.bigmodel.cn/api/paas/v4`
   - `llm_model`: `glm-4-flash`
   - `llm_api_key`: 你的 key

> 任何 OpenAI 兼容的接口都能用，改 `llm_base_url` / `llm_model` / `llm_api_key` 即可。

### 3. 生成 config.json

```bash
cd 推送目录
cp config.example.json config.json
# 用编辑器（vim/nano）填入上面的密钥
nano config.json
```

---

## 三、本地测试

先在屏幕上预览生成内容（不推送）：

```bash
python3 daily_push.py --dry-run
```

发一条测试消息到微信，验证推送配置：

```bash
python3 daily_push.py --test
```

微信收到测试消息即配置成功。正常推送一次看效果：

```bash
python3 daily_push.py
```

---

## 四、设置每天定时

### Linux（cron）

编辑 crontab：

```bash
crontab -e
```

加一行（每天早 7:30 推送，时间自定）：

```cron
30 7 * * * cd /服务器上的/推送目录 && /usr/bin/python3 daily_push.py >> push.log 2>&1
```

- `cd` 到脚本目录是为了让它找到同目录的 `config.json`
- `>> push.log 2>&1` 把运行日志存下来，排错用
- 路径用绝对路径，`python3` 路径可用 `which python3` 确认

保存退出后即可。用 `crontab -l` 查看是否生效。

### Windows（任务计划程序）

若服务器是 Windows：打开「任务计划程序」→ 创建基本任务 → 触发器「每天 7:30」→ 操作「启动程序」：
- 程序：`python.exe` 的完整路径
- 参数：`daily_push.py`
- 起始位置：脚本所在目录

---

## 五、排错

| 现象 | 排查 |
|---|---|
| 微信没收到 | 先跑 `--test`；看 `push.log` 里推送结果 `code` 是否成功 |
| 只有今日任务、没有知识点/一题/时政 | LLM 调用失败，检查 `llm_api_key`、余额、`llm_base_url` |
| 日期/星期不对 | 服务器时区不是北京时间，执行上方的 `timedatectl` 命令 |
| cron 不触发 | 确认 crond 服务运行（`systemctl status cron`）；路径用绝对路径 |

---

## 六、与计划同步

脚本的阶段时间硬编码在 `daily_push.py` 顶部的 `PHASES` 列表，与 [../计划/总体计划.md](../计划/总体计划.md) 一致。

**若你调整了计划阶段时间或国考/省考日期**，同步修改 `daily_push.py` 里的：
- `PHASES`（阶段起止）
- `GUOKAO_DATE` / `SHENGKAO_DATE`（倒计时用）

国考/省考实际日期以官方公告为准，临近时记得更新。
