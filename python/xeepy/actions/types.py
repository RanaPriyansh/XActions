"""
Xeepy Action Types

Data classes and types for action results and configurations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TweetElement:
    """Represents a tweet element scraped from the page."""

    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    url: Optional[str] = None  # alias for tweet_url
    text: Optional[str] = None
    author_username: Optional[str] = None
    author_display_name: Optional[str] = None
    author_followers: Optional[int] = None
    # New canonical field names (Optional, default None)
    like_count: Optional[int] = None
    retweet_count: Optional[int] = None
    reply_count: Optional[int] = None
    view_count: Optional[int] = None
    # Legacy aliases (kept for existing code)
    likes_count: int = 0
    retweets_count: int = 0
    replies_count: int = 0
    views_count: int = 0
    is_retweet: bool = False
    is_reply: bool = False
    is_quote: bool = False
    has_media: bool = False
    has_text: bool = True
    language: Optional[str] = None
    timestamp: Optional[datetime] = None
    hashtags: Optional[list] = None
    mentions: Optional[list] = None

    @property
    def engagement_score(self) -> int:
        """Calculate total engagement score."""
        lc = self.like_count if self.like_count is not None else self.likes_count
        rc = self.retweet_count if self.retweet_count is not None else self.retweets_count
        pc = self.reply_count if self.reply_count is not None else self.replies_count
        return lc + rc + pc


@dataclass
class UserElement:
    """Represents a user element scraped from the page."""
    
    user_id: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    tweets_count: int = 0
    is_verified: bool = False
    is_following: bool = False
    profile_url: Optional[str] = None


@dataclass
class LikeResult:
    """Result of a like operation (single-tweet or aggregate)."""

    # Single-tweet result fields
    success: Optional[bool] = None
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    was_already_liked: bool = False
    error: Optional[str] = None
    # Aggregate fields
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    liked_tweets: list = field(default_factory=list)
    failed_tweets: list = field(default_factory=list)
    skipped_tweets: list = field(default_factory=list)
    duration_seconds: float = 0.0
    rate_limited: bool = False
    cancelled: bool = False
    errors: list = field(default_factory=list)
    
    @property
    def total_processed(self) -> int:
        return self.success_count + self.failed_count + self.skipped_count
    
    def to_dict(self) -> dict:
        return {
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "liked_tweets": self.liked_tweets,
            "duration_seconds": self.duration_seconds,
            "rate_limited": self.rate_limited,
            "cancelled": self.cancelled,
        }


@dataclass
class CommentResult:
    """Result of a comment operation."""

    # Single-tweet result fields
    success: Optional[bool] = None
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    comment_text: Optional[str] = None
    reply_tweet_id: Optional[str] = None
    error: Optional[str] = None
    # Aggregate fields
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    comments_posted: list = field(default_factory=list)
    failed_comments: list = field(default_factory=list)
    duration_seconds: float = 0.0
    rate_limited: bool = False
    cancelled: bool = False
    errors: list = field(default_factory=list)
    
    @property
    def total_processed(self) -> int:
        return self.success_count + self.failed_count + self.skipped_count
    
    def to_dict(self) -> dict:
        return {
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "comments_posted": self.comments_posted,
            "duration_seconds": self.duration_seconds,
            "rate_limited": self.rate_limited,
            "cancelled": self.cancelled,
        }


@dataclass
class RetweetResult:
    """Result of a retweet operation."""

    # Single-tweet result fields
    success: Optional[bool] = None
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    is_quote_tweet: bool = False
    quote_text: Optional[str] = None
    was_already_retweeted: bool = False
    error: Optional[str] = None
    # Aggregate fields
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    retweeted_tweets: list = field(default_factory=list)
    quoted_tweets: list = field(default_factory=list)
    failed_tweets: list = field(default_factory=list)
    duration_seconds: float = 0.0
    rate_limited: bool = False
    cancelled: bool = False
    errors: list = field(default_factory=list)
    
    @property
    def total_processed(self) -> int:
        return self.success_count + self.failed_count + self.skipped_count
    
    def to_dict(self) -> dict:
        return {
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "retweeted_tweets": self.retweeted_tweets,
            "quoted_tweets": self.quoted_tweets,
            "duration_seconds": self.duration_seconds,
            "rate_limited": self.rate_limited,
            "cancelled": self.cancelled,
        }


@dataclass
class BookmarkResult:
    """Result of a bookmark operation."""

    # Single-tweet result fields
    success: Optional[bool] = None
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    action: Optional[str] = None  # 'add' or 'remove'
    was_already_bookmarked: bool = False
    error: Optional[str] = None
    # Aggregate fields
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    bookmarked_tweets: list = field(default_factory=list)
    removed_bookmarks: list = field(default_factory=list)
    failed_tweets: list = field(default_factory=list)
    exported_count: int = 0
    export_path: Optional[str] = None
    duration_seconds: float = 0.0
    rate_limited: bool = False
    cancelled: bool = False
    errors: list = field(default_factory=list)
    
    @property
    def total_processed(self) -> int:
        return self.success_count + self.failed_count
    
    def to_dict(self) -> dict:
        return {
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "bookmarked_tweets": self.bookmarked_tweets,
            "exported_count": self.exported_count,
            "export_path": self.export_path,
            "duration_seconds": self.duration_seconds,
            "rate_limited": self.rate_limited,
            "cancelled": self.cancelled,
        }


@dataclass
class LikeFilters:
    """Filters for like operations."""

    min_likes: int = 0
    max_likes: Optional[int] = None
    min_retweets: int = 0
    max_retweets: Optional[int] = None
    min_followers: int = 0
    max_followers: Optional[int] = None
    exclude_retweets: bool = False
    exclude_replies: bool = False
    exclude_media_only: bool = False
    require_text: bool = True
    language: Optional[str] = None
    include_keywords: list = field(default_factory=list)
    exclude_keywords: list = field(default_factory=list)
    blocked_keywords: list = field(default_factory=list)
    blocked_users: list = field(default_factory=list)
    
    def matches(self, tweet: TweetElement) -> tuple[bool, str]:
        """
        Check if a tweet matches the filters.
        
        Returns:
            (matches, reason)
        """
        # Check engagement limits
        lc = tweet.like_count if tweet.like_count is not None else tweet.likes_count
        rc = tweet.retweet_count if tweet.retweet_count is not None else tweet.retweets_count
        if lc < self.min_likes:
            return False, f"too few likes ({lc} < {self.min_likes})"
        if self.max_likes is not None and lc > self.max_likes:
            return False, f"too many likes ({lc} > {self.max_likes})"
        if rc < self.min_retweets:
            return False, f"too few retweets ({rc} < {self.min_retweets})"
        if self.max_retweets is not None and rc > self.max_retweets:
            return False, f"too many retweets ({rc} > {self.max_retweets})"

        # Check author followers
        if tweet.author_followers is not None:
            if tweet.author_followers < self.min_followers:
                return False, "author has too few followers"
            if self.max_followers is not None and tweet.author_followers > self.max_followers:
                return False, "author has too many followers"
        
        # Check tweet type
        if self.exclude_retweets and tweet.is_retweet:
            return False, "is retweet"
        if self.exclude_replies and tweet.is_reply:
            return False, "is reply"
        if self.exclude_media_only and tweet.has_media and not tweet.has_text:
            return False, "media only (no text)"
        if self.require_text and not tweet.has_text:
            return False, "no text content"
        
        # Check language
        if self.language and tweet.language and tweet.language != self.language:
            return False, f"wrong language ({tweet.language})"
        
        # Check blocked keywords
        if tweet.text:
            text_lower = tweet.text.lower()
            for keyword in self.blocked_keywords:
                if keyword.lower() in text_lower:
                    return False, f"contains blocked keyword: {keyword}"
        
        # Check blocked users
        if tweet.author_username:
            username_lower = tweet.author_username.lower()
            for user in self.blocked_users:
                if user.lower() == username_lower:
                    return False, f"from blocked user: {user}"
        
        return True, "passed all filters"


@dataclass
class AutoLikeConfig:
    """Configuration for auto-liker."""
    
    # Targeting
    keywords: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    from_users: list[str] = field(default_factory=list)
    
    # Filtering
    min_likes: int = 0
    max_likes: int = 10000
    min_followers: int = 100
    exclude_retweets: bool = True
    exclude_replies: bool = False
    exclude_media_only: bool = False
    require_text: bool = True
    language: str = "en"
    
    # Blacklist
    blocked_keywords: list[str] = field(default_factory=list)
    blocked_users: list[str] = field(default_factory=list)
    
    # Limits
    max_likes_per_session: int = 50
    max_likes_per_hour: int = 30
    delay_range: tuple = field(default_factory=lambda: (2, 5))
    min_delay: float = 30.0
    max_delay: float = 120.0
    skip_retweets: bool = False
    
    # Advanced
    like_probability: float = 1.0  # Random chance to like (0-1)
    also_retweet: bool = False
    also_bookmark: bool = False
    
    def to_filters(self) -> LikeFilters:
        """Convert to LikeFilters."""
        return LikeFilters(
            min_likes=self.min_likes,
            max_likes=self.max_likes,
            min_followers=self.min_followers,
            exclude_retweets=self.exclude_retweets,
            exclude_replies=self.exclude_replies,
            exclude_media_only=self.exclude_media_only,
            require_text=self.require_text,
            language=self.language,
            blocked_keywords=self.blocked_keywords,
            blocked_users=self.blocked_users,
        )


@dataclass
class AutoCommentConfig:
    """Configuration for auto-commenter."""
    
    # Targeting
    keywords: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    from_users: list[str] = field(default_factory=list)
    
    # Comments
    templates: list[str] = field(default_factory=list)
    use_ai: bool = False
    ai_style: str = "helpful"  # 'helpful', 'casual', 'professional', 'witty'
    ai_max_length: int = 280
    
    # Smart features
    mention_author: bool = False
    add_hashtags: bool = False
    personalize: bool = True
    
    # Filtering
    min_likes: int = 0
    max_likes: int = 10000
    min_followers: int = 100
    exclude_retweets: bool = True
    
    # Limits
    max_comments_per_session: int = 10
    max_comments_per_hour: int = 5
    delay_range: tuple = field(default_factory=lambda: (60, 120))
    min_delay: float = 60.0
    max_delay: float = 180.0
    
    # Safety
    review_before_post: bool = True
    blocked_keywords: list[str] = field(default_factory=list)
    blocked_users: list[str] = field(default_factory=list)


@dataclass
class AutoRetweetConfig:
    """Configuration for auto-retweeter."""
    
    # Targeting
    keywords: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    from_users: list[str] = field(default_factory=list)
    
    # Filtering
    min_likes: int = 10
    max_likes: int = 50000
    min_followers: int = 500
    exclude_replies: bool = True
    language: str = "en"
    
    # Blacklist
    blocked_keywords: list[str] = field(default_factory=list)
    blocked_users: list[str] = field(default_factory=list)
    
    # Limits
    max_retweets_per_session: int = 20
    max_retweets_per_hour: int = 10
    delay_range: tuple = field(default_factory=lambda: (5, 15))
    min_delay: float = 5.0
    max_delay: float = 30.0
    
    # Advanced
    retweet_probability: float = 1.0
    quote_instead: bool = False
    quote_templates: list[str] = field(default_factory=list)
