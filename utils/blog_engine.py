"""
Blog Engine - Flat-File CMS for Markdown Posts
===============================================
Handles scanning, parsing, and caching of Markdown blog posts.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import frontmatter
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension


# Configuration
POSTS_DIR = Path("./posts")
DEFAULT_AUTHOR = "Muhsin Kompas"
DATE_FORMAT = "%Y-%m-%d"


@dataclass
class BlogPost:
    """Represents a single blog post."""
    slug: str
    title: str
    date: datetime
    content_html: str
    content_raw: str
    excerpt: str
    tags: List[str] = field(default_factory=list)
    author: str = DEFAULT_AUTHOR
    featured_image: Optional[str] = None
    reading_time: int = 1
    is_draft: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def date_formatted(self) -> str:
        """Return formatted date string."""
        return self.date.strftime("%B %d, %Y")

    @property
    def date_iso(self) -> str:
        """Return ISO formatted date string."""
        return self.date.strftime("%Y-%m-%d")

    @property
    def year(self) -> int:
        """Return the year of the post."""
        return self.date.year

    @property
    def month(self) -> int:
        """Return the month of the post."""
        return self.date.month

    def to_dict(self) -> Dict[str, Any]:
        """Convert post to dictionary for template rendering."""
        return {
            "slug": self.slug,
            "title": self.title,
            "date": self.date,
            "date_formatted": self.date_formatted,
            "date_iso": self.date_iso,
            "content": self.content_html,
            "content_raw": self.content_raw,
            "excerpt": self.excerpt,
            "tags": self.tags,
            "author": self.author,
            "featured_image": self.featured_image,
            "reading_time": self.reading_time,
            "is_draft": self.is_draft,
            "meta": self.meta,
        }


class BlogEngine:
    """
    Flat-File CMS Blog Engine.
    
    Scans a directory for Markdown files, parses them with frontmatter,
    and provides methods to retrieve posts with caching.
    """

    def __init__(self, posts_dir: str | Path = POSTS_DIR):
        self.posts_dir = Path(posts_dir)
        self._cache_timestamp: Optional[float] = None
        
        # Configure Markdown parser with extensions
        self.md = markdown.Markdown(
            extensions=[
                FencedCodeExtension(),
                CodeHiliteExtension(
                    css_class="highlight",
                    linenums=False,
                    guess_lang=True,
                ),
                TableExtension(),
                TocExtension(
                    permalink=True,
                    permalink_class="header-link",
                    toc_depth="2-4",
                ),
                "nl2br",  # Newline to <br>
                "smarty",  # Smart quotes
                "attr_list",  # Attribute lists for elements
            ],
            output_format="html5",
        )

    def _calculate_reading_time(self, text: str) -> int:
        """Calculate estimated reading time in minutes."""
        words = len(text.split())
        reading_time = max(1, round(words / 200))  # Assume 200 WPM
        return reading_time

    def _generate_excerpt(self, content: str, max_length: int = 160) -> str:
        """Generate excerpt from content."""
        # Remove HTML tags
        clean_text = re.sub(r"<[^>]+>", "", content)
        # Remove extra whitespace
        clean_text = " ".join(clean_text.split())
        
        if len(clean_text) <= max_length:
            return clean_text
        
        # Truncate at word boundary
        truncated = clean_text[:max_length].rsplit(" ", 1)[0]
        return truncated + "..."

    def _extract_slug_from_filename(self, filename: str) -> str:
        """Extract slug from filename (e.g., '2024-01-30-hello-world.md' -> 'hello-world')."""
        # Remove .md extension
        name = filename.rsplit(".", 1)[0]
        
        # Check if filename starts with date pattern (YYYY-MM-DD-)
        date_pattern = re.match(r"^\d{4}-\d{2}-\d{2}-(.+)$", name)
        if date_pattern:
            return date_pattern.group(1)
        
        return name

    def _parse_post(self, filepath: Path) -> Optional[BlogPost]:
        """Parse a single Markdown file into a BlogPost object."""
        try:
            # Load frontmatter and content
            post = frontmatter.load(filepath)
            
            # Skip drafts in production (optional: can be controlled via env var)
            is_draft = post.get("draft", False)
            
            # Extract metadata
            title = post.get("title", "Untitled")
            
            # Parse date - try frontmatter first, then filename
            date_str = post.get("date")
            if date_str:
                if isinstance(date_str, datetime):
                    date = date_str
                else:
                    date = datetime.strptime(str(date_str), DATE_FORMAT)
            else:
                # Try to extract from filename
                filename = filepath.name
                date_match = re.match(r"^(\d{4}-\d{2}-\d{2})", filename)
                if date_match:
                    date = datetime.strptime(date_match.group(1), DATE_FORMAT)
                else:
                    date = datetime.fromtimestamp(filepath.stat().st_mtime)
            
            # Get slug
            slug = post.get("slug") or self._extract_slug_from_filename(filepath.name)
            
            # Parse tags
            tags = post.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            
            # Reset markdown parser state
            self.md.reset()
            
            # Render content
            content_html = self.md.convert(post.content)
            
            # Generate excerpt
            excerpt = post.get("excerpt") or post.get("description") or self._generate_excerpt(content_html)
            
            return BlogPost(
                slug=slug,
                title=title,
                date=date,
                content_html=content_html,
                content_raw=post.content,
                excerpt=excerpt,
                tags=tags,
                author=post.get("author", DEFAULT_AUTHOR),
                featured_image=post.get("featured_image") or post.get("image"),
                reading_time=self._calculate_reading_time(post.content),
                is_draft=is_draft,
                meta=dict(post.metadata),
            )
            
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return None

    def _get_posts_dir_mtime(self) -> float:
        """Get the latest modification time of the posts directory."""
        if not self.posts_dir.exists():
            return 0.0
        
        latest_mtime = self.posts_dir.stat().st_mtime
        
        for filepath in self.posts_dir.glob("*.md"):
            mtime = filepath.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime
        
        return latest_mtime

    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed based on file changes."""
        current_mtime = self._get_posts_dir_mtime()
        
        if self._cache_timestamp is None:
            return True
        
        return current_mtime > self._cache_timestamp

    @lru_cache(maxsize=1)
    def _load_all_posts_cached(self, cache_key: float) -> List[BlogPost]:
        """
        Load all posts with LRU cache.
        
        The cache_key parameter is used to invalidate the cache
        when files are modified.
        """
        posts = []
        
        if not self.posts_dir.exists():
            print(f"Warning: Posts directory '{self.posts_dir}' does not exist.")
            return posts
        
        for filepath in self.posts_dir.glob("*.md"):
            post = self._parse_post(filepath)
            if post:
                posts.append(post)
        
        # Sort by date (newest first)
        posts.sort(key=lambda p: p.date, reverse=True)
        
        return posts

    def get_all_posts(self, include_drafts: bool = False) -> List[BlogPost]:
        """
        Get all blog posts, sorted by date (newest first).
        
        Args:
            include_drafts: Whether to include draft posts.
        
        Returns:
            List of BlogPost objects.
        """
        # Check if we need to refresh the cache
        if self._should_refresh_cache():
            self._load_all_posts_cached.cache_clear()
            self._cache_timestamp = self._get_posts_dir_mtime()
        
        posts = self._load_all_posts_cached(self._cache_timestamp or 0)
        
        if not include_drafts:
            posts = [p for p in posts if not p.is_draft]
        
        return posts

    def get_post_by_slug(self, slug: str) -> Optional[BlogPost]:
        """
        Get a single post by its slug.
        
        Args:
            slug: The post slug.
        
        Returns:
            BlogPost object or None if not found.
        """
        posts = self.get_all_posts(include_drafts=True)
        
        for post in posts:
            if post.slug == slug:
                return post
        
        return None

    def get_posts_by_tag(self, tag: str) -> List[BlogPost]:
        """
        Get all posts with a specific tag.
        
        Args:
            tag: The tag to filter by.
        
        Returns:
            List of BlogPost objects.
        """
        posts = self.get_all_posts()
        return [p for p in posts if tag.lower() in [t.lower() for t in p.tags]]

    def get_all_tags(self) -> Dict[str, int]:
        """
        Get all tags with their post counts.
        
        Returns:
            Dictionary mapping tags to post counts.
        """
        tags: Dict[str, int] = {}
        
        for post in self.get_all_posts():
            for tag in post.tags:
                tag_lower = tag.lower()
                tags[tag_lower] = tags.get(tag_lower, 0) + 1
        
        return dict(sorted(tags.items(), key=lambda x: x[1], reverse=True))

    def get_recent_posts(self, limit: int = 5) -> List[BlogPost]:
        """
        Get the most recent posts.
        
        Args:
            limit: Maximum number of posts to return.
        
        Returns:
            List of BlogPost objects.
        """
        return self.get_all_posts()[:limit]

    def get_related_posts(self, post: BlogPost, limit: int = 3) -> List[BlogPost]:
        """
        Get posts related to the given post (by tags).
        
        Args:
            post: The reference post.
            limit: Maximum number of related posts.
        
        Returns:
            List of related BlogPost objects.
        """
        all_posts = self.get_all_posts()
        
        # Score posts by number of shared tags
        scored_posts = []
        for p in all_posts:
            if p.slug == post.slug:
                continue
            
            shared_tags = len(set(t.lower() for t in p.tags) & set(t.lower() for t in post.tags))
            if shared_tags > 0:
                scored_posts.append((shared_tags, p))
        
        # Sort by score (highest first) and return top results
        scored_posts.sort(key=lambda x: x[0], reverse=True)
        
        return [p for _, p in scored_posts[:limit]]

    def search_posts(self, query: str) -> List[BlogPost]:
        """
        Search posts by title and content.
        
        Args:
            query: Search query string.
        
        Returns:
            List of matching BlogPost objects.
        """
        query_lower = query.lower()
        results = []
        
        for post in self.get_all_posts():
            if (query_lower in post.title.lower() or 
                query_lower in post.content_raw.lower() or
                any(query_lower in tag.lower() for tag in post.tags)):
                results.append(post)
        
        return results

    def clear_cache(self) -> None:
        """Clear the post cache."""
        self._load_all_posts_cached.cache_clear()
        self._cache_timestamp = None


# Global blog engine instance
blog_engine = BlogEngine()


def get_blog_engine() -> BlogEngine:
    """Get the global blog engine instance."""
    return blog_engine