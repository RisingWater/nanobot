"""WXAuto channel configuration management."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class ChatConfig:
    """Configuration for a specific chat."""
    
    chat_name: str
    process_text: bool = True
    process_voice: bool = False
    process_image: bool = False
    process_file: bool = False
    process_link: bool = False
    image_prompt: str = ""
    file_prompt: str = ""
    link_prompt: str = ""
    
    def should_process(self, message_type: str) -> bool:
        """Check if this message type should be processed for this chat."""
        type_map = {
            "text": self.process_text,
            "voice": self.process_voice,
            "image": self.process_image,
            "file": self.process_file,
            "link": self.process_link,
        }
        return type_map.get(message_type, False)
    
    def get_prompt(self, message_type: str) -> str:
        """Get the prompt for this message type."""
        prompt_map = {
            "image": self.image_prompt,
            "file": self.file_prompt,
            "link": self.link_prompt,
        }
        return prompt_map.get(message_type, "")


@dataclass
class WXAutoChannelConfig:
    """Main configuration for WXAuto channel."""
    
    chat_configs: List[ChatConfig] = field(default_factory=list)
    
    @classmethod
    def load(cls, config_path: Path) -> WXAutoChannelConfig:
        """Load configuration from file."""
        if not config_path.exists():
            logger.info(f"Config file not found at {config_path}, creating default")
            config = cls.create_default()
            config.save(config_path)
            return config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chat_configs = []
            for chat_data in data.get("chat_configs", []):
                chat_config = ChatConfig(
                    chat_name=chat_data.get("chat_name", ""),
                    process_text=chat_data.get("process_text", True),
                    process_voice=chat_data.get("process_voice", False),
                    process_image=chat_data.get("process_image", False),
                    process_file=chat_data.get("process_file", False),
                    process_link=chat_data.get("process_link", False),
                    image_prompt=chat_data.get("image_prompt", ""),
                    file_prompt=chat_data.get("file_prompt", ""),
                    link_prompt=chat_data.get("link_prompt", ""),
                )
                chat_configs.append(chat_config)
            
            return cls(chat_configs=chat_configs)
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            # Fall back to default config
            config = cls.create_default()
            config.save(config_path)
            return config
    
    def save(self, config_path: Path) -> bool:
        """Save configuration to file."""
        try:
            data = {
                "chat_configs": [
                    {
                        "chat_name": config.chat_name,
                        "process_text": config.process_text,
                        "process_voice": config.process_voice,
                        "process_image": config.process_image,
                        "process_file": config.process_file,
                        "process_link": config.process_link,
                        "image_prompt": config.image_prompt,
                        "file_prompt": config.file_prompt,
                        "link_prompt": config.link_prompt,
                    }
                    for config in self.chat_configs
                ]
            }
            
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Config saved to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            return False
    
    @classmethod
    def create_default(cls) -> WXAutoChannelConfig:
        """Create default configuration."""
        default_chats = [
            ChatConfig(
                chat_name="文件传输助手",
                process_text=True,
                process_voice=False,
                process_image=False,
                process_file=False,
                process_link=False,
                image_prompt="请分析这张图片的内容",
                file_prompt="请分析这个文件的内容",
                link_prompt="请分析这个链接的内容",
            )
        ]
        return cls(chat_configs=default_chats)
    
    def get_chat_config(self, chat_name: str) -> Optional[ChatConfig]:
        """Get configuration for a specific chat."""
        for config in self.chat_configs:
            if config.chat_name == chat_name:
                return config
        return None
    
    def add_or_update_chat_config(self, chat_config: ChatConfig) -> None:
        """Add or update a chat configuration."""
        for i, existing_config in enumerate(self.chat_configs):
            if existing_config.chat_name == chat_config.chat_name:
                self.chat_configs[i] = chat_config
                return
        
        # If not found, add new config
        self.chat_configs.append(chat_config)
    
    def remove_chat_config(self, chat_name: str) -> bool:
        """Remove configuration for a chat."""
        for i, config in enumerate(self.chat_configs):
            if config.chat_name == chat_name:
                self.chat_configs.pop(i)
                return True
        return False