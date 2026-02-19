from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from src.helper.config import get_settings, Settings
from .LLMProviderEnums import LLMProviderEnum


class LLMProvider:
    def __init__(self):
        self.settings: Settings = get_settings()
        self.provider_name = self.settings.LLM_PROVIDER
        self.model_name = self.settings.LLM_MODEL
        self.model = self._initialize_model()

    def _initialize_model(self):
        if self.provider_name == LLMProviderEnum.GROQ.value:
            return ChatGroq(
                model=self.model_name,
                temperature=self.settings.LLM_TEMPERATURE,
                api_key=self.settings.API_KEY_GROQ,
            )

        elif self.provider_name == LLMProviderEnum.OLLAMA.value:
            return ChatOllama(
                model=self.model_name,
                base_url=self.settings.API_URL_LLM,
                temperature=self.settings.LLM_TEMPERATURE,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider_name}")

    def get_model(self):
        return self.model
