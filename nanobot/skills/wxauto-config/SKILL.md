# WXAuto Config Skill

管理 WXAuto 通道的聊天配置。

## 功能

通过聊天命令管理 `~/.nanobot/wxauto_config/chat_config.json` 配置文件：

1. **添加新的聊天配置**
2. **删除已有的聊天配置**
3. **更新聊天配置**
4. **查看所有配置**
5. **查看特定聊天配置**
6. **重置为默认配置**

## 使用方法

### 基本命令格式
```
/wxconfig <命令> [参数]
```

### 可用命令

#### 1. 查看所有配置
```
/wxconfig list
```
显示所有已配置的聊天对象及其基本设置。

#### 2. 查看特定聊天配置
```
/wxconfig show <聊天名>
```
显示指定聊天对象的详细配置。

#### 3. 添加新的聊天配置
```
/wxconfig add <聊天名>
```
为新的聊天对象创建默认配置。

#### 4. 删除聊天配置
```
/wxconfig remove <聊天名>
```
删除指定聊天对象的配置。

#### 5. 更新配置项
```
/wxconfig set <聊天名> <配置项> <值>
```
更新指定聊天对象的配置项。

#### 6. 重置为默认配置
```
/wxconfig reset
```
重置所有配置为默认值。

### 配置项说明

可配置的项包括：

| 配置项 | 说明 | 默认值 | 示例值 |
|--------|------|--------|--------|
| `process_text` | 是否处理文字消息 | `true` | `true` / `false` |
| `process_voice` | 是否处理语音消息 | `false` | `true` / `false` |
| `process_image` | 是否处理图片消息 | `false` | `true` / `false` |
| `process_file` | 是否处理文件消息 | `false` | `true` / `false` |
| `process_link` | 是否处理链接消息 | `false` | `true` / `false` |
| `image_prompt` | 图片消息提示词 | `""` | `"请分析这张图片的内容"` |
| `file_prompt` | 文件消息提示词 | `""` | `"请分析这个文件的内容"` |
| `link_prompt` | 链接消息提示词 | `""` | `"请分析这个链接的内容"` |

### 示例

#### 示例 1：添加新聊天配置
```
/wxconfig add 工作群
```
为"工作群"创建默认配置。

#### 示例 2：启用图片处理
```
/wxconfig set 工作群 process_image true
```
启用"工作群"的图片消息处理。

#### 示例 3：设置图片提示词
```
/wxconfig set 工作群 image_prompt "请分析这张图片中的内容"
```
为"工作群"设置图片处理提示词。

#### 示例 4：查看配置
```
/wxconfig show 工作群
```
查看"工作群"的详细配置。

#### 示例 5：删除配置
```
/wxconfig remove 测试群
```
删除"测试群"的配置。

## 配置文件位置

配置文件保存在：
```
~/.nanobot/wxauto_config/chat_config.json
```

## 配置文件格式

```json
{
  "chat_configs": [
    {
      "chat_name": "文件传输助手",
      "process_text": true,
      "process_voice": false,
      "process_image": false,
      "process_file": false,
      "process_link": false,
      "image_prompt": "请分析这张图片的内容",
      "file_prompt": "请分析这个文件的内容",
      "link_prompt": "请分析这个链接的内容"
    }
  ]
}
```

## 注意事项

1. **配置立即生效**：修改配置后，WXAuto 通道会立即使用新配置
2. **聊天名区分大小写**：配置中的聊天名需要与实际聊天名完全一致
3. **默认配置**：新添加的聊天对象会使用默认配置
4. **配置文件备份**：建议定期备份配置文件

## 错误处理

- 如果聊天名不存在，会显示错误信息
- 如果配置项名称错误，会显示可用配置项列表
- 如果值类型错误，会显示正确的值类型

## 相关文件

- `nanobot/channels/wxauto_config.py` - 配置管理模块
- `nanobot/channels/wxauto.py` - WXAuto 通道实现