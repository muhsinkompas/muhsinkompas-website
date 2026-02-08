"""
Knowledge Base Manager
======================
Handles loading and caching of terminal command data from knowledge_base.json
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


# Configuration
KB_FILE = Path("./data/knowledge_base.json")


@dataclass
class Command:
    """Represents a single terminal command."""
    command: str
    comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "comment": self.comment,
        }


@dataclass
class Terminal:
    """Represents a terminal window with multiple commands."""
    id: str
    title: str
    commands: List[Command] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "commands": [cmd.to_dict() for cmd in self.commands],
        }


class KnowledgeBaseManager:
    """
    Knowledge Base Manager.
    
    Loads terminal command data from JSON and provides caching.
    """

    def __init__(self, kb_file: str | Path = KB_FILE):
        self.kb_file = Path(kb_file)
        self._cache_timestamp: Optional[float] = None

    def _get_kb_file_mtime(self) -> float:
        """Get the modification time of the knowledge base file."""
        if not self.kb_file.exists():
            return 0.0
        return self.kb_file.stat().st_mtime

    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed based on file changes."""
        current_mtime = self._get_kb_file_mtime()
        
        if self._cache_timestamp is None:
            return True
        
        return current_mtime > self._cache_timestamp

    @lru_cache(maxsize=1)
    def _load_terminals_cached(self, cache_key: float) -> List[Terminal]:
        """
        Load terminals with LRU cache.
        
        The cache_key parameter is used to invalidate the cache
        when the file is modified.
        """
        terminals = []
        
        if not self.kb_file.exists():
            print(f"Warning: Knowledge base file '{self.kb_file}' does not exist.")
            return terminals
        
        try:
            with open(self.kb_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            terminals_data = data.get("terminals", [])
            
            for term_data in terminals_data:
                commands = []
                for cmd_data in term_data.get("commands", []):
                    commands.append(Command(
                        command=cmd_data.get("command", ""),
                        comment=cmd_data.get("comment"),
                    ))
                
                terminals.append(Terminal(
                    id=term_data.get("id", ""),
                    title=term_data.get("title", "terminal"),
                    commands=commands,
                ))
        
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
        
        return terminals

    def get_terminals(self) -> List[Terminal]:
        """
        Get all terminal windows.
        
        Returns:
            List of Terminal objects.
        """
        # Check if we need to refresh the cache
        if self._should_refresh_cache():
            self._load_terminals_cached.cache_clear()
            self._cache_timestamp = self._get_kb_file_mtime()
        
        terminals = self._load_terminals_cached(self._cache_timestamp or 0)
        return terminals

    def get_terminal_by_id(self, terminal_id: str) -> Optional[Terminal]:
        """
        Get a single terminal by its ID.
        
        Args:
            terminal_id: The terminal ID.
        
        Returns:
            Terminal object or None if not found.
        """
        terminals = self.get_terminals()
        
        for terminal in terminals:
            if terminal.id == terminal_id:
                return terminal
        
        return None

    def clear_cache(self) -> None:
        """Clear the terminal cache."""
        self._load_terminals_cached.cache_clear()
        self._cache_timestamp = None


# Global knowledge base manager instance
kb_manager = KnowledgeBaseManager()


def get_kb_manager() -> KnowledgeBaseManager:
    """Get the global knowledge base manager instance."""
    return kb_manager
