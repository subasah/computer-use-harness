"""
Model Context Protocol (MCP) JSON-RPC 2.0 Data Structures and Types.
Compliant with Model Context Protocol specification.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request."""
    jsonrpc: Literal["2.0"] = "2.0"
    id: Union[int, str]
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCNotification(BaseModel):
    """JSON-RPC 2.0 Notification (no id, no response expected)."""
    jsonrpc: Literal["2.0"] = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCErrorDetail(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response."""
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[int, str]] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCErrorDetail] = None


class MCPToolParameterSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class MCPToolDefinition(BaseModel):
    """Definition of an individual tool exposed by an MCP server."""
    name: str
    description: Optional[str] = ""
    inputSchema: Dict[str, Any] = Field(default_factory=dict)


class MCPContentItem(BaseModel):
    type: Literal["text", "image", "resource"] = "text"
    text: Optional[str] = None
    data: Optional[str] = None
    mimeType: Optional[str] = None


class MCPCallToolResult(BaseModel):
    """Result of calling a tool on an MCP server."""
    content: List[MCPContentItem] = Field(default_factory=list)
    isError: bool = False


class MCPResourceDefinition(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None
