import abc
import typing
from typing import Any

from pydantic import BaseModel, Field


def UserConfigurable(*args, **kwargs):
    return Field(*args, **kwargs, user_configurable=True)


class SystemConfiguration(BaseModel):
    def get_user_config(self) -> dict[str, Any]:
        return _get_user_config_fields(self)

    class Config:
        extra = "forbid"
        use_enum_values = True


class SystemSettings(BaseModel):
    """A base class for all system settings."""

    name: str
    description: str

    class Config:
        extra = "forbid"
        use_enum_values = True


class Configurable(abc.ABC):
    """A base class for all configurable objects."""

    prefix: str = ""
    defaults: typing.ClassVar[SystemSettings]

    @classmethod
    def get_user_config(cls) -> dict[str, Any]:
        return _get_user_config_fields(cls.defaults)

    @classmethod
    def build_agent_configuration(cls, configuration: dict) -> SystemSettings:
        """Process the configuration for this object."""

        final_configuration = cls.defaults.dict()
        final_configuration.update(configuration)

        return cls.defaults.__class__.parse_obj(final_configuration)


def _get_user_config_fields(instance: BaseModel) -> dict[str, Any]:
    """
    Get the user config fields of a Pydantic model instance.

    Args:
        instance: The Pydantic model instance.

    Returns:
        The user config fields of the instance.
    """
    user_config_fields = {}

    for name, value in instance.__dict__.items():
        field_info = instance.__fields__[name]
        if "user_configurable" in field_info.field_info.extra:
            user_config_fields[name] = value
        elif isinstance(value, SystemConfiguration):
            user_config_fields[name] = value.get_user_config()
        elif isinstance(value, list) and all(
            isinstance(i, SystemConfiguration) for i in value
        ):
            user_config_fields[name] = [i.get_user_config() for i in value]
        elif isinstance(value, dict) and all(
            isinstance(i, SystemConfiguration) for i in value.values()
        ):
            user_config_fields[name] = {
                k: v.get_user_config() for k, v in value.items()
            }

    return user_config_fields