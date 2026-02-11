from __future__ import absolute_import

import six

from client.api_client import ApiClient


class SamApi(object):
    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()

        self.api_client = api_client

    def search(self, **kwargs):
        """
        Makes synchronous HTTP request by default. To make
        asynchronous HTTP request, pass async_req=True
        >>> thread = api.search(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str api_key: Sam.gov API key
        :param str piid: Contract award PIID
        :param str referenced_idv_piid: Referenced IDV PIID for child awards
        :param str naics_code: NAICS code
        :param str contracting_subtier_name: Contracting subtier name
        :param str date_signed: Date signed filter
        :param int limit: Max results to include
        :param int offset: Offset for pagination
        :return: AwardResponse
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs["_return_http_data_only"] = True

        if kwargs.get("async_req"):
            return self.search_with_http_info(**kwargs)
        else:
            data = self.search_with_http_info(**kwargs)
            return data

    def search_with_http_info(self, **kwargs):
        """
        Makes synchronous HTTP request by default. To make
        asynchronous HTTP request, pass async_req=True
        >>> thread = api.search_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str api_key: Sam.gov API key
        :param str piid: Contract award PIID
        :param str naics_code: NAICS code
        :param str contracting_department_name: Agency name
        :param str date_signed: Date signed filter
        :param int limit: Max results to include
        :param int offset: Offset for pagination
        :return: AwardResponse
                 If the method is called asynchronously,
                 returns the request thread.
        """
        all_params = [
            "api_key",
            "piid",
            "referenced_idv_piid",
            "naics_code",
            "contracting_subtier_name",
            "date_signed",
            "limit",
            "offset",
        ]
        all_params.append("async_req")
        all_params.append("_return_http_data_only")
        all_params.append("_preload_content")
        all_params.append("_request_timeout")

        params = locals()

        for key, val in six.iteritems(params["kwargs"]):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'" " to method search" % key
                )

            params[key] = val

        del params["kwargs"]
        collection_formats = {}
        path_params = {}
        query_params = []

        if "api_key" in params:
            query_params.append(("api_key", params["api_key"]))

        if "piid" in params:
            query_params.append(("piid", params["piid"]))

        if "referenced_idv_piid" in params:
            query_params.append(("referencedIdvPiid", params["referenced_idv_piid"]))

        if "naics_code" in params:
            query_params.append(("naicsCode", params["naics_code"]))

        if "contracting_subtier_name" in params:
            query_params.append(
                ("contractingSubtierName", params["contracting_subtier_name"])
            )

        if "date_signed" in params:
            query_params.append(("dateSigned", params["date_signed"]))

        if "limit" in params:
            query_params.append(("limit", params["limit"]))

        if "offset" in params:
            query_params.append(("offset", params["offset"]))

        header_params = {}
        form_params = []
        local_var_files = {}
        body_params = None
        header_params["Accept"] = self.api_client.select_header_accept(
            ["application/json"]
        )
        auth_settings = []

        return self.api_client.call_api(
            "/contract-awards/v1/search",
            "GET",
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type="AwardResponse",
            auth_settings=auth_settings,
            async_req=params.get("async_req"),
            _return_http_data_only=params.get("_return_http_data_only"),
            _preload_content=params.get("_preload_content", True),
            _request_timeout=params.get("_request_timeout"),
            collection_formats=collection_formats,
        )
