"""WXAuto channel implementation for WeChat automation."""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.paths import get_media_dir
from nanobot.config.schema import WXAutoConfig
from nanobot.utils.helpers import split_message

from .wxauto_config import WXAutoChannelConfig, ChatConfig


class WXAutoAPI:
    """WXAuto API client for WeChat automation."""

    def __init__(self, api_url: str, api_key: str, wxname: str = ""):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.wxname = wxname
        self.headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def send_text_message(self, who: str, msg: str, exact: bool = False) -> Dict[str, Any]:
        """
        Send text message via WXAuto API.
        
        Args:
            who: Recipient name (e.g., "文件传输助手")
            msg: Message content to send
            exact: Whether to match recipient exactly
            
        Returns:
            dict: API response
        """
        try:
            url = f"{self.api_url}/v1/wechat/send"
            
            payload = {
                "wxname": self.wxname,
                "who": who,
                "exact": exact,
                "msg": msg,
                "clear": True,
                "at": ""
            }
            
            logger.info(f"Sending message to '{who}': {msg[:50]}...")
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Message sent successfully to '{who}'")
                return {"success": True, "data": result}
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "status_code": response.status_code}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def get_next_new_message(self, filter_mute: bool = False, timeout: int = 30) -> Dict[str, Any]:
        """
        Get next new message via WXAuto API.
        
        Args:
            filter_mute: Whether to filter muted chats
            
        Returns:
            dict: API response with message data
        """
        try:
            url = f"{self.api_url}/v1/wechat/getnextnewmessage"
            
            payload = {
                "wxname": self.wxname,
                "filter_mute": filter_mute
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    message_data = result.get("data", {})
                    messages = message_data.get("msg", [])
                    
                    if messages:
                        logger.info(f"Received new message from '{message_data.get('chat_name', 'Unknown')}'")
                        return {
                            "success": True,
                            "has_message": True,
                            "chat_name": message_data.get("chat_name"),
                            "chat_type": message_data.get("chat_type"),
                            "messages": messages,
                            "raw_data": result
                        }
                    else:
                        return {
                            "success": True,
                            "has_message": False,
                            "raw_data": result
                        }
                else:
                    error_msg = result.get("message", "Unknown error")
                    logger.error(f"API returned error: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "raw_data": result
                    }
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "status_code": response.status_code}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def upload_file(self, file_path: str, description: str = "", uploader: str = "") -> Dict[str, Any]:
        """
        Upload file via WXAuto API.
        
        Args:
            file_path: Path to the file to upload
            description: File description (optional)
            uploader: Uploader name (optional)
            
        Returns:
            dict: API response with file_id
        """
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        try:
            url = f"{self.api_url}/api/v1/files/upload"
            
            headers = {
                'accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
            }
            
            files = {
                'file': (os.path.basename(file_path), open(file_path, 'rb')),
            }
            
            data = {}
            if description:
                data['description'] = description
            if uploader:
                data['uploader'] = uploader
            
            logger.info(f"Uploading file: {file_path}")
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"File uploaded successfully: {result.get('filename')}, file_id: {result.get('file_id')}")
                return {"success": True, "data": result}
            else:
                error_msg = f"File upload failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "status_code": response.status_code}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during file upload: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during file upload: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        finally:
            # Ensure file is closed
            if 'files' in locals():
                files['file'][1].close()

    def send_file_message(self, who: str, file_path: str, exact: bool = False) -> Dict[str, Any]:
        """
        Send file message via WXAuto API.
        
        Args:
            who: Recipient name (e.g., "文件传输助手")
            file_path: Path to the file to send
            exact: Whether to match recipient exactly
            
        Returns:
            dict: API response
        """
        # Step 1: Upload file
        upload_result = self.upload_file(file_path)
        if not upload_result.get("success"):
            return upload_result
        
        file_id = upload_result["data"].get("file_id")
        if not file_id:
            error_msg = "No file_id returned from upload"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Step 2: Send file using file_id
        try:
            url = f"{self.api_url}/v1/wechat/sendfile"
            
            payload = {
                "wxname": self.wxname,
                "who": who,
                "exact": exact,
                "file_id": file_id
            }
            
            logger.info(f"Sending file to '{who}': {os.path.basename(file_path)}")
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"File sent successfully to '{who}': {os.path.basename(file_path)}")
                    self.delete_file(file_id)
                    return {"success": True, "data": result, "file_info": upload_result["data"]}
                else:
                    error_msg = result.get("message", "Unknown error in send file")
                    logger.error(f"Send file failed: {error_msg}")
                    self.delete_file(file_id)
                    return {"success": False, "error": error_msg, "raw_data": result}
            else:
                error_msg = f"Send file API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                self.delete_file(file_id)
                return {"success": False, "error": error_msg, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during file send: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during file send: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """
        Delete uploaded file.
        
        Args:
            file_id: File ID to delete
            
        Returns:
            dict: Delete operation result
        """
        try:
            url = f"{self.api_url}/api/v1/files/{file_id}"
            
            headers = {
                'accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            response = requests.delete(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("message") == "文件删除成功":
                    logger.info(f"File deleted successfully: {file_id}")
                    return {"success": True}
                else:
                    error_msg = result.get("message", "Unknown deletion error")
                    logger.error(f"File deletion failed: {error_msg}")
                    return {"success": False, "error": error_msg}
            else:
                error_msg = f"Delete file API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during file deletion: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during file deletion: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def download_file(self, file_id: str, file_path: str) -> Dict[str, Any]:
        """
        Download file by file_id and delete it from server after successful download.
        
        Args:
            file_id: File ID to download
            file_path: Local path to save the downloaded file
            
        Returns:
            dict: Download operation result
        """
        try:
            url = f"{self.api_url}/api/v1/files/{file_id}/download"
            
            headers = {
                'accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            
            if response.status_code == 200:
                # 确保目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # 流式下载文件
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # 验证文件是否下载成功
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    logger.info(f"File downloaded successfully: {file_id} -> {file_path}")
                    
                    # 下载成功后删除服务器上的临时文件
                    delete_result = self.delete_file(file_id)
                    if delete_result.get("success"):
                        logger.info(f"Server file deleted successfully: {file_id}")
                    else:
                        logger.warning(f"Failed to delete server file {file_id}: {delete_result.get('error', 'Unknown error')}")
                    
                    return {
                        "success": True, 
                        "file_path": file_path,
                        "file_size": os.path.getsize(file_path),
                        "server_file_deleted": delete_result.get("success", False)
                    }
                else:
                    error_msg = "Downloaded file is empty or not created"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
                    
            elif response.status_code == 404:
                error_msg = f"File not found: {file_id}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            else:
                error_msg = f"Download file API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during file download: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except IOError as e:
            error_msg = f"File write error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during file download: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def is_online(self) -> Dict[str, Any]:
        """
        Check if WeChat is online.
        
        Returns:
            dict: Online status result
        """
        try:
            url = f"{self.api_url}/v1/wechat/isonline"
            
            payload = {
                "wxname": self.wxname
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"WeChat online status checked successfully: {result}")
                if not result.get("success"):
                    return {
                        "success": False,
                        "data": result
                    }
                else:
                    return {
                        "success": True,
                        "data": result
                    }
            else:
                error_msg = f"IsOnline API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during is_online check: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during is_online check: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}


class WXAutoChannel(BaseChannel):
    """
    WXAuto channel for WeChat automation.
    
    Uses polling to get new messages from WXAuto API.
    """

    name = "wxauto"
    display_name = "WXAuto"

    def __init__(self, config: WXAutoConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: WXAutoConfig = config
        self._api: Optional[WXAutoAPI] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._chat_name_to_id: Dict[str, str] = {}  # Map chat names to chat IDs
        
        # Load chat-specific configuration
        self._chat_config = self._load_chat_config()
    
    def _load_chat_config(self) -> WXAutoChannelConfig:
        """Load chat-specific configuration from file."""
        from nanobot.config.paths import get_runtime_subdir
        
        config_dir = get_runtime_subdir("wxauto_config")
        config_path = config_dir / "chat_config.json"
        
        return WXAutoChannelConfig.load(config_path)

    async def start(self) -> None:
        """Start the WXAuto channel with polling."""
        if not self.config.api_url or not self.config.api_key:
            logger.error("WXAuto API URL or API key not configured")
            return

        self._running = True
        self._api = WXAutoAPI(self.config.api_url, self.config.api_key, self.config.wxname)

        # Check if WeChat is online
        online_result = self._api.is_online()
        if not online_result.get("success"):
            logger.warning("WeChat may not be online or WXAuto API is not accessible")
        else:
            logger.info("WXAuto channel connected successfully")

        logger.info("Starting WXAuto channel (polling mode)...")

        # Start polling task
        self._polling_task = asyncio.create_task(self._polling_loop())

        # Keep running until stopped
        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the WXAuto channel."""
        self._running = False

        # Cancel polling task
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped WXAuto channel")

    async def send(self, msg: OutboundMessage) -> None:
        """Send a message through WXAuto."""
        if not self._api:
            logger.warning("WXAuto API not initialized")
            return
        
        if msg.metadata.get("_progress") and not self.config.showProgress:
            logger.warning(f"progress: {msg.content}")
            return

        # Extract chat name from chat_id (format: "wxauto:chat_name")
        # If chat_id doesn't have prefix, use it directly
        if msg.chat_id.startswith("wxauto:"):
            chat_name = msg.chat_id.split(":", 1)[1]
        else:
            chat_name = msg.chat_id

        # Send text content
        if msg.content and msg.content != "[empty message]":
            for chunk in split_message(msg.content, 1000):  # WeChat message length limit
                result = self._api.send_text_message(chat_name, chunk, exact=True)
                if not result.get("success"):
                    logger.error(f"Failed to send message to '{chat_name}': {result.get('error')}")

        # Send media files
        for media_path in (msg.media or []):
            if os.path.exists(media_path):
                result = self._api.send_file_message(chat_name, media_path, exact=True)
                if not result.get("success"):
                    logger.error(f"Failed to send file to '{chat_name}': {result.get('error')}")
            else:
                logger.error(f"Media file not found: {media_path}")

    async def _polling_loop(self) -> None:
        """Poll for new messages from WXAuto API."""
        logger.info("WXAuto polling started (interval: {}s)", self.config.poll_interval)

        while self._running and self._api:
            try:
                # Get next new message
                result = self._api.get_next_new_message(timeout=30)
                
                if result.get("success") and result.get("has_message"):
                    await self._handle_incoming_message(result)
                elif not result.get("success"):
                    logger.error("Error polling for messages: {}", result.get("error"))
                
                # Wait before next poll
                await asyncio.sleep(self.config.poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in polling loop: {}", e)
                await asyncio.sleep(self.config.poll_interval)

    async def _handle_incoming_message(self, result: Dict[str, Any]) -> None:
        """Handle an incoming message from WXAuto with chat-specific configuration."""
        chat_name = result.get("chat_name", "Unknown")
        chat_type = result.get("chat_type", "unknown")
        messages = result.get("messages", [])
        
        # Get chat-specific configuration
        chat_config = self._chat_config.get_chat_config(chat_name)
        
        # Build content from messages
        content_parts = []
        media_paths = []
        has_mention = False
        
        # Check if this is a group with mention policy
        is_group_with_mention = (chat_type == "group" and self.config.group_policy == "mention")
        
        for msg in messages:
            if msg.get("attr") == "self":
                logger.info(f"skip message from yourself: {msg.get('content', '')[:50]}...")
                continue

            msg_type = msg.get("type", "text")
            msg_content = msg.get("content", "")
            
            # For group messages with mention policy, check if this message has @mention
            if is_group_with_mention and msg_type == "text":
                if f"@{self.config.wxname}" not in msg_content:
                    # Skip text messages without @mention in group with mention policy
                    logger.debug(f"Skipping text message without @mention in group '{chat_name}'")
                    continue
                else:
                    has_mention = True
            
            # Check if this message type should be processed based on config
            should_process = False
            if chat_config:
                should_process = chat_config.should_process(msg_type)
            
            if not should_process:
                logger.debug(f"Skipping {msg_type} message from '{chat_name}' (not enabled in config)")
                continue
            
            # Process the message based on type
            if msg_type == "text":
                content_parts.append(msg_content)
            
            elif msg_type == "image":
                # Download image if file_id is available
                file_id = msg.get("file_id")
                if file_id and self._api:
                    # Create media directory per chat: wxauto/{chat_name}/
                    media_dir = get_media_dir(f"wxauto/{chat_name}")
                    # Get filename from file_info if available, otherwise use default
                    file_info = msg.get("file_info", {})
                    filename = file_info.get("filename", f"{file_id[:16]}.png")
                    file_path = media_dir / filename
                    
                    download_result = self._api.download_file(file_id, str(file_path))
                    if download_result.get("success"):
                        media_paths.append(str(file_path))
                        # Add prompt if configured
                        prompt = chat_config.get_prompt("image") if chat_config else ""
                        if prompt:
                            content_parts.append(f"{prompt} [image: {file_path}]")
                        else:
                            content_parts.append(f"[image: {file_path}]")
                    else:
                        content_parts.append(f"[image: download failed]")
                else:
                    content_parts.append(f"[image: {msg_content}]")
            
            elif msg_type == "file":
                # Download file if file_id is available
                file_id = msg.get("file_id")
                if file_id and self._api:
                    # Create media directory per chat: wxauto/{chat_name}/
                    media_dir = get_media_dir(f"wxauto/{chat_name}")
                    # Get filename from file_info if available, otherwise use default
                    file_info = msg.get("file_info", {})
                    filename = file_info.get("filename", f"{file_id[:16]}.bin")
                    file_path = media_dir / filename
                    
                    download_result = self._api.download_file(file_id, str(file_path))
                    if download_result.get("success"):
                        media_paths.append(str(file_path))
                        # Add prompt if configured
                        prompt = chat_config.get_prompt("file") if chat_config else ""
                        if prompt:
                            content_parts.append(f"{prompt} [file: {file_path}]")
                        else:
                            content_parts.append(f"[file: {file_path}]")
                    else:
                        content_parts.append(f"[file: download failed]")
                else:
                    content_parts.append(f"[file: {msg_content}]")
            
            elif msg_type == "link":
                url = msg.get("url", msg_content)
                # Add prompt if configured
                prompt = chat_config.get_prompt("link") if chat_config else ""
                if prompt:
                    content_parts.append(f"[link: {url}] {prompt}")
                else:
                    content_parts.append(f"[link: {url}]")
            
            elif msg_type == "voice":
                voice_text = msg.get("voice_to_text", msg_content)
                content_parts.append(f"[voice: {voice_text}]")
            
            else:
                content_parts.append(f"[{msg_type}: {msg_content}]")
        
        # If no content parts after filtering, skip this message
        if not content_parts:
            logger.debug(f"No processable messages from '{chat_name}' after config filtering")
            return
        
        content = "\n".join(content_parts)
        
        # Generate sender_id (use chat_name for now, could be enhanced)
        sender_id = f"wxauto:{chat_name}"
        
        # Store chat name to ID mapping
        self._chat_name_to_id[sender_id] = chat_name
        
        logger.debug("WXAuto message from {}: {}...", chat_name, content[:50])
        
        # Forward to the message bus
        await self._handle_message(
            sender_id=sender_id,
            chat_id=f"wxauto:{chat_name}",  # Use prefixed chat_id
            content=content,
            media=media_paths,
            metadata={
                "chat_name": chat_name,
                "chat_type": chat_type,
                "message_count": len(messages),
                "has_mention": has_mention,
                "raw_data": result.get("raw_data", {})
            }
        )

    def is_allowed(self, sender_id: str) -> bool:
        """Check if sender is allowed based on chat name."""
        if super().is_allowed(sender_id):
            return True
        
        # Extract chat name from sender_id
        if sender_id.startswith("wxauto:"):
            chat_name = sender_id.split(":", 1)[1]
        else:
            chat_name = sender_id
        
        allow_list = getattr(self.config, "allow_from", [])
        if not allow_list:
            return False
        if "*" in allow_list:
            return True
        
        return chat_name in allow_list