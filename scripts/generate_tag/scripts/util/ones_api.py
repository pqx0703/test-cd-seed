# -*- coding: utf-8 -*-
import os
import random
import requests

from util.const import config
from .request import call_ones_api

cached_data = {}
ROOT_UUID = "__root__"


def generate_uuid(prefix=""):
    length = 8
    has_number = True
    has_uppercase = True
    has_lowercase = True
    seed = []
    if has_number:
        seed.append("0123456789")
    if has_uppercase:
        seed.append("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if has_lowercase:
        seed.append("abcdefghijklmnopqrstuvwxyz")

    seed_str = "".join(seed)
    salt = []
    for _ in range(length):
        salt.append(random.choice(seed_str))
    return prefix + ''.join(salt)


def generate_task_uuid():
    return generate_uuid(cached_data["user_uuid"])


def call_authed_ones_api(url, method, product, data=None):
    if cached_data["token"] is None or cached_data["user_uuid"] is None:
        raise Exception("token or user_uuid is not found,should login first!!")
    headers = {
        "Ones-Auth-Token": cached_data["token"],
        "Ones-User-Id": cached_data["user_uuid"]
    }
    return call_ones_api(url, method, product, data, headers)


def call_authed_team_ones_api(url, method, product, data=None, url_params={}):
    url = url.format(team_uuid=config["TEAM_UUID"], **url_params)
    return call_authed_ones_api(url, method, product, data)


def login(email=None, password=None):
    if email is None:
        email = config["EMAIL"]
    if password is None:
        password = config["PASSWORD"]

    result = call_ones_api("/auth/login", "post", "project", {
        "email": email,
        "password": password
    })
    cached_data["token"] = result["user"]["token"]
    cached_data["user_uuid"] = result["user"]["uuid"]


def create_task(tasks):
    result = call_authed_team_ones_api(
        "/team/{team_uuid}/tasks/add2", "post", "project", {"tasks": tasks})

    if result["bad_tasks"]:
        bad_task = result["bad_tasks"][0]
        raise Exception("Add task %s failed,reason is: %s" %
                        (bad_task["uuid"], bad_task["errcode"]))
    return result["tasks"]


def peek_tasks(query, sort, include_subtasks):
    data = {
        "with_boards": False,
        "boards": None,
        "query": query,
        "group_by": "",
        "sort": sort,
        "include_subtasks": include_subtasks,
        "include_status_uuid": False,
        "include_issue_type": False,
        "include_project_uuid": False,
        "is_show_derive": False
    }
    result = call_authed_team_ones_api(
        "/team/{team_uuid}/filters/peek", "post", "project", data)
    return result


def task_info(task_uuid):
    result = call_authed_team_ones_api(
        "/team/{team_uuid}/task/"+task_uuid+"/info", "get", "project")
    return result


def create_reference(task_uuid, ref_task_uuids, ref_uuid):
    data = {
        "task_uuids": ref_task_uuids,
        "task_link_type_uuid": ref_uuid,
        "link_desc_type": "link_out_desc"
    }
    result = call_authed_team_ones_api(
        "/team/{team_uuid}/task/"+task_uuid+"/related_tasks", "post", "project", data)
    return result


def update_task(tasks):
    """ tasks格式
        [{
            "uuid":"FXWjFL8RryicBCNz",
            "field_values":[
                {"field_uuid":"LPKEfKhk","type":2,"value":1},
                {"field_uuid":"x82sadCV","type":1,"value":"..."}
            ]
        }]
    """
    data = {"tasks": tasks}
    result = call_authed_team_ones_api(
        "/team/{team_uuid}/tasks/update3", "post", "project", data)
    return result


def graph_ql(query):
    data = {"query": query}
    result = call_authed_team_ones_api(
        "/team/{team_uuid}/items/graphql", "post", "project", data)
    return result
