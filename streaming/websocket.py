"""
WebSocket connection manager for real-time audio streaming
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.audio_buffers: Dict[str, List[bytes]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.audio_buffers[client_id] = []
        logger.info(f"Client {client_id} connected")
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.audio_buffers:
            del self.audio_buffers[client_id]
        logger.info(f"Client {client_id} disconnected")
        
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                
    async def broadcast(self, message: dict):
        for client_id in self.active_connections:
            await self.send_message(client_id, message)
            
    def add_audio_chunk(self, client_id: str, audio_data: bytes):
        if client_id in self.audio_buffers:
            self.audio_buffers[client_id].append(audio_data)
            
    def get_audio_buffer(self, client_id: str) -> bytes:
        if client_id in self.audio_buffers:
            return b"".join(self.audio_buffers[client_id])
        return b""
        
    def clear_buffer(self, client_id: str):
        if client_id in self.audio_buffers:
            self.audio_buffers[client_id] = []


manager = ConnectionManager()