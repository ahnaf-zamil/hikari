#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
import mock
import pytest

from hikari.clients import components
from hikari.clients.rest import base
from hikari.net import ratelimits
from hikari.net import rest


class TestBaseRESTComponent:
    @pytest.fixture()
    def low_level_rest_impl(self) -> rest.REST:
        return mock.MagicMock(
            rest.REST,
            global_ratelimiter=mock.create_autospec(ratelimits.ManualRateLimiter, spec_set=True),
            bucket_ratelimiters=mock.create_autospec(ratelimits.RESTBucketManager, spec_set=True),
        )

    @pytest.fixture()
    def rest_clients_impl(self, low_level_rest_impl) -> base.BaseRESTComponent:
        class RestClientImpl(base.BaseRESTComponent):
            def __init__(self):
                super().__init__(mock.MagicMock(components.Components), low_level_rest_impl)

        return RestClientImpl()

    @pytest.mark.asyncio
    async def test___aenter___and___aexit__(self, rest_clients_impl):
        rest_clients_impl.close = mock.AsyncMock()
        async with rest_clients_impl as client:
            assert client is rest_clients_impl
        rest_clients_impl.close.assert_called_once_with()

    def test_global_ratelimit_queue_size(self, rest_clients_impl, low_level_rest_impl):
        low_level_rest_impl.global_ratelimiter.queue = [object() for _ in range(107)]
        assert rest_clients_impl.global_ratelimit_queue_size == 107

    def test_route_ratelimit_queue_size(self, rest_clients_impl, low_level_rest_impl):
        low_level_rest_impl.bucket_ratelimiters.real_hashes_to_buckets = {
            "aaaaa;1234;5678;9101123": mock.create_autospec(
                ratelimits.RESTBucket, spec_set=True, queue=[object() for _ in range(30)]
            ),
            "aaaaa;1234;5678;9101122": mock.create_autospec(
                ratelimits.RESTBucket, spec_set=True, queue=[object() for _ in range(29)]
            ),
            "aaaab;1234;5678;9101123": mock.create_autospec(
                ratelimits.RESTBucket, spec_set=True, queue=[object() for _ in range(28)]
            ),
            "zzzzz;1234;5678;9101123": mock.create_autospec(
                ratelimits.RESTBucket, spec_set=True, queue=[object() for _ in range(20)]
            ),
        }

        assert rest_clients_impl.route_ratelimit_queue_size == 107
