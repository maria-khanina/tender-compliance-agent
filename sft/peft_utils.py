"""Narrows peft/trl's necessarily-Union return types (they cover call
shapes this project never uses, like get_peft_model(mixed=True) or a
Trainer built without a model) down to the concrete PeftModel our own
training scripts actually work with, in one place instead of at every
call site.
"""
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import PreTrainedModel


def wrap_with_lora(model: PreTrainedModel, lora_config: LoraConfig) -> PeftModel:
    wrapped = get_peft_model(model, lora_config)
    assert isinstance(wrapped, PeftModel)
    return wrapped


def as_peft_model(model: object) -> PeftModel:
    assert isinstance(model, PeftModel)
    return model
