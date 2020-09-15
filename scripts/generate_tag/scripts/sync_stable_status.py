# -*- coding: utf-8 -*-
import argparse
import requests
import json
import random
import semver
import pprint

from datetime import datetime
from util import mars
from util.common import bump_version
from util.const import ALL_REPOS, BUMP_TYPES, config
from util.load_config import generate_repo_info_mapping
from util.github_api import get_branch_info
from util.ones_api import cached_data, create_task, login, \
    generate_task_uuid, peek_tasks, task_info, create_reference, \
    update_task, graph_ql


def get_updated_tasks(time_range):
    query = """
    query TASKS {
        tasks(filter:{
            project_in: ["%s"],
            issueType_in: ["%s", "%s", "%s", "%s"],
            serverUpdateStamp_range: %s
        }) {
            uuid
            name
            _%s {
                uuid
                value
            }
            _%s
        }
    }
    """ % (
        config["DEPLOY_APPLICATION_PROJECT_UUID"],
        config["DEPLOY_APPLICATION_ISSUE_TYPE_UUID"],
        config["API_ISSUE_TYPE_UUID"],
        config["WEB_ISSUE_TYPE_UUID"],
        config["TOOL_ISSUE_TYPE_UUID"],
        time_range,
        config["STABLE_FIELD_UUID"],
        config["VERSION_FIELD_UUID"]
    )
    tasks = graph_ql(query)
    return tasks


def get_unsure_tasks(time_range):
    query = """
    query TASKS {
        tasks(filter:{
            project_in: ["%s"],
            issueType_in: ["%s", "%s", "%s", "%s"],
            _AZ6F1szy_notIn: ["%s", "%s"],
            serverUpdateStamp_range: %s
        }) {
            uuid
            number
            name
            _%s {
                uuid
                value
            }
            _%s
        }
    }
    """ % (
        config["DEPLOY_APPLICATION_PROJECT_UUID"],
        config["DEPLOY_APPLICATION_ISSUE_TYPE_UUID"],
        config["API_ISSUE_TYPE_UUID"],
        config["WEB_ISSUE_TYPE_UUID"],
        config["TOOL_ISSUE_TYPE_UUID"],
        config["STABLE_OPTION_UUID"],
        config["UNSTABLE_OPTION_UUID"],
        time_range,
        config["STABLE_FIELD_UUID"],
        config["VERSION_FIELD_UUID"]
    )
    tasks = graph_ql(query)
    return tasks


# 同步不稳定状态到mars
def sync_stable_status():
    tasks = get_updated_tasks('{quick: "today"}')
    all_tasks = tasks["data"]["tasks"]
    if not all_tasks:
        print("未发现任务, 跳过...")
        return
    versions = mars.get_all_versions()

    stable_field = "_{}".format(config["STABLE_FIELD_UUID"])
    task_version_map = {}
    for v in versions:
        if not v or not v.get("extra_info") \
            or not v.get("extra_info").get("task_uuid"):
            continue
        task_uuid = v["extra_info"]["task_uuid"]
        task_version_map[task_uuid] = v

    versions_to_mark = {}
    for task in all_tasks:
        if not task or not task[stable_field]:
            continue
        v = task_version_map.get(task["uuid"])
        if not v:
            continue
        version_notsure = (v["stable"] == 1)
        version_stable = (v["stable"] == 2)
        task_stable = (task[stable_field]["uuid"] == config["STABLE_OPTION_UUID"])
        if version_notsure or task_stable != version_stable:
            versions_to_mark[v["key"]] = task_stable

    # 标记有变更的版本
    for key, value in versions_to_mark.items():
        if value:
            print("标记 {} 为稳定版本...".format(key))
            print(mars.mark_stable(key).decode("utf-8"))
        else:
            print("标记 {} 为不稳定版本...".format(key))
            print(mars.mark_unstable(key).decode("utf-8"))


# 自动设置3天内没有标记为稳定版的组件为稳定版本
def auto_set_stable_status():
    tasks = get_unsure_tasks('{lt: "last_3_days"}')
    pprint.pprint(tasks)
    all_tasks = tasks["data"]["tasks"]
    if not all_tasks:
        print("未发现3日内未标记的任务...")
        return all_tasks
    for task in all_tasks:
        print("标记任务 「#{} {}」为稳定版本".format(task["number"], task["name"]))
        update_task([{
            "uuid": task["uuid"],
            "field_values":[
                {"field_uuid": config["STABLE_FIELD_UUID"], "type":1, "value": config["STABLE_OPTION_UUID"]},
            ]
        }])
    return all_tasks

def main():
    login()
    sync_stable_status()
    if auto_set_stable_status():
        sync_stable_status()

if __name__ == "__main__":
    main()
