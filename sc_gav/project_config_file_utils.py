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

from .search_constants import SearchConstants


class ProjectConfigFileUtils:

    def __init__(self):
        pass

    @staticmethod
    def parse_dependencies_and_generate_config(csv_filename, skip_title_line=True):
        dependencies = ProjectConfigFileUtils.parse_dependencies_from_csv(csv_filename, skip_title_line)
        ProjectConfigFileUtils.generate_maven_config(dependencies)
        ProjectConfigFileUtils.generate_gradle_config(dependencies)
        ProjectConfigFileUtils.generate_ant_config(dependencies)

    @staticmethod
    def parse_dependencies_from_csv(csv_filename, skip_title_line=True):
        dependencies = list()
        try:
            logging.getLogger(__name__).info('read hash values from csv...')
            with open(csv_filename, newline='', encoding='utf-8') as csv_file:
                sr = csv.reader(csv_file, delimiter=',')
                filename_index = -1
                hash_index = -1
                found_index = -1
                found_with_index = -1
                group_id_index = -1
                artifact_id_index = -1
                version_index = -1
                for elements in sr:
                    if skip_title_line:
                        skip_title_line = False
                        for index in range(len(elements)):
                            element = elements[index]
                            if "Group Id" == element:
                                group_id_index = index
                            elif "Artifact Id" == element:
                                artifact_id_index = index
                            elif "Version" == element:
                                version_index = index
                            elif "Found" == element:
                                found_index = index
                            elif "Found With" == element:
                                found_with_index = index
                            elif "File Name" == element:
                                filename_index = index
                            elif SearchConstants.DEFAULT_HASH_NAME == element:
                                hash_index = index
                        if filename_index == -1 or hash_index == -1:
                            logging.getLogger(__name__).error("invalid file format, cannot find correct 'File Name',"
                                                              " and '%s' columns", SearchConstants.DEFAULT_HASH_NAME)
                            break
                        continue
                    filename = elements[filename_index]
                    hash_value = elements[hash_index]
                    found = ""
                    if found_index != -1:
                        found = elements[found_index]
                    found_with = ""
                    if found_with_index != -1:
                        found_with = elements[found_with_index]
                    group_id = ""
                    if group_id_index != -1:
                        group_id = elements[group_id_index]
                    artifact_id = ""
                    if artifact_id_index != -1:
                        artifact_id = elements[artifact_id_index]
                    version = ""
                    if version_index != -1:
                        version = elements[version_index]
                    dependencies.append({
                        'filename': filename,
                        SearchConstants.DEFAULT_HASH_NAME: hash_value,
                        'found': found,
                        'found_with': found_with,
                        'groupId': group_id,
                        'artifactId': artifact_id,
                        'version': version
                    })
        except FileNotFoundError as error:
            logging.getLogger(__name__).error("file %s not found, cause: %s", csv_filename, error)
        return dependencies

    @staticmethod
    def generate_gradle_config(dependencies, filename="build.gradle"):
        logging.getLogger(__name__).info('generating gradle build.gradle...')
        with open(filename, 'w') as output_file:
            print("apply plugin: 'java'", file=output_file)
            print("apply plugin: 'eclipse'", file=output_file)
            print("apply plugin: 'idea'", file=output_file)
            print("group = 'com.bcs.gradle.test'", file=output_file)
            print("version = '1.0.0-SNAPSHOT'", file=output_file)
            print('', file=output_file)
            if len(dependencies) > 0:
                print('dependencies {', file=output_file)
                for dependency in dependencies:
                    print("    compile group: '{0}', name: '{1}', version: '{2}'".format(
                        dependency['groupId'],
                        dependency['artifactId'],
                        dependency['version'],
                    ), file=output_file)
                print('}', file=output_file)
            print('', file=output_file)
        logging.getLogger(__name__).info('gradle build.gradle generated')

    @staticmethod
    def generate_maven_config(dependencies, filename="pom.xml"):
        logging.getLogger(__name__).info('generating maven configuration...')
        with open(filename, 'w') as output_file:
            print('<?xml version="1.0" encoding="UTF-8"?>', file=output_file)
            print('<project xmlns="http://maven.apache.org/POM/4.0.0"', file=output_file)
            print('    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                  'xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 '
                  'http://maven.apache.org/xsd/maven-4.0.0.xsd">', file=output_file)
            print('    <modelVersion>4.0.0</modelVersion>', file=output_file)
            print('', file=output_file)
            print('   <groupId>com.bcs.mvn.test</groupId>', file=output_file)
            print('    <artifactId>mvn-sample</artifactId>', file=output_file)
            print('    <version>1.0-SNAPSHOT</version>', file=output_file)
            print('    <name>mvn-sample</name>', file=output_file)
            print('', file=output_file)
            if len(dependencies) > 0:
                print('    <dependencies>', file=output_file)
                for dependency in dependencies:
                    print('        <dependency>', file=output_file)
                    print('             <groupId>{0}</groupId>'.format(dependency['groupId']), file=output_file)
                    print('             <artifactId>{0}</artifactId>'.format(dependency['artifactId']),
                          file=output_file)
                    print('             <version>{0}</version>'.format(dependency['version']), file=output_file)
                    print('        </dependency>', file=output_file)
                print('    </dependencies>', file=output_file)
            print('</project>', file=output_file)
        logging.getLogger(__name__).info('maven configuration generated')

    @staticmethod
    def generate_ant_config(dependencies, filename="build.xml", nexus_url="http://nexus.mis.bcs:8081", version="2.1.3"):
        logging.getLogger(__name__).info('generating ant configuration...')
        with open(filename, 'w') as output_file:
            print('<?xml version="1.0" encoding="UTF-8"?>', file=output_file)
            print('<project name="ant-sample" default="download-dependencies" xmlns:artifact="urn:maven-artifact-ant">',
                  file=output_file)
            print('	<property name="maven.ant.tasks.jar.version" value="{0}" />'.format(version), file=output_file)
            print(
                '	<property name="maven.ant.tasks.jar" value="maven-ant-tasks-${maven.ant.tasks.jar.version}.jar" />',
                file=output_file)
            print('	<property name="maven.settings.file" value="${user.home}/.m2/settings.xml" />', file=output_file)
            print('	<target name="init-maven-task" depends="obtain-maven-task-jar">', file=output_file)
            print('		<available property="maven.ant.tasks.jar.exists" file="${maven.ant.tasks.jar}" />',
                  file=output_file)
            print(
                '		<typedef resource="org/apache/maven/artifact/ant/antlib.xml" uri="urn:maven-artifact-ant" classpath="${maven.ant.tasks.jar}" />',
                file=output_file)
            print('	</target>', file=output_file)
            print('	<target name="obtain-maven-task-jar">', file=output_file)
            print('		<available property="maven.ant.tasks.jar.exists" file="${maven.ant.tasks.jar}" />',
                  file=output_file)
            print('		<antcall target="download-maven-jar" />', file=output_file)
            print('	</target>', file=output_file)
            print('	<target name="download-maven-jar" unless="maven.ant.tasks.jar.exists">', file=output_file)
            url = nexus_url
            url += "/repository/maven-public/org/apache/maven/maven-ant-tasks/${maven.ant.tasks.jar.version}/${maven.ant.tasks.jar}"
            print('		<property name="maven.ant.tasks.url" value="{0}" />'.format(url), file=output_file)
            print('		<get src="${maven.ant.tasks.url}" dest="${maven.ant.tasks.jar}" />', file=output_file)
            print('	</target>', file=output_file)
            print('	<target name="download-dependencies" depends="init-maven-task">', file=output_file)
            print(
                '		<artifact:dependencies pathId="dependencies.classpath" settingsFile="${maven.settings.file}">',
                file=output_file)
            if len(dependencies) > 0:
                for dependency in dependencies:
                    print('			<dependency groupId="{0}" artifactId="{1}" version="{2}" />'.format(
                        dependency['groupId'],
                        dependency['artifactId'],
                        dependency['version']
                    ), file=output_file)
            print('		</artifact:dependencies>', file=output_file)
            print('		<move todir="libs">', file=output_file)
            print('			<path refid="dependencies.classpath" />', file=output_file)
            print('		</move>', file=output_file)
            print('	</target>', file=output_file)
            print('</project>', file=output_file)
        logging.getLogger(__name__).info('ant configuration generated')
