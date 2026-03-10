# WXAuto Channel for nanobot

## 概述

WXAuto channel 是一个 nanobot 的聊天通道，用于通过 WXAuto 的 Web API 与微信进行通信。它允许 nanobot 接收和发送微信消息，包括文字、图片和文件。

## 功能特性

- ✅ 接收微信消息（文字、图片、文件、链接）
- ✅ 发送微信消息（文字、图片、文件）
- ✅ 支持个人聊天和群聊
- ✅ 可配置的允许列表（allow_from）
- ✅ 群聊策略控制（open/mention）
- ✅ 轮询方式获取新消息
- ✅ 文件下载和上传支持

## 配置

### 配置文件示例

在 `~/.nanobot/config.json` 中添加以下配置：

```json
{
  "channels": {
    "wxauto": {
      "enabled": true,
      "apiUrl": "http://localhost:8080",
      "apiKey": "your_wxauto_api_key",
      "wxname": "",  // 可选：微信账号名称
      "pollInterval": 3,  // 轮询间隔（秒）
      "allowFrom": ["*"],  // 允许的聊天列表，["*"] 表示允许所有
      "groupPolicy": "open"  // 群聊策略：open（所有消息）或 mention（仅@消息）
    }
  }
}
```

### 环境变量

也可以通过环境变量配置：

```bash
export NANOBOT_CHANNELS__WXAUTO__ENABLED=true
export NANOBOT_CHANNELS__WXAUTO__APIURL="http://localhost:8080"
export NANOBOT_CHANNELS__WXAUTO__APIKEY="your_wxauto_api_key"
export NANOBOT_CHANNELS__WXAUTO__ALLOWFROM='["文件传输助手", "王旭"]'
```

## 使用方法

### 1. 启动 WXAuto 服务器

确保 WXAuto 服务器正在运行。WXAuto 是一个微信自动化工具，提供 Web API 接口。

### 2. 启动 nanobot gateway

使用配置文件启动 nanobot：

```bash
nanobot gateway -c ~/.nanobot/config.json
```

或者使用测试配置文件：

```bash
nanobot gateway -c test_wxauto_config.json
```

### 3. 发送消息

通过微信向配置中允许的联系人发送消息，nanobot 会自动回复。

### 4. 测试

运行测试脚本验证配置：

```bash
python test_wxauto.py
```

## API 接口说明

WXAuto channel 使用以下 WXAuto API 接口：

### 发送消息
- `POST /v1/wechat/send` - 发送文字消息
- `POST /v1/wechat/sendfile` - 发送文件消息

### 接收消息
- `POST /v1/wechat/getnextnewmessage` - 获取下一条新消息

### 文件管理
- `POST /api/v1/files/upload` - 上传文件
- `GET /api/v1/files/{file_id}/download` - 下载文件
- `DELETE /api/v1/files/{file_id}` - 删除文件

### 状态检查
- `POST /v1/wechat/isonline` - 检查微信是否在线

## 消息格式

### 接收的消息格式

WXAuto channel 接收的消息包含以下信息：

```python
{
    "chat_name": "联系人名称",  # 如："文件传输助手"
    "chat_type": "personal",   # 或 "group"
    "messages": [
        {
            "type": "text",    # text, image, file, link
            "content": "消息内容",
            "file_id": "文件ID（如果是文件或图片）",
            "file_name": "文件名（如果是文件）"
        }
    ]
}
```

### 发送的消息格式

nanobot 通过 WXAuto channel 发送的消息会转换为微信消息：

- 文字消息：直接发送
- 图片/文件：先上传到 WXAuto 服务器，然后发送文件ID

## 安全注意事项

1. **API 密钥保护**：确保 API 密钥安全，不要泄露
2. **允许列表配置**：建议配置具体的 `allowFrom` 列表，而不是使用 `["*"]`
3. **网络隔离**：WXAuto 服务器应在受信任的网络环境中运行
4. **权限控制**：WXAuto 服务器应有适当的访问控制

## 故障排除

### 常见问题

1. **连接失败**：检查 WXAuto 服务器是否运行，API URL 是否正确
2. **认证失败**：检查 API 密钥是否正确
3. **消息不接收**：检查 `allowFrom` 配置，确保联系人名称正确
4. **文件发送失败**：检查文件路径和权限

### 日志查看

启用详细日志查看问题：

```bash
nanobot gateway -c config.json --verbose
```

## 开发说明

### 代码结构

- `nanobot/channels/wxauto.py` - 主 channel 实现
- `nanobot/config/schema.py` - 配置结构定义
- `nanobot/channels/manager.py` - channel 管理器

### 扩展功能

如需扩展功能，可以修改以下部分：

1. **消息类型支持**：在 `_handle_incoming_message` 方法中添加新的消息类型处理
2. **API 接口**：在 `WXAutoAPI` 类中添加新的 API 方法
3. **配置选项**：在 `WXAutoConfig` 类中添加新的配置字段

## 相关项目

- [nanobot](https://github.com/HKUDS/nanobot) - 个人 AI 助手
- [WXAuto](https://github.com/yourusername/wxauto) - 微信自动化工具（需要自行部署）

## 许可证

MIT