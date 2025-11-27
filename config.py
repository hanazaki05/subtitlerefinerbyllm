"""
Configuration module for subtitle refinement tool.

Defines the Config class with all necessary parameters for the tool,
including API settings, token limits, and model configuration.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """
    Configuration class for subtitle refinement tool.

    Attributes:
        model_name: Name of the LLM model to use (default: "gpt-5.1")
        api_key: OpenAI API key for authentication
        api_base_url: Base URL for API requests (default: OpenAI's endpoint)
        max_context_tokens: Maximum context window size for the model
        max_output_tokens: Maximum tokens for model output
        memory_token_limit: Maximum tokens allowed for global memory
        chunk_token_soft_limit: Soft limit for tokens per chunk (as fraction of max_context)
        pairs_per_chunk: Fixed number of pairs per chunk (overrides token-based chunking)
        reasoning_effort: Level of reasoning effort requested from the model ("none", "low", "medium", "high")
        api_timeout: Timeout for API requests in seconds
        verbose: Enable verbose output with detailed progress and timing
        very_verbose: Dump full API responses after each chunk (implies verbose)
        debug_prompts: Print system prompt/memory for each chunk (implies very verbose)
        stats_interval: Stats refresh interval in seconds (for verbose mode)
        dry_run: Whether to run in test mode (only process limited data)
        max_chunks: Maximum number of chunks to process (None for all)
        price_per_1k_prompt_tokens: Cost per 1000 prompt tokens (USD)
        price_per_1k_completion_tokens: Cost per 1000 completion tokens (USD)
    """

    model_name: str = "gpt-5-mini"
    api_key: str = ""
    api_base_url: str = "https://api.openai.com/v1"
    max_context_tokens: int = 128000
    max_output_tokens: int = 12000
    memory_token_limit: int = 4000
    chunk_token_soft_limit: int = 60000  # ~0.8 * max_context_tokens
    pairs_per_chunk: Optional[int] = None  # If set, override token-based chunking
    reasoning_effort: str = "medium"  # Optional reasoning effort hint for GPT-5.1
    api_timeout: int = 240  # API request timeout in seconds
    verbose: bool = False  # Enable verbose output with detailed progress
    very_verbose: bool = False  # Dump full API responses (requires verbose)
    debug_prompts: bool = False  # Print system prompt/memory (requires very verbose)
    stats_interval: float = 1.0  # Stats refresh interval in seconds (for verbose mode)
    dry_run: bool = False
    max_chunks: Optional[int] = None
    price_per_1k_prompt_tokens: float = 0.03
    price_per_1k_completion_tokens: float = 0.06

    def __post_init__(self):
        """Validate and set default values from environment variables if needed."""
        # Try to get API key from environment if not set
        if not self.api_key:
            self.api_key = os.getenv(
                "OPENAI_API_KEY",
                #"***REMOVED***"
                "***REMOVED***"
            )

        if not self.api_key:
            raise ValueError("API key must be provided either in config or OPENAI_API_KEY environment variable")


def load_config(
    model_name: Optional[str] = None,
    dry_run: bool = False,
    max_chunks: Optional[int] = None,
    memory_limit: Optional[int] = None,
    pairs_per_chunk: Optional[int] = None,
    reasoning_effort: Optional[str] = None,
    api_timeout: Optional[int] = None,
    verbose: bool = False,
    very_verbose: bool = False,
    debug_prompts: bool = False,
    stats_interval: Optional[float] = None
) -> Config:
    """
    Load configuration with optional overrides.

    Args:
        model_name: Override for model name
        dry_run: Enable dry run mode
        max_chunks: Override for maximum chunks to process
        memory_limit: Override for memory token limit
        pairs_per_chunk: Override for pairs per chunk
        reasoning_effort: Override for reasoning effort hint
        api_timeout: Override for API request timeout
        verbose: Enable verbose mode
        very_verbose: Enable very verbose mode (full API outputs)
        debug_prompts: Print system prompt/memory for debugging
        stats_interval: Stats refresh interval in seconds

    Returns:
        Config object with specified settings
    """
    config = Config()

    if model_name:
        config.model_name = model_name
    if dry_run:
        config.dry_run = dry_run
    if max_chunks is not None:
        config.max_chunks = max_chunks
    if memory_limit is not None:
        config.memory_token_limit = memory_limit
    if pairs_per_chunk is not None:
        config.pairs_per_chunk = pairs_per_chunk
    if reasoning_effort is not None:
        config.reasoning_effort = reasoning_effort
    if api_timeout is not None:
        config.api_timeout = api_timeout
    if verbose:
        config.verbose = verbose
    if very_verbose:
        config.very_verbose = very_verbose
        config.verbose = True  # Very verbose implies verbose
    if debug_prompts:
        config.debug_prompts = debug_prompts
        config.very_verbose = True
        config.verbose = True
    if stats_interval is not None:
        config.stats_interval = stats_interval

    return config
