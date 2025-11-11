"""
Pytest fixtures for Library module

所有测试可复用的数据和对象都定义在这里
"""

import pytest
from uuid import uuid4
from backend.api.app.modules.library.domain import Library


@pytest.fixture
def sample_user_id():
    """提供一个示例用户 ID"""
    return uuid4()


@pytest.fixture
def sample_library(sample_user_id):
    """提供一个示例 Library 对象"""
    return Library.create(
        user_id=sample_user_id,
        name="测试知识库"
    )


@pytest.fixture
def sample_library_data(sample_user_id):
    """提供一个示例 Library 数据字典"""
    return {
        "user_id": sample_user_id,
        "name": "测试知识库",
        "description": "用于测试的知识库"
    }# Pytest fixtures for library module
