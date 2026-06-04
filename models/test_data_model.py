import json
from pydantic import BaseModel, AnyHttpUrl


class CredentialsModel(BaseModel):
    username: str
    password: str

    def __repr__(self) -> str:
        return "CredentialsModel(username='***', password='***')"

    def __str__(self) -> str:
        return self.__repr__()


class SearchModel(BaseModel):
    query: str
    max_price: float
    limit: int = 5


class TimeoutsModel(BaseModel):
    page_load: int
    element: int
    navigation: int


class TestDataModel(BaseModel):
    base_url: AnyHttpUrl
    login_url: AnyHttpUrl
    cart_url: AnyHttpUrl
    credentials: CredentialsModel
    search: list[SearchModel]
    budget_per_item: float
    timeouts: TimeoutsModel

    @classmethod
    def load_and_validate(cls, path: str) -> "TestDataModel":
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"test_data.json not found at path: {path}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"test_data.json is not valid JSON: {exc}")

        try:
            return cls.model_validate(raw)
        except Exception as exc:
            raise ValueError(f"test_data.json validation failed: {exc}") from exc
