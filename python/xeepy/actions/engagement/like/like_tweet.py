"""
Like Tweet Action

Like a single tweet by URL or ID.
"""

import asyncio
import re
from typing import Optional

from loguru import logger

from xeepy.actions.base import BaseAction, BrowserManager, RateLimiter
from xeepy.actions.types import LikeResult


class LikeTweet(BaseAction):
    """
    Like a single tweet.
    
    Usage:
        like_action = LikeTweet(browser, rate_limiter)
        result = await like_action.execute("https://x.com/user/status/123456")
    """
    
    SELECTORS = {
        "tweet_article": 'article[data-testid="tweet"]',
        "like_button": '[data-testid="like"]',
        "unlike_button": '[data-testid="unlike"]',
        "tweet_text": '[data-testid="tweetText"]',
    }
    
    def __init__(
        self,
        browser: BrowserManager,
        rate_limiter: Optional[RateLimiter] = None,
        dry_run: bool = False,
        skip_if_liked: bool = True,
    ):
        """
        Initialize LikeTweet action.

        Args:
            browser: Browser manager instance
            rate_limiter: Rate limiter (optional)
            dry_run: If True, don't actually like (for testing)
            skip_if_liked: If True, skip tweets already liked
        """
        self.browser = browser
        self.rate_limiter = rate_limiter
        self.dry_run = dry_run
        self.skip_if_liked = skip_if_liked
    
    async def execute(
        self,
        tweet_url: str,
        skip_if_liked: bool = True,
    ) -> LikeResult:
        """
        Like a tweet.
        
        Args:
            tweet_url: URL of the tweet to like
            skip_if_liked: Skip if already liked
            
        Returns:
            LikeResult with success/failure info
        """
        import time
        start_time = time.time()
        result = LikeResult(tweet_url=tweet_url)

        # Validate URL
        normalized_url = self._normalize_url(tweet_url)
        if not normalized_url:
            result.success = False
            result.failed_count = 1
            result.errors.append("Invalid tweet URL")
            return result

        tweet_url = normalized_url
        result.tweet_url = tweet_url
        _skip_if_liked = skip_if_liked if skip_if_liked is not None else self.skip_if_liked

        # Dry run: skip all browser interaction
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would like: {tweet_url}")
            result.success = True
            result.was_already_liked = False
            result.success_count = 1
            result.liked_tweets.append(tweet_url)
            return result

        try:
            # Apply rate limiting
            if self.rate_limiter and hasattr(self.rate_limiter, 'wait'):
                try:
                    await self.rate_limiter.wait()
                except TypeError:
                    self.rate_limiter.wait()

            # Navigate to tweet
            logger.info(f"Navigating to tweet: {tweet_url}")
            try:
                nav = self.browser.goto(tweet_url)
                if asyncio.iscoroutine(nav):
                    await nav
            except Exception:
                pass
            await asyncio.sleep(2)  # Wait for page load

            # Wait for tweet to load
            try:
                ws = self.browser.wait_for_selector(
                    self.SELECTORS["tweet_article"],
                    timeout=10000
                )
                if asyncio.iscoroutine(ws):
                    await ws
            except Exception:
                pass  # Continue even if selector not found

            # Check if already liked
            unlike_button = await self._find_element(self.SELECTORS["unlike_button"])
            if unlike_button and _skip_if_liked:
                logger.info(f"Tweet already liked: {tweet_url}")
                result.success = True
                result.was_already_liked = True
                result.skipped_count = 1
                result.skipped_tweets.append(tweet_url)
                return result

            # Find like button
            like_button = await self._find_element(self.SELECTORS["like_button"])
            if not like_button:
                result.success = False
                result.failed_count = 1
                result.errors.append("Like button not found")
                return result

            # Perform like
            await like_button.click()
            await asyncio.sleep(1)

            # Verify like was successful
            unlike_button = await self._find_element(self.SELECTORS["unlike_button"])
            if unlike_button:
                logger.info(f"Successfully liked: {tweet_url}")
                result.success = True
                result.success_count = 1
                result.liked_tweets.append(tweet_url)
                if self.rate_limiter:
                    self.rate_limiter.record_success()
            else:
                result.success = False
                result.failed_count = 1
                result.errors.append("Like action failed to register")
                if self.rate_limiter:
                    self.rate_limiter.record_error()

        except Exception as e:
            logger.error(f"Error liking tweet: {e}")
            result.success = False
            result.failed_count = 1
            result.errors.append(str(e))
            if self.rate_limiter:
                self.rate_limiter.record_error()

        result.duration_seconds = time.time() - start_time
        return result
    
    async def unlike(self, tweet_url: str) -> LikeResult:
        """
        Unlike a tweet.
        
        Args:
            tweet_url: URL of the tweet to unlike
            
        Returns:
            LikeResult with success/failure info
        """
        import time
        start_time = time.time()
        result = LikeResult()
        
        tweet_url = self._normalize_url(tweet_url)
        if not tweet_url:
            result.failed_count = 1
            result.errors.append("Invalid tweet URL")
            return result
        
        try:
            if self.rate_limiter:
                await self.rate_limiter.wait()
            
            await self.browser.goto(tweet_url)
            await asyncio.sleep(2)
            
            # Find unlike button (heart is filled)
            unlike_button = await self._find_element(self.SELECTORS["unlike_button"])
            if not unlike_button:
                result.skipped_count = 1
                result.skipped_tweets.append(tweet_url)
                logger.info(f"Tweet not liked (skipping unlike): {tweet_url}")
                return result
            
            if not self.dry_run:
                await unlike_button.click()
                await asyncio.sleep(1)
                
                # Verify unlike
                like_button = await self._find_element(self.SELECTORS["like_button"])
                if like_button:
                    logger.info(f"Successfully unliked: {tweet_url}")
                    result.success_count = 1
                else:
                    result.failed_count = 1
                    result.errors.append("Unlike action failed to register")
            else:
                logger.info(f"[DRY-RUN] Would unlike: {tweet_url}")
                result.success_count = 1
            
        except Exception as e:
            logger.error(f"Error unliking tweet: {e}")
            result.failed_count = 1
            result.errors.append(str(e))
        
        result.duration_seconds = time.time() - start_time
        return result
    
    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize tweet URL to standard format."""
        # Handle tweet ID
        if url.isdigit():
            return f"https://x.com/i/status/{url}"
        
        # Handle various URL formats
        patterns = [
            r'https?://(?:www\.)?(?:twitter|x)\.com/\w+/status/(\d+)',
            r'https?://(?:mobile\.)?(?:twitter|x)\.com/\w+/status/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                tweet_id = match.group(1)
                return f"https://x.com/i/status/{tweet_id}"
        
        # If already in correct format
        if re.match(r'https?://x\.com/', url):
            return url
        
        return None
    
    async def _find_element(self, selector: str):
        """Find an element on the page."""
        try:
            page = self.browser.page if hasattr(self.browser, 'page') else None
            if page is None:
                return None
            return await page.query_selector(selector)
        except Exception:
            return None
