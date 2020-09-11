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


pp = pprint.PrettyPrinter(indent=1)
def chunks(l, n): return [l[x: x+n] for x in range(0, len(l), n)]


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo_tags",
        help="tag for repositories,example: bang-api=v2.40.0",
        nargs="+",
        required=True
    )
    parser.add_argument(
        "--bump_type",
        help="Specify version type. default: patch",
        default="patch",
        choices=BUMP_TYPES
    )
    return parser.parse_args()


def generate_parent_task(tag, bump_type):
    """生成父工作项"""
    product_text = "ONES"
    summary = "{} {}".format(product_text, tag)
    print("Generating deploy application parent task data, product: {},tag: {}".format(
        product_text, tag))

    field_values = [
        # tag版本
        {
            "field_uuid": config["VERSION_FIELD_UUID"],
            "value": tag
        },
        # 版本类型
        {
            "field_uuid": config["BUMP_TYPE_FIELD_UUID"],
            "value": get_option_uuid(bump_type)
        }
    ]
    task = {
        "uuid": generate_task_uuid(),
        "summary": summary,
        "assign": cached_data["user_uuid"],
        "owner": cached_data["user_uuid"],
        "issue_type_uuid": config["DEPLOY_APPLICATION_ISSUE_TYPE_UUID"],
        "project_uuid": config["DEPLOY_APPLICATION_PROJECT_UUID"],
        "parent_uuid": "",
        "field_values": field_values
    }

    return task


def generate_sub_task(parent_uuid, repo, tag):
    """生成子工作项"""
    print("Generating deploy application subtask data, repo: {}, tag: {}".format(repo, tag))
    repo_info = config["REPO_MAP"][repo]
    repo_type = repo_info["type"]
    module_text = repo_info["text"]
    (commit, commit_times) = get_branch_info(repo, tag)
    issue_type = config["%s_ISSUE_TYPE_UUID" % repo_type]
    summary = "{} {}".format(module_text, tag)

    field_values = [
        # tag版本
        {
            "field_uuid": config["VERSION_FIELD_UUID"],
            "value": tag
        },
        # commit号
        {
            "field_uuid": config["COMMIT_FIELD_UUID"],
            "value": commit
        },
        # build号(最后提交时间戳)
        {
            "field_uuid": config["BUILD_FIELD_UUID"],
            "value": str(commit_times)
        }
    ]
    task = {
        "uuid": generate_task_uuid(),
        "summary": summary,
        "assign": cached_data["user_uuid"],
        "owner": cached_data["user_uuid"],
        "issue_type_uuid": issue_type,
        "sub_issue_type_uuid": issue_type,
        "project_uuid": config["DEPLOY_APPLICATION_PROJECT_UUID"],
        "parent_uuid": parent_uuid,
        "field_values": field_values
    }

    return task


def get_option_uuid(bump_type):
    if bump_type == "patch":
        return config["PATCH_OPTION_UUID"]
    return config["MINOR_OPTION_UUID"]


def parse_task_summary(summary):
    repo_name = None
    version_tag = None
    for repo, info in config["REPO_MAP"].items():
        pp.pprint(repo)
        pp.pprint(info)
        pp.pprint(summary)
        if summary.startswith(info["text"]):
            repo_name = repo
            version_tag = str(summary.strip(info["text"])).strip()
    return repo_name, version_tag


def generate_task(options):
    sub_com_ref_uuid = config["SUB_COM_REFERENCE_UUID"]
    repo_tag_mapping = {
        arr[0]: arr[1]
        for arr in [s.split("=") for s in options.repo_tags]
    }

    # 获取 ones 的最高版本
    highest_version = mars.get_highest_ones_version()
    max_ver = highest_version["tag"].replace("v", "")
    version = bump_version(options.bump_type, max_ver)
    ones_tag = "v{}".format(version)
    print("ones highest version: %s -> %s" % (max_ver, version))

    # 获取 ones 当前版本
    current_version = mars.get_current_version()
    print("ones current version: ", current_version)

    # 生成任务
    parent_task = generate_parent_task(ones_tag, options.bump_type)
    sub_tasks = {
        repo: generate_sub_task(parent_task["uuid"], repo, tag)
        for repo, tag in repo_tag_mapping.items()
    }
    tasks = [parent_task] + list(sub_tasks.values())

    # 创建 mars 新版本
    changed = {}
    new_sub_components = []
    exist_sub_components = []
    team_uuid = config["TEAM_UUID"]
    create_time = int(datetime.utcnow().timestamp())
    mars_versions = []
    for repo, task in sub_tasks.items():
        repo_tag = repo_tag_mapping[repo]
        version_key = "{}@{}".format(repo, repo_tag)
        new_sub_components.append(version_key)
        old_coms = [
            com_tag for com_tag in current_version["sub_components"] 
            if com_tag.startswith(repo)
        ]
        if len(old_coms) > 0:
            changed[version_key] = old_coms[0]
        else:
            changed[version_key] = ""
        commit = ""
        for f in task["field_values"]:
            if f["field_uuid"] == config["COMMIT_FIELD_UUID"]:
                commit = f["value"]
                break
        mars_versions.append({
            "key": version_key,
            "repo": repo,
            "tag": repo_tag,
            "create_time": create_time,
            "sub_components": [],
            "stable": 1,
            "changed": {},
            "commit": commit,
            "migrations": [],
            "previous_version": "",
            "semver_tag": "",
            "bump_type": options.bump_type,
            "extra_info": {
                "task_uuid": task["uuid"],
                "project_uuid": task["project_uuid"],
                "team_uuid": team_uuid
            }
        })
    for com_tag in current_version["sub_components"]:
        repo = com_tag.split("@")[0]
        if repo in repo_tag_mapping:
            continue
        exist_sub_components.append(com_tag)
    mars_versions.append({
        "key": "ones@{}".format(ones_tag),
        "repo": "ones",
        "tag": ones_tag,
        "create_time": create_time,
        "sub_components": new_sub_components + exist_sub_components,
        "stable": 1,
        "changed": changed,
        "commit": "",
        "migrations": [],
        "previous_version": "",
        "semver_tag": "",
        "bump_type": options.bump_type,
        "extra_info": {
            "task_uuid": parent_task["uuid"],
            "project_uuid": parent_task["project_uuid"],
            "team_uuid": team_uuid
        }
    })
    mars.add_versions(mars_versions)

    exist_version_map = {}
    for key in exist_sub_components:
        try:
            exist_version_map[key] = mars.get_version(key)
        except:
            print("waring: {} not found".format(key))
            pass

    # 创建工作项, 大于10个时，要分批创建, 否则会报错
    if tasks:
        print("Sending data to ones api server...")
        for chunk in chunks(tasks, 10):
            create_task(chunk)
        print("Finished create deploy application task...")

    # 设置关联
    ref_task_uuids = [s["uuid"] for s in sub_tasks.values()]
    ref_task_uuids = ref_task_uuids + [
        v["extra_info"]['task_uuid'] 
        for _, v in exist_version_map.items() 
        if v["extra_info"] and v["extra_info"]['task_uuid']
    ]
    create_reference(parent_task["uuid"], ref_task_uuids, sub_com_ref_uuid)

    # 设置当前版本
    mars.set_current_version("ones@{}".format(ones_tag))


if __name__ == "__main__":
    options = parse_options()
    login()
    generate_task(options)
