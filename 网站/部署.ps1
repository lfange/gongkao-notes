# 网站/部署.ps1 —— 一键把笔记网站部署到服务器
#
# 用法：
#   1. 把下方 $Server / $RemotePath 改成你的服务器信息
#   2. 在仓库根目录执行：  powershell -ExecutionPolicy Bypass -File 网站\部署.ps1
#
# 工作方式：
#   - 先把白名单内容（网站文件 + 全部笔记）复制到临时目录
#     → 天然排除 推送/、.git/、.claude/ 等不该上网的东西
#   - 打成 tar.gz 上传（中文文件名只存在于压缩包内部，避免编码乱码）
#   - 在服务器上解压到网站目录
#
# 首次部署前，请先读 同目录下的 部署指南.md 在服务器上装好 Web 服务。

# ===================== 需要修改的两项 =====================
$Server     = "user@your-server"       # 例："root@192.168.1.100"（需已配好 ssh 免密或会提示输密码）
$RemotePath = "/var/www/gongkao"       # 服务器上的网站根目录
# ==========================================================

$ErrorActionPreference = "Stop"

if ($Server -eq "user@your-server") {
    Write-Host "请先编辑 网站\部署.ps1，填入 `$Server 和 `$RemotePath" -ForegroundColor Yellow
    exit 1
}

# ---- 0. 检查依赖 ----
foreach ($cmd in @("ssh", "scp", "tar")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "缺少命令：$cmd （ssh/scp 需要 Win10 1809+ 自带的 OpenSSH 客户端；tar 系统自带）" -ForegroundColor Red
        exit 1
    }
}

# ---- 1. 白名单内容复制到临时目录 ----
# 白名单 = 网站必需文件 + 所有笔记目录。新增顶层目录/文件时要记得加进来。
$items = @(
    "index.html", "_sidebar.md", ".nojekyll",
    "README.md", "错题本.md", "资源推荐.md",
    "网站\assets",
    "计划", "xingce", "shenlun", "笔记", "真题"
)

$stage = Join-Path $env:TEMP "gongkao-site"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory $stage | Out-Null

foreach ($item in $items) {
    if (Test-Path $item) {
        Copy-Item $item -Destination $stage -Recurse
        Write-Host "已加入：$item"
    } else {
        Write-Host "跳过（本地不存在）：$item" -ForegroundColor DarkGray
    }
}

# ---- 2. 安全自检：临时目录里绝不允许出现密钥类文件 ----
$danger = Get-ChildItem $stage -Recurse -File | Where-Object {
    $_.Name -match '^config\.json$' -or $_.Name -match '\.(log|key|pem)$' -or $_.FullName -match '\\.git(\\|$)'
}
if ($danger) {
    Write-Host "发现不该上传的文件，已中止（检查白名单是否漏排）：" -ForegroundColor Red
    $danger | ForEach-Object { Write-Host "  $($_.FullName)" }
    Remove-Item $stage -Recurse -Force
    exit 1
}

# ---- 3. 打包上传并解压 ----
$archive = Join-Path $env:TEMP "gongkao-site.tar.gz"
if (Test-Path $archive) { Remove-Item $archive -Force }
tar -czf $archive -C $stage .
Write-Host "打包完成：$([math]::Round((Get-Item $archive).Length / 1KB)) KB，上传到 ${Server}:${RemotePath} ..."

scp -q $archive "${Server}:/tmp/gongkao-site.tar.gz"
ssh $Server "mkdir -p $RemotePath && tar -xzf /tmp/gongkao-site.tar.gz -C $RemotePath && rm -f /tmp/gongkao-site.tar.gz"

# ---- 4. 清理 ----
Remove-Item $stage -Recurse -Force
Remove-Item $archive -Force
Write-Host ""
Write-Host "部署完成！浏览器打开 http://服务器IP/ 即可看笔记。" -ForegroundColor Green
Write-Host "以后改完笔记，重新运行本脚本即可同步（服务器上的旧文件会被同名覆盖，但删除的笔记不会自动清理）。"

# ---- 附：Linux/macOS 上等价的部署命令（rsync，效果相同）----
# rsync -avz --delete --exclude '推送' --exclude '.git' --exclude '.claude' \
#   --exclude '网站' --include '网站/assets/***' \
#   ./ user@server:/var/www/gongkao/
