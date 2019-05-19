# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2019 Matthias Klumpp <matthias@tenstral.net>
#
# Licensed under the GNU Lesser General Public License Version 3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the license, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

import math
import humanize
from flask import current_app, Blueprint, render_template, abort
from laniakea.db import session_scope, BinaryPackage, SourcePackage, \
    Job, JobStatus, JobResult, SparkWorker
from laniakea.utils import get_dir_shorthand_for_uuid
from ..utils import humanized_timediff, is_uuid

packages = Blueprint('packages',
                     __name__,
                     url_prefix='/package')


@packages.route('/bin/<name>/<version>')
def bin_package_details(name, version):
    with session_scope() as session:
        bpkgs = session.query(BinaryPackage) \
            .filter(BinaryPackage.name == name) \
            .order_by(BinaryPackage.version.desc()) \
            .all()
        if not bpkgs:
            abort(404)

        # TODO: Doing this in Python is probably inefficient, we could also
        # directly fetch the informatuion with some SQL to improve performance
        suites = set()
        architectures = set()
        versions = set()
        bpkg_rep = None
        for bpkg in bpkgs:
            suites.update(bpkg.suites)
            architectures.add(bpkg.architecture)
            versions.add(bpkg.version)
            if bpkg.version == version:
                bpkg_rep = bpkg
        if not bpkg_rep:
            abort(404)

        return render_template('packages/bin_details.html',
                               pkg=bpkg_rep,
                               versions=versions,
                               suites=suites,
                               architectures=architectures,
                               naturalsize=humanize.naturalsize)


@packages.route('/src/<name>/<version>')
def src_package_details(name, version):
    with session_scope() as session:
        spkgs = session.query(SourcePackage) \
            .filter(SourcePackage.name == name) \
            .order_by(SourcePackage.version.desc()) \
            .all()
        if not spkgs:
            abort(404)

        # TODO: Doing this in Python is probably inefficient, we could also
        # directly fetch the informatuion with some SQL to improve performance
        suites = set()
        versions = set()
        spkg_rep = None
        for spkg in spkgs:
            suites.update(spkg.suites)
            versions.add(spkg.version)
            if spkg.version == version:
                spkg_rep = spkg
        if not spkg_rep:
            abort(404)

        return render_template('packages/src_details.html',
                               pkg=spkg_rep,
                               versions=versions,
                               suites=suites)


@packages.route('/builds/<name>/<int:page>')
def builds_list(name, page):
    with session_scope() as session:
        spkg = session.query(SourcePackage) \
            .filter(SourcePackage.name == name) \
            .order_by(SourcePackage.version.desc()) \
            .first()
        if not spkg:
            abort(404)

        jobs_per_page = 20
        jobs_total = session.query(Job) \
            .filter(Job.trigger == spkg.source_uuid) \
            .order_by(Job.time_created.desc()) \
            .count()
        page_count = math.ceil(jobs_total / jobs_per_page)

        jobs = session.query(Job) \
            .filter(Job.trigger == spkg.source_uuid) \
            .order_by(Job.time_created.desc()) \
            .slice((page - 1) * jobs_per_page, page * jobs_per_page) \
            .all()

        return render_template('packages/builds_list.html',
                               JobStatus=JobStatus,
                               humanized_timediff=humanized_timediff,
                               pkg=spkg,
                               jobs=jobs,
                               jobs_per_page=jobs_per_page,
                               jobs_total=jobs_total,
                               current_page=page,
                               page_count=page_count)


@packages.route('/builds/job/<uuid>')
def build_details(uuid):
    if not is_uuid(uuid):
        abort(404)

    with session_scope() as session:
        job = session.query(Job).filter(Job.uuid == uuid).one_or_none()
        if not job:
            abort(404)

        worker = session.query(SparkWorker).filter(SparkWorker.uuid == job.worker).one_or_none()

        log_url = None
        if job.result == JobResult.SUCCESS or job.result == JobResult.FAILURE:
            log_url = current_app.config['LOG_STORAGE_URL'] + '/' + get_dir_shorthand_for_uuid(job.uuid) + '/' + str(job.uuid) + '.log'

        spkg = session.query(SourcePackage) \
            .filter(SourcePackage.source_uuid == job.trigger) \
            .filter(SourcePackage.version == job.version) \
            .one_or_none()
        if not spkg:
            abort(404)

        suite_name = 'unknown'
        if job.data:
            suite_name = job.data.get('suite')

        return render_template('packages/build_details.html',
                               humanized_timediff=humanized_timediff,
                               JobStatus=JobStatus,
                               JobResult=JobResult,
                               job=job,
                               worker=worker,
                               spkg=spkg,
                               suite_name=suite_name,
                               log_url=log_url)