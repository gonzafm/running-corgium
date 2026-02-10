"""Tests for the deployment factory module."""

import pytest

from src.deployment import (
    AWSFactory,
    DeploymentFactory,
    DeploymentMode,
    StandaloneFactory,
    get_factory,
)


class TestDeploymentMode:
    def test_aws_value(self):
        assert DeploymentMode.AWS == "aws"

    def test_standalone_value(self):
        assert DeploymentMode.STANDALONE == "standalone"

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            DeploymentMode("invalid")


class TestGetFactory:
    def test_aws_returns_aws_factory(self):
        factory = get_factory("aws")
        assert isinstance(factory, AWSFactory)

    def test_standalone_returns_standalone_factory(self):
        factory = get_factory("standalone")
        assert isinstance(factory, StandaloneFactory)

    def test_invalid_backend_raises(self):
        with pytest.raises(ValueError):
            get_factory("postgres")

    def test_returns_deployment_factory(self):
        """Both factories satisfy the DeploymentFactory interface."""
        assert isinstance(get_factory("aws"), DeploymentFactory)
        assert isinstance(get_factory("standalone"), DeploymentFactory)