"""WXAuto Config Skill - Manage WXAuto channel configurations."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from nanobot.agent.context import AgentContext
from nanobot.agent.tools.filesystem import read_file, write_file, edit_file


class WXAutoConfigSkill:
    """Skill for managing WXAuto channel configurations."""
    
    def __init__(self, context: AgentContext):
        self.context = context
        self.config_path = self._get_config_path()
        
    def _get_config_path(self) -> Path:
        """Get the WXAuto config file path."""
        from nanobot.config.paths import get_runtime_subdir
        
        config_dir = get_runtime_subdir("wxauto_config")
        return config_dir / "chat_config.json"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if not self.config_path.exists():
                return {"chat_configs": []}
            
            content = read_file(str(self.config_path))
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {"chat_configs": []}
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = json.dumps(config, ensure_ascii=False, indent=2)
            write_file(str(self.config_path), content)
            return True
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")
            return False
    
    def _find_chat_config(self, config: Dict[str, Any], chat_name: str) -> Optional[Dict[str, Any]]:
        """Find a chat configuration by name."""
        for chat_config in config.get("chat_configs", []):
            if chat_config.get("chat_name") == chat_name:
                return chat_config
        return None
    
    def _get_default_config(self, chat_name: str) -> Dict[str, Any]:
        """Get default configuration for a chat."""
        return {
            "chat_name": chat_name,
            "process_text": True,
            "process_voice": False,
            "process_image": False,
            "process_file": False,
            "process_link": False,
            "image_prompt": "",
            "file_prompt": "",
            "link_prompt": ""
        }
    
    def list_configs(self) -> str:
        """List all chat configurations."""
        config = self._load_config()
        
        if not config.get("chat_configs"):
            return "当前没有配置任何聊天对象。"
        
        result = ["已配置的聊天对象:", ""]
        for chat_config in config["chat_configs"]:
            chat_name = chat_config.get("chat_name", "未知")
            enabled_features = []
            
            if chat_config.get("process_text", True):
                enabled_features.append("文字")
            if chat_config.get("process_voice", False):
                enabled_features.append("语音")
            if chat_config.get("process_image", False):
                enabled_features.append("图片")
            if chat_config.get("process_file", False):
                enabled_features.append("文件")
            if chat_config.get("process_link", False):
                enabled_features.append("链接")
            
            features_str = "、".join(enabled_features) if enabled_features else "无"
            result.append(f"- {chat_name}: 启用 {features_str}")
        
        return "\n".join(result)
    
    def show_config(self, chat_name: str) -> str:
        """Show detailed configuration for a chat."""
        config = self._load_config()
        chat_config = self._find_chat_config(config, chat_name)
        
        if not chat_config:
            return f"未找到聊天对象 '{chat_name}' 的配置。"
        
        result = [f"聊天对象: {chat_name}", ""]
        
        # 消息处理设置
        result.append("消息处理设置:")
        result.append(f"  - 文字消息: {'是' if chat_config.get('process_text', True) else '否'}")
        result.append(f"  - 语音消息: {'是' if chat_config.get('process_voice', False) else '否'}")
        result.append(f"  - 图片消息: {'是' if chat_config.get('process_image', False) else '否'}")
        result.append(f"  - 文件消息: {'是' if chat_config.get('process_file', False) else '否'}")
        result.append(f"  - 链接消息: {'是' if chat_config.get('process_link', False) else '否'}")
        
        # 提示词设置
        result.append("")
        result.append("提示词设置:")
        
        image_prompt = chat_config.get("image_prompt", "")
        file_prompt = chat_config.get("file_prompt", "")
        link_prompt = chat_config.get("link_prompt", "")
        
        result.append(f"  - 图片提示词: {image_prompt if image_prompt else '(未设置)'}")
        result.append(f"  - 文件提示词: {file_prompt if file_prompt else '(未设置)'}")
        result.append(f"  - 链接提示词: {link_prompt if link_prompt else '(未设置)'}")
        
        return "\n".join(result)
    
    def add_config(self, chat_name: str) -> str:
        """Add a new chat configuration."""
        config = self._load_config()
        
        if self._find_chat_config(config, chat_name):
            return f"聊天对象 '{chat_name}' 的配置已存在。"
        
        new_config = self._get_default_config(chat_name)
        config.setdefault("chat_configs", []).append(new_config)
        
        if self._save_config(config):
            return f"已为聊天对象 '{chat_name}' 创建默认配置。"
        else:
            return f"创建聊天对象 '{chat_name}' 的配置失败。"
    
    def remove_config(self, chat_name: str) -> str:
        """Remove a chat configuration."""
        config = self._load_config()
        
        chat_configs = config.get("chat_configs", [])
        new_chat_configs = [
            cfg for cfg in chat_configs 
            if cfg.get("chat_name") != chat_name
        ]
        
        if len(new_chat_configs) == len(chat_configs):
            return f"未找到聊天对象 '{chat_name}' 的配置。"
        
        config["chat_configs"] = new_chat_configs
        
        if self._save_config(config):
            return f"已删除聊天对象 '{chat_name}' 的配置。"
        else:
            return f"删除聊天对象 '{chat_name}' 的配置失败。"
    
    def set_config(self, chat_name: str, key: str, value: str) -> str:
        """Set a configuration value for a chat."""
        config = self._load_config()
        chat_config = self._find_chat_config(config, chat_name)
        
        if not chat_config:
            return f"未找到聊天对象 '{chat_name}' 的配置。请先使用 '/wxconfig add {chat_name}' 添加配置。"
        
        # Parse value based on expected type
        if key in ["process_text", "process_voice", "process_image", "process_file", "process_link"]:
            # Boolean values
            if value.lower() in ["true", "是", "yes", "1", "启用", "开启"]:
                parsed_value = True
            elif value.lower() in ["false", "否", "no", "0", "禁用", "关闭"]:
                parsed_value = False
            else:
                return f"值 '{value}' 无效。请使用 'true'/'false' 或 '是'/'否'。"
        else:
            # String values
            parsed_value = value
        
        # Update the configuration
        chat_config[key] = parsed_value
        
        if self._save_config(config):
            return f"已更新聊天对象 '{chat_name}' 的配置: {key} = {parsed_value}"
        else:
            return f"更新聊天对象 '{chat_name}' 的配置失败。"
    
    def reset_config(self) -> str:
        """Reset configuration to default."""
        default_config = {
            "chat_configs": [
                {
                    "chat_name": "文件传输助手",
                    "process_text": True,
                    "process_voice": False,
                    "process_image": False,
                    "process_file": False,
                    "process_link": False,
                    "image_prompt": "请分析这张图片的内容",
                    "file_prompt": "请分析这个文件的内容",
                    "link_prompt": "请分析这个链接的内容"
                }
            ]
        }
        
        if self._save_config(default_config):
            return "已重置配置为默认值。"
        else:
            return "重置配置失败。"
    
    def get_help(self) -> str:
        """Get help message."""
        return """WXAuto 配置管理命令:

