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

import csv
import logging
import os

from scutils import Singleton

from .exception import *
from .gav_search_api import GavSearchClient
from .project_config_file_utils import ProjectConfigFileUtils
from .search_constants import SearchConstants
from .utils import config


class GavSearcher(metaclass=Singleton):

    def __init__(self):
        self._online_url = config.get("url") or "https://search.maven.org"
        self._online_client = GavSearchClient(url=self._online_url)
        self._hash_file = "lib-hash.csv"
        self._report_file = 'report.csv'
        self._retries_str = config.get("retries") or "3"
        self._retries = int(self._retries_str)
        self._artifacts = {}
        self._dependencies = []
        self._exception_dependencies = []
        self._unknown_dependencies = []

    def search_dependency_gav(self):
        dependencies = []
        # if report.csv found, parse hash values from this file directly
        source_file = self._hash_file
        dependencies.extend(ProjectConfigFileUtils.parse_dependencies_from_csv(source_file))
        self._search_dependencies(dependencies)
        self._generate_project_config_files()
        self._generate_report()

    def _search_dependencies(self, dependencies):
        for dependency in dependencies:
            filename = dependency['filename']
            hash_value = dependency[SearchConstants.DEFAULT_HASH_NAME]
            found = None
            if "found" in dependency:
                found = dependency["found"]
            # check if artifact already found
            if found == "Y":
                self._dependencies.append(dependency)
                key = GavSearcher.get_artifact_full_name(dependency)
                if key not in self._artifacts:
                    self._artifacts[key] = dependency
            else:
                result = self._search_dependency(hash_value, filename)
                if len(result) > 0 and "found" in result and result['found']:
                    self._dependencies.append(result)
                    key = GavSearcher.get_artifact_full_name(result)
                    if key not in self._artifacts:
                        self._artifacts[key] = result
                elif len(result) > 0 and "exception" in result and result['exception']:
                    self._exception_dependencies.append(result)
                else:
                    self._unknown_dependencies.append(dependency)

    def _search_dependency(self, hash_value, filename):
        result = self._search_online(hash_value, filename)
        if len(result) > 0 and "found" in result and result['found']:
            result['found_with'] = 'online'
            return result
        result['found_with'] = ''
        return result

    def _search_online(self, hash_value, filename):
        logging.getLogger(__name__).info('search online with %s %s', SearchConstants.DEFAULT_HASH_NAME, hash_value)
        response = None
        retry_count = 0
        while response is None:
            try:
                response = self._online_client.search_with_sha1(hash_value)
                break
            except HttpClientAPIError as e:
                logging.getLogger(__name__).warning('timed out when finding hash %s online', hash_value)
                retry_count += 1
                if retry_count > self._retries:
                    result = dict()
                    result['filename'] = filename
                    result['found'] = False
                    result['exception'] = True
                    result[SearchConstants.DEFAULT_HASH_NAME] = hash_value
                    logging.getLogger(__name__).error('failed to find %s online, retried % times, cause: %s',
                                                      hash_value, self._retries, e)
                    return result
        parsed_result = GavSearchClient.parse_online_search_result(response)
        if parsed_result is not None:
            logging.getLogger(__name__).info('hash %s found online, artifact: %s', hash_value, parsed_result)
            parsed_result['filename'] = filename
            parsed_result['found'] = True
            parsed_result[SearchConstants.DEFAULT_HASH_NAME] = hash_value
            return parsed_result
        logging.getLogger(__name__).warning('artifact %s not found online', hash_value)
        return {}

    def _generate_project_config_files(self):
        dependencies = self._artifacts.values()
        ProjectConfigFileUtils.generate_maven_config(dependencies)
        ProjectConfigFileUtils.generate_gradle_config(dependencies)
        ProjectConfigFileUtils.generate_ant_config(dependencies)

    def _generate_report(self):
        logging.getLogger(__name__).info('generating report.csv...')
        with open(self._report_file, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['File Name', SearchConstants.DEFAULT_HASH_NAME, 'Found', 'Found With', 'Group Id',
                             'Artifact Id', 'Version'])
            for dependency in self._dependencies:
                writer.writerow([
                    dependency['filename'],
                    dependency[SearchConstants.DEFAULT_HASH_NAME],
                    'Y',  # Found
                    dependency['found_with'],
                    dependency['groupId'],
                    dependency['artifactId'],
                    dependency['version']
                ])
            for dependency in self._exception_dependencies:
                writer.writerow([
                    dependency['filename'],
                    dependency[SearchConstants.DEFAULT_HASH_NAME],
                    'Exception',  # Found
                    '',  # Found With
                    '',  # groupId
                    '',  # artifactId
                    ''  # version
                ])
            for dependency in self._unknown_dependencies:
                writer.writerow([
                    dependency['filename'],
                    dependency[SearchConstants.DEFAULT_HASH_NAME],
                    'N',  # Found
                    '',  # Found With
                    '',  # groupId
                    '',  # artifactId
                    ''  # version
                ])

    @staticmethod
    def get_artifact_full_name(artifact_map):
        return artifact_map['groupId'] + artifact_map['artifactId'] + artifact_map['version']
