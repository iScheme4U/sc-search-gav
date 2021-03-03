#  The MIT License (MIT)
#
#  Copyright (c) 2021. Scott Lau
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import logging

from .request_api import RequestClient


class GavSearchClient(RequestClient):
    """
    A class to interact with search.maven.org site's API.

    Args:
        url (str): the url.
    """
    SEARCH_ENDPOINT = "solrsearch/select"

    def __init__(self, *, url):
        super(GavSearchClient, self).__init__(url=url, x509_verify=True)

    @staticmethod
    def get_query_str(params):
        query_str = ""
        first = True
        for key, value in params.items():
            if first:
                first = False
            else:
                query_str += " AND "
            query_str += key + ':"' + value + '"'
        return query_str

    def search_with_sha1(self, sha1):
        params = {"1": sha1}
        query_params = {
            "q": GavSearchClient.get_query_str(params)
        }
        return self.http_request(method="get", endpoint=GavSearchClient.SEARCH_ENDPOINT, params=query_params)

    def search_with_artifact(self, *, group_id, artifact_id, version, packaging="jar"):
        params = {
            "g": group_id,
            "a": artifact_id,
            "v": version,
            "p": packaging
        }
        query_params = {
            "q": GavSearchClient.get_query_str(params)
        }
        return self.http_request(method="get", endpoint=GavSearchClient.SEARCH_ENDPOINT, params=query_params)

    @staticmethod
    def parse_online_search_result(response):
        if response is None:
            return None
        ret_json = response.json()
        if 'response' not in ret_json:
            return None
        if 'numFound' not in ret_json['response']:
            return None
        num_found = int(ret_json['response']["numFound"])
        if num_found == 0:
            return None
        if "docs" not in ret_json['response']:
            return None
        # found artifact
        docs = ret_json['response']["docs"]
        item = docs[0]
        oldest_timestamp = item['timestamp']
        if len(docs) > 1:
            logging.getLogger(__name__).warning('multiple artifacts found, choose the oldest artifact')
            # choose the oldest artifact
            for doc in docs:
                timestamp = doc['timestamp']
                if timestamp < oldest_timestamp:
                    oldest_timestamp = timestamp
                    item = doc
        return {'groupId': item['g'], 'artifactId': item['a'], 'version': item['v']}
