"""Unit tests for provider inference functionality."""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codebase_summarizer.main import _infer_provider_from_model
from services.llm_usage_metrics import LLMProvider


def test_infer_openai_models():
    """Test inference of OpenAI models."""
    assert _infer_provider_from_model("gpt-4") == LLMProvider.OPENAI
    assert _infer_provider_from_model("gpt-4-turbo") == LLMProvider.OPENAI
    assert _infer_provider_from_model("gpt-4o") == LLMProvider.OPENAI
    assert _infer_provider_from_model("gpt-4o-mini") == LLMProvider.OPENAI
    assert _infer_provider_from_model("gpt-3.5-turbo") == LLMProvider.OPENAI
    assert _infer_provider_from_model("gpt-5") == LLMProvider.OPENAI
    assert _infer_provider_from_model("gpt-5-mini") == LLMProvider.OPENAI
    assert _infer_provider_from_model("gpt-5-nano") == LLMProvider.OPENAI
    print("✓ OpenAI model inference tests passed")


def test_infer_anthropic_models():
    """Test inference of Anthropic models and aliases."""
    assert _infer_provider_from_model("claude-sonnet-4-20250514") == LLMProvider.ANTHROPIC
    assert _infer_provider_from_model("claude-opus-4-1-20250805") == LLMProvider.ANTHROPIC
    assert _infer_provider_from_model("sonnet") == LLMProvider.ANTHROPIC
    assert _infer_provider_from_model("opus") == LLMProvider.ANTHROPIC
    print("✓ Anthropic model inference tests passed")


def test_infer_google_models():
    """Test inference of Google models."""
    assert _infer_provider_from_model("gemini-2.5-pro") == LLMProvider.GOOGLE
    assert _infer_provider_from_model("gemini-2.5-flash") == LLMProvider.GOOGLE
    print("✓ Google model inference tests passed")


def test_unknown_model():
    """Test handling of unknown models."""
    assert _infer_provider_from_model("unknown-model") is None
    assert _infer_provider_from_model("") is None
    assert _infer_provider_from_model("random-string") is None
    print("✓ Unknown model handling tests passed")


def test_case_sensitivity():
    """Test that model inference is case-sensitive."""
    # These should work (exact matches)
    assert _infer_provider_from_model("gpt-4") == LLMProvider.OPENAI
    assert _infer_provider_from_model("sonnet") == LLMProvider.ANTHROPIC

    # These should not work (wrong case)
    assert _infer_provider_from_model("GPT-4") is None
    assert _infer_provider_from_model("SONNET") is None
    print("✓ Case sensitivity tests passed")


def test_partial_matches():
    """Test that partial matches don't incorrectly infer providers."""
    # These should not match
    assert _infer_provider_from_model("gpt") is None
    assert _infer_provider_from_model("claude") is None
    assert _infer_provider_from_model("gemini") is None
    assert _infer_provider_from_model("sonnet-extra") is None
    print("✓ Partial match tests passed")


def test_inference_completeness():
    """Test that all models in AVAILABLE_MODELS can be inferred."""
    from services.llm_usage_metrics import AVAILABLE_MODELS

    for provider in LLMProvider:
        provider_config = AVAILABLE_MODELS[provider]

        # Test all direct models
        for model in provider_config["models"]:
            inferred = _infer_provider_from_model(model)
            assert inferred == provider, f"Failed to infer {provider.value} for model {model}"

        # Test all aliases
        aliases = provider_config.get("aliases", {})
        for alias in aliases.keys():
            inferred = _infer_provider_from_model(alias)
            assert inferred == provider, f"Failed to infer {provider.value} for alias {alias}"
    print("✓ Inference completeness tests passed")


if __name__ == "__main__":
    print("Running provider inference unit tests...")
    test_infer_openai_models()
    test_infer_anthropic_models()
    test_infer_google_models()
    test_unknown_model()
    test_case_sensitivity()
    test_partial_matches()
    test_inference_completeness()
    print("\nAll tests passed!")