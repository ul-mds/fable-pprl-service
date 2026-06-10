import pytest

from pprl_service.config import Role
from pprl_service.main import create_app


@pytest.mark.parametrize(
    "role,expected_route_names,not_expected_route_names",
    [
        (Role.both, ["preprocess_entities", "mask_entities", "perform_matching"], []),
        (Role.data_owner, ["preprocess_entities", "mask_entities"], ["perform_matching"]),
        (Role.linkage_unit, ["perform_matching"], ["preprocess_entities", "mask_entities"]),
    ],
)
def test_different_roles(monkeypatch, role, expected_route_names, not_expected_route_names):
    monkeypatch.setenv("ROLE", role)
    app = create_app()
    route_names = [route.name for route in app.routes]

    assert all([name in route_names for name in expected_route_names])
    assert all([name not in route_names for name in not_expected_route_names])
