from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class NormalizedField(BaseModel, Generic[T]):
    field_name: str
    original_value: Any
    normalized_value: Optional[T] = None
    field_type: str
    is_valid: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "field_type": self.field_type,
            "is_valid": self.is_valid,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class NormalizedRecord(BaseModel):
    record_type: str  # TRANSACTION, INVOICE, CRYPTO
    fields: Dict[str, NormalizedField[Any]] = Field(default_factory=dict)
    all_valid: bool = True
    warnings: List[str] = Field(default_factory=list)

    def get_normalized(self, field_name: str, default: Any = None) -> Any:
        field = self.fields.get(field_name)
        if field and field.is_valid and field.normalized_value is not None:
            return field.normalized_value
        return default

    def get_original(self, field_name: str, default: Any = None) -> Any:
        field = self.fields.get(field_name)
        if field:
            return field.original_value
        return default
