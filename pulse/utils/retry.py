"""Retry utilities for API calls with exponential backoff."""

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from pulse.utils.logger import get_logger

log = get_logger(__name__)

T = TypeVar("T")


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (TimeoutError, ConnectionError, OSError),
) -> Callable:
    """
    Decorator to add retry logic to async functions.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff calculation
        retryable_exceptions: Tuple of exception types that should trigger retry

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(max_retries=3, initial_delay=1.0)
        async def fetch_data(url: str) -> dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(initial_delay * (exponential_base**attempt), max_delay)

                        # Add jitter (random variation) to avoid thundering herd
                        jitter = delay * 0.1 * (0.5 + asyncio.random())
                        total_delay = delay + jitter

                        log.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {total_delay:.1f}s..."
                        )

                        await asyncio.sleep(total_delay)
                    else:
                        log.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
                        raise

            # This should never be reached, but satisfies type checker
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected error in {func.__name__}")

        return wrapper

    return decorator


class RetryPolicy:
    """
    Configurable retry policy for API calls.

    Attributes:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff
        retry_on_status: HTTP status codes to retry on
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retry_on_status: tuple[int, ...] = (429, 500, 502, 503, 504),
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on_status = retry_on_status

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Check if a retry should be attempted."""
        if attempt >= self.max_retries:
            return False

        # Check for specific exception types
        if isinstance(exception, (TimeoutError, ConnectionError, OSError)):
            return True

        # Check for HTTP status codes in exception
        error_str = str(exception).lower()
        for status in self.retry_on_status:
            if str(status) in error_str or f"status {status}" in error_str:
                return True

        return False

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        delay = min(self.initial_delay * (self.exponential_base**attempt), self.max_delay)
        # Add 10% jitter
        jitter = delay * 0.1 * (0.5 + asyncio.random())
        return delay + jitter


async def retry_async_call(
    func: Callable[..., T],
    *args: Any,
    policy: RetryPolicy | None = None,
    **kwargs: Any,
) -> T:
    """
    Execute an async function with retry logic.

    Args:
        func: Async function to execute
        *args: Positional arguments for the function
        policy: Optional RetryPolicy, uses default if not provided
        **kwargs: Keyword arguments for the function

    Returns:
        Result from the function

    Raises:
        The last exception if all retries are exhausted
    """
    if policy is None:
        policy = RetryPolicy()

    last_exception: Exception | None = None

    for attempt in range(policy.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if policy.should_retry(attempt, e):
                delay = policy.get_delay(attempt)
                log.warning(
                    f"Attempt {attempt + 1}/{policy.max_retries + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                log.error(f"All {policy.max_retries + 1} attempts failed for {func.__name__}: {e}")
                raise

    # Should not reach here
    if last_exception:
        raise last_exception
    raise RuntimeError(f"Unexpected error executing {func.__name__}")
