from app.config import Settings, get_settings

from .provider import AIProvider, MockProvider


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    provider_name = settings.AI_PROVIDER.value if settings.AI_PROVIDER else "MOCK"
    if provider_name == Settings.AIProviderEnum.OPENAI.value:
        # Lazy import to avoid requiring openai when not used
        from .provider import OpenAIProvider
        return OpenAIProvider()
    return MockProvider()
