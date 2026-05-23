=== Claude Code File Upload 插件 ===

将文件拖入桌面悬浮窗，Claude Code 自动识别并分析，无需手动输入路径。

--- 文件说明 ---

upload.pyw        桌面拖拽上传小窗（双击启动，无边框，可拖拽移动）
check_upload.py   Claude Code 自动检测脚本（放入 ~/.claude/hooks/）
README.txt        本说明文件

--- 安装步骤 ---

1. 将 upload.pyw 放在桌面（或其他方便的位置）

2. 将 check_upload.py 放入 ~/.claude/hooks/ 目录：
   - 创建目录：mkdir -p ~/.claude/hooks
   - 复制文件：cp check_upload.py ~/.claude/hooks/

3. 配置 Claude Code 的 settings.json：
   在 ~/.claude/settings.json 中添加以下内容：
   ┌────────────────────────────────────────────────────┐
   │ "hooks": {                                         │
   │   "UserPromptSubmit": [                            │
   │     {                                              │
   │       "matcher": "",                               │
   │       "hooks": [                                   │
   │         {                                          │
   │           "type": "command",                       │
   │           "command": "python ~/.claude/hooks/check_upload.py" │
   │         }                                          │
   │       ]                                            │
   │     }                                              │
   │   ]                                                │
   │ }                                                  │
   └────────────────────────────────────────────────────┘

   注意：如果 settings.json 中已有 "hooks" 项，请将
   "UserPromptSubmit" 合并进去，不要重复创建 "hooks" 键。

4. 重启 Claude Code 使配置生效

--- 使用方式 ---

1. 双击 upload.pyw 启动悬浮窗
2. 将任意文本文件拖入窗口（或点击窗口选择文件）
3. 预览文件内容，确认后点击 SEND 按钮
4. 切换到 Claude Code，输入任意内容（如"帮我看看"）
5. Claude Code 自动读取文件内容并分析

支持的文件类型：
  .py  .js  .ts  .go  .rs  .c  .cpp  .java  .json
  .md  .txt  .log  .html  .css  .xml  .yaml  .toml
  以及更多纯文本格式

二进制文件（图片、视频、压缩包、PDF 等）：
  - 无法预览文本内容，但会显示文件名、路径和大小
  - 如有需要，可在对话中请 Claude 用其他工具分析

--- 依赖环境 ---

- Python 3.x（需在 PATH 中可用）
- tkinter（Python 标准库自带）
- Claude Code（桌面终端版）

可选依赖（增强拖拽体验）：
  pip install windnd
  或
  pip install tkinterdnd2

如果没有安装以上可选依赖，仍然可以点击窗口手动选择文件。

--- 常见问题 ---

Q: 拖入文件没有反应？
A: 安装 windnd 或 tkinterdnd2 获得拖拽支持，或直接点击窗口选择文件。

Q: 点击 SEND 后 Claude Code 没有自动识别？
A: 确认 check_upload.py 路径正确，settings.json 配置无误，
   并重启 Claude Code。可查看 ~/upload_debug.log 排查问题。

Q: SEND 按钮是灰色的？
A: 需要先拖入或选择一个文件，按钮才会变为可用状态。

Q: 中文显示乱码？
A: 文件编码应为 UTF-8。其他编码会自动替换无法识别的字符。
