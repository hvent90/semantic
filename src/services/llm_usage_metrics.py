"""LLM Usage Metrics Collector for tracking token usage and costs."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMUsageMetrics:
    """Represents usage metrics for a single LLM call."""
    provider: LLMProvider
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    timestamp: datetime
    operation_type: str  # e.g., "skillset_detection", "api_description"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging."""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
            "timestamp": self.timestamp.isoformat(),
            "operation_type": self.operation_type
        }


class LLMUsageCollector:
    """
    Interface for all LLM calls that collects and logs usage metrics.
    
    This class acts as a wrapper around LLM clients (e.g., OpenAI's client)
    and ensures all usage is tracked and logged to the console for monitoring.
    """
    
    # Cost per 1K tokens (as of 2024) - these should be updated periodically
    COST_PER_1K_TOKENS = {
        LLMProvider.OPENAI: {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        },
        LLMProvider.ANTHROPIC: {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        }
    }
    
    def __init__(self):
        """Initialize the LLM usage collector."""
        self._total_cost = 0.0
        self._total_calls = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        logger.info("LLM Usage Collector initialized")
    
    def estimate_cost(
        self,
        provider: LLMProvider,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate the cost of an LLM call based on token usage.
        
        Args:
            provider: The LLM provider
            model: The specific model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        if provider not in self.COST_PER_1K_TOKENS:
            logger.warning(f"Unknown provider {provider}, cannot estimate cost")
            return 0.0
        
        provider_costs = self.COST_PER_1K_TOKENS[provider]
        if model not in provider_costs:
            logger.warning(f"Unknown model {model} for provider {provider}, cannot estimate cost")
            return 0.0
        
        model_costs = provider_costs[model]
        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]
        
        return input_cost + output_cost
    
    def log_usage(
        self,
        provider: LLMProvider,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation_type: str
    ) -> LLMUsageMetrics:
        """
        Log usage metrics for an LLM call.
        
        Args:
            provider: The LLM provider
            model: The specific model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            operation_type: Type of operation (e.g., "skillset_detection")
            
        Returns:
            LLMUsageMetrics object with the logged metrics
        """
        total_tokens = input_tokens + output_tokens
        estimated_cost = self.estimate_cost(provider, model, input_tokens, output_tokens)
        timestamp = datetime.utcnow()
        
        metrics = LLMUsageMetrics(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            timestamp=timestamp,
            operation_type=operation_type
        )
        
        # Update running totals
        self._total_cost += estimated_cost
        self._total_calls += 1
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        
        # Log to console (structured format for CI/CD)
        logger.info(f"LLM Usage: {json.dumps(metrics.to_dict(), indent=None)}")
        
        return metrics
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all LLM usage in the current session.
        
        Returns:
            Dictionary containing session usage summary
        """
        return {
            "total_calls": self._total_calls,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "total_estimated_cost": self._total_cost,
            "average_cost_per_call": self._total_cost / self._total_calls if self._total_calls > 0 else 0.0
        }
    
    def log_session_summary(self) -> None:
        """Log the session summary to the console."""
        summary = self.get_session_summary()
        logger.info(f"LLM Session Summary: {json.dumps(summary, indent=None)}")


# Global instance to be used across the application
llm_usage_collector = LLMUsageCollector()