# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
REST API performance endpoint. Provides information on monthly performance.
e.g., number of tier deployments by status and total for every month since
first tier deployment in database.
"""


from datetime import datetime, timedelta

from cornice.resource import resource, view

import tds.model
from . import base
from .urls import ALL_URLS
from .permissions import PERFORMANCE_PERMISSIONS


@resource(path=ALL_URLS['performance'])
class PerformanceView(base.BaseView):
    """
    Performance view.
    """

    permissions = PERFORMANCE_PERMISSIONS

    model_dict = dict(
        packages=dict(model=tds.model.Package, attr='created'),
        deployments=dict(model=tds.model.Deployment, attr='declared'),
        tier_deployments=dict(model=tds.model.AppDeployment, attr='realized'),
        host_deployments=dict(model=tds.model.HostDeployment, attr='realized'),
    )

    @staticmethod
    def _add_one_month(date_obj):
        return (date_obj.replace(day=1) + timedelta(days=32)).replace(day=1)

    def validate_performance_get(self, request):
        """
        Validate a performance GET request.
        """
        self.name = 'performance'
        self._validate_params([])
        obj_type = request.matchdict['obj_type']
        if obj_type not in self.model_dict:
            request.errors.add(
                'path', 'obj_type',
                "Unknown object type {obj_type}. Supported object types are: "
                "{types}.".format(
                    obj_type=obj_type,
                    types=sorted(self.model_dict.keys()),
                )
            )
            self.request.errors.status = 404
            return

        latest = datetime.today()
        time_fmt = "%Y-%m-%d %H:%M:%S"
        to_return = dict()
        model = self.model_dict[obj_type]['model']
        col_name = self.model_dict[obj_type]['attr']
        # for model_name in self.model_dict:
        date_objs = list()
        # model = self.model_dict[model_name]['model']
        # col_name = self.model_dict[model_name]['attr']
        column = getattr(model, col_name)
        if getattr(model, 'delegate', None):
            table = model.delegate.__table__
        else:
            table = model.__table__
        statuses = table.columns['status'].type.enums
        earliest = min(
            [getattr(obj, col_name) for obj in self.query(model).all()] +
            [latest]
        )
        earliest = datetime(
            year=earliest.year, month=earliest.month, day=1
        )
        current = earliest
        month_later = self._add_one_month(current)
        while month_later <= latest:
            date_obj = dict(month=current.strftime("%Y-%m"))
            all_objs = self.query(model).filter(
                column < month_later.strftime(time_fmt),
                column >= current.strftime(time_fmt)
            ).all()
            date_obj['total'] = len(all_objs)
            for status in statuses:
                date_obj[status] = len([
                    obj for obj in all_objs if
                    getattr(obj, 'status') == status
                ])
            date_objs.append(date_obj)
            current = self._add_one_month(current)
            month_later = self._add_one_month(current)
        # to_return[model_name] = date_objs
        # self.result = to_return
        self.result = date_objs

    def validate_performance_options(self, _request):
        """
        Validate a performance OPTIONS request.
        """
        self.result = dict(
            GET=dict(
                description="Get metrics on packages, tier deployments, host "
                    "deployments, or deployments by month for all months.",
                parameters=dict(),
            ),
            HEAD=dict(description="Do a GET query without a body returned."),
            OPTIONS=dict(
                description="Get HTTP method options and parameters for this "
                    "URL endpoint.",
            )
        )

    @view(validators=('validate_performance_get', 'validate_cookie'))
    def get(self):
        """
        Perform a GET request after all validation has passed.
        """
        return self.make_response(self.to_json_obj(self.result))

    @view(validators=('validate_performance_get', 'validate_cookie'))
    def head(self):
        """
        Same as get above except returns empty body.
        """
        return self.make_response(renderer="empty")

    @view(validators=('validate_performance_options',))
    def options(self):
        """
        Perform an OPTIONS request after all validation has passed.
        """
        return self.make_response(
            body=self.to_json_obj(self.result),
            headers=dict(Allows="GET, HEAD, OPTIONS"),
        )

    @view(validators=('method_not_allowed'))
    def delete(self):
        """
        Method not allowed.
        """
        return self.make_response({})
