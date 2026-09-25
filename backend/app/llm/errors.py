"""Failures of the model call. HTTP details stay generic."""


class ModelUnavailableError(Exception):
    """The provider could not be called. No draft was accepted."""


class InvalidModelOutputError(Exception):
    """The provider responded, but the body was not a valid analysis."""


class LLMConfigError(Exception):
    """The process is configured to call a provider it cannot authenticate."""


class ToolLoopError(Exception):
    """The model kept calling tools until the step cap. No draft was accepted."""
