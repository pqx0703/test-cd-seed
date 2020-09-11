# -*- coding: utf-8 -*-#

import os
import base64

from util.const import config
from .request import call_github_api_v4, call_github_api


def get_branch_info(repo, tag):
    owner_name = config["ORG_NAME"]

    result = call_github_api_v4("""
    query TagInfo($repo: String!, $owner: String!, $tag: String!){
        repository(owner: $owner,name: $repo){
            object(expression: $tag){
                ... on Commit{
                    oid
                    history {
                        totalCount
                    }
                }
            }
        }
    }
    """, {"repo": repo, "tag": tag, "owner": owner_name})
    tag = result["repository"]["object"]
    commit = tag["oid"]
    commit_times = tag["history"]["totalCount"]

    return commit, commit_times


def create_new_tag(repository, tag, commit):
    message = "{} {} has released!".format(repository, tag)
    data = {
        "tag": tag,
        "message": message,
        "object": commit,
        "type": "commit",
        "tagger": {
            "name": "ci",
            "email": "ci.ones.ai"
        }
    }
    create_tag_url = "/repos/{}/{}/git/tags".format(
        config["ORG_NAME"], repository)
    call_github_api(create_tag_url, "post", data)


def create_tag_reference(repository, tag, commit):
    data = {
        "ref": "refs/tags/%s" % tag,
        "sha": commit
    }
    create_ref_url = "/repos/{}/{}/git/refs".format(
        config["ORG_NAME"], repository)
    call_github_api(create_ref_url, "post", data)


def delete_tag_reference(repository, tag):
    delete_ref_url = "/repos/{}/{}/git/refs/tags/{}".format(
        config["ORG_NAME"], repository, tag)
    call_github_api(delete_ref_url, "delete")


def get_branch_commit(repository, branch):
    get_branch_url = "/repos/{}/{}/branches/{}".format(
        config["ORG_NAME"], repository, branch)
    branch = call_github_api(get_branch_url, "get")
    last_commit = branch["commit"]["sha"]
    return last_commit


def get_tags(repository):
    url = "/repos/{}/{}/git/refs/tags".format(config["ORG_NAME"], repository)
    return call_github_api(url, "get")


def get_contents(repository, branch, path):
    url = "/repos/{}/{}/contents/{}".format(
        config["ORG_NAME"], repository, path)
    result = call_github_api(url, "get", {"ref": branch})
    file_content = result["content"]
    return base64.b64decode(file_content), result["sha"]


def get_files(repository, branch, path):
    url = "/repos/{}/{}/contents/{}".format(
        config["ORG_NAME"], repository, path)
    result = call_github_api(url, "get", {"ref": branch})
    return result


def update_contents(repository, branch, path, params):
    print(params["content"])
    params["content"] = base64.b64encode(bytes(params["content"], encoding = "utf8")).decode("ascii")

    url = "/repos/{}/{}/contents/{}".format(
        config["ORG_NAME"], repository, path)

    return call_github_api(url, "put", params)