命令格式: /wxconfig <命令> [参数]

可用命令:
1. /wxconfig list                    - 列出所有聊天配置
2. /wxconfig show <聊天名>           - 查看指定聊天配置
3. /wxconfig add <聊天名>            - 添加新的聊天配置
4. /wxconfig remove <聊天名>         - 删除聊天配置
5. /wxconfig set <聊天名> <项> <值> - 设置配置项
6. /wxconfig reset                   - 重置为默认配置
7. /wxconfig help                    - 显示此帮助信息

配置项:
- process_text    - 是否处理文字消息 (true/false)
- process_voice   - 是否处理语音消息 (true/false)
- process_image   - 是否处理图片消息 (true/false)
- process_file    - 是否处理文件消息 (true/false)
- process_link    - 是否处理链接消息 (true/false)
- image_prompt    - 图片消息提示词 (字符串)
- file_prompt     - 文件消息提示词 (字符串)
- link_prompt     - 链接消息提示词 (字符串)

示例:
/wxconfig add 工作群
/wxconfig set 工作群 process_image true
/wxconfig set 工作群 image_prompt "请分析图片内容"
/wxconfig show 工作群
"""


def handle_wxconfig_command(context: AgentContext, command: str) -> str:
    """Handle wxconfig commands."""
    skill = WXAutoConfigSkill(context)
    
    # Parse command
    parts = command.strip().split()
    if not parts:
        return skill.get_help()
    
    cmd = parts[0].lower()
    
    try:
        if cmd == "list":
            return skill.list_configs()
        
        elif cmd == "show":
            if len(parts) < 2:
                return "请指定聊天名。格式: /wxconfig show <聊天名>"
            return skill.show_config(parts[1])
        
        elif cmd == "add":
            if len(parts) < 2:
                return "请指定聊天名。格式: /wxconfig add <聊天名>"
            return skill.add_config(parts[1])
        
        elif cmd == "remove":
            if len(parts) < 2:
                return "请指定聊天名。格式: /wxconfig remove <聊天名>"
            return skill.remove_config(parts[1])
        
        elif cmd == "set":
            if len(parts) < 4:
                return "参数不足。格式: /wxconfig set <聊天名> <配置项> <值>"
            return skill.set_config(parts[1], parts[2], " ".join(parts[3:]))
        
        elif cmd == "reset":
            return skill.reset_config()
        
        elif cmd in ["help", "?"]:
            return skill.get_help()
        
        else:
            return f"未知命令: {cmd}\n\n{skill.get_help()}"
    
    except Exception as e:
        logger.error(f"Error handling wxconfig command: {e}")
        return f"处理命令时出错: {str(e)}"


# Register the skill
def register(context: AgentContext):
    """Register the skill with the agent."""
    # This skill is triggered by /wxconfig commands
    # The actual command handling is done in the agent's command processor
    pass