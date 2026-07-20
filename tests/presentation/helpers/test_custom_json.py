"""Тесты для helpers presentation layer."""

import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from payment_processing_service.presentation.utils.helpers.custom_json import (
    CustomJsonEncoder,
    CustomJSONResponse,
    custom_json_serializer,
    dumps,
    loads,
)


class SamplePydanticModel(BaseModel):
    """Тестовая Pydantic модель."""

    name: str
    value: int


class TestCustomJsonEncoder:
    """Тесты для CustomJsonEncoder."""

    def test_encodes_datetime(self):
        """Должен сериализовать datetime."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = json.dumps(dt, cls=CustomJsonEncoder)
        assert '"2024-01-15T10:30:00"' in result

    def test_encodes_date(self):
        """Должен сериализовать date."""
        d = date(2024, 1, 15)
        result = json.dumps(d, cls=CustomJsonEncoder)
        assert '"2024-01-15"' in result

    def test_encodes_time(self):
        """Должен сериализовать time."""
        t = time(10, 30, 0)
        result = json.dumps(t, cls=CustomJsonEncoder)
        assert '"10:30:00"' in result

    def test_encodes_timedelta(self):
        """Должен сериализовать timedelta."""
        td = timedelta(days=1, hours=2, minutes=3)
        result = json.dumps(td, cls=CustomJsonEncoder)
        # isodate может сериализовать как P1DT2H3M
        assert "PT" in result or "P1D" in result

    def test_encodes_decimal(self):
        """Должен сериализовать Decimal как float."""
        d = Decimal("1500.50")
        result = json.dumps(d, cls=CustomJsonEncoder)
        assert "1500.5" in result

    def test_encodes_uuid(self):
        """Должен сериализовать UUID как строку."""
        uid = uuid4()
        result = json.dumps(uid, cls=CustomJsonEncoder)
        assert f'"{uid}"' in result

    def test_encodes_set(self):
        """Должен сериализовать set как list."""
        s = {1, 2, 3}
        result = json.dumps(s, cls=CustomJsonEncoder)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert set(parsed) == {1, 2, 3}

    def test_encodes_pydantic_model(self):
        """Должен сериализовать Pydantic модель."""
        model = SamplePydanticModel(name="test", value=42)
        result = json.dumps(model, cls=CustomJsonEncoder)
        parsed = json.loads(result)
        assert parsed["name"] == "test"
        assert parsed["value"] == 42

    def test_encodes_dict(self):
        """Должен рекурсивно сериализовать dict."""
        data = {"amount": Decimal("100"), "date": datetime(2024, 1, 1)}
        result = json.dumps(data, cls=CustomJsonEncoder)
        parsed = json.loads(result)
        assert parsed["amount"] == 100.0
        assert "2024-01-01" in parsed["date"]

    def test_encodes_list(self):
        """Должен сериализовать list."""
        data = [Decimal("100"), Decimal("200")]
        result = json.dumps(data, cls=CustomJsonEncoder)
        parsed = json.loads(result)
        assert parsed == [100.0, 200.0]

    def test_encodes_none_as_null_string(self):
        """Должен сериализовать None как строку 'null'."""
        data = {"value": None}
        result = json.dumps(data, cls=CustomJsonEncoder)
        parsed = json.loads(result)
        assert parsed["value"] is None

    def test_encodes_nested_structures(self):
        """Должен сериализовать вложенные структуры."""
        data = {
            "payment": {
                "amount": Decimal("1500.00"),
                "created": datetime(2024, 1, 15, 10, 30),
                "meta": {"address": "1234567890123456"},
            }
        }
        result = json.dumps(data, cls=CustomJsonEncoder)
        parsed = json.loads(result)
        assert parsed["payment"]["amount"] == 1500.0
        assert parsed["payment"]["meta"]["address"] == "1234567890123456"


class TestCustomJSONResponse:
    """Тесты для CustomJSONResponse."""

    def test_render_datetime(self):
        """render должен корректно сериализовать datetime."""
        response = CustomJSONResponse(content={"timestamp": datetime(2024, 1, 15, 10, 30)})
        rendered = response.render({"timestamp": datetime(2024, 1, 15, 10, 30)})
        assert b"2024-01-15T10:30:00" in rendered

    def test_render_decimal(self):
        """render должен корректно сериализовать Decimal."""
        response = CustomJSONResponse(content={"amount": Decimal("1500.50")})
        rendered = response.render({"amount": Decimal("1500.50")})
        assert b"1500.5" in rendered

    def test_render_uuid(self):
        """render должен корректно сериализовать UUID."""
        uid = uuid4()
        rendered = CustomJSONResponse(content={"id": uid}).render({"id": uid})
        assert str(uid).encode() in rendered

    def test_render_nested(self):
        """render должен корректно сериализовать вложенные структуры."""
        data = {
            "payment": {
                "amount": Decimal("100"),
                "created": datetime(2024, 1, 1),
            }
        }
        rendered = CustomJSONResponse(content=data).render(data)
        parsed = json.loads(rendered)
        assert parsed["payment"]["amount"] == 100.0


class TestCustomJsonHelpers:
    """Тесты для helper функций custom_json."""

    def test_custom_json_serializer(self):
        """custom_json_serializer должен сериализовать с CustomJsonEncoder."""
        data = {"amount": Decimal("100")}
        result = custom_json_serializer(data)
        parsed = json.loads(result)
        assert parsed["amount"] == 100.0

    def test_dumps_default_encoder(self):
        """dumps должен использовать CustomJsonEncoder по умолчанию."""
        data = {"amount": Decimal("100")}
        result = dumps(data)
        parsed = json.loads(result)
        assert parsed["amount"] == 100.0

    def test_dumps_with_cls(self):
        """dumps должен использовать переданный cls."""
        data = {"value": "test"}
        result = dumps(data, cls=json.JSONEncoder)
        assert '"test"' in result

    def test_loads(self):
        """loads должен десериализовать JSON."""
        data = '{"amount": 100.0}'
        result = loads(data)
        assert result["amount"] == 100.0
