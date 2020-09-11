# -*- coding: utf-8 -*-
import subprocess
import re
import semver
import argparse
import requests
import json
import os
import yaml

from functools import cmp_to_key
from util.const import ALL_REPOS, BUMP_TYPES, config
from util.common import bump_version
from util.load_config import generate_repo_info_mapping
from util.github_api import get_tags, get_branch_commit, create_new_tag, create_tag_reference, delete_tag_reference, get_contents, get_files, update_contents


def parse_options():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="action")

    get_parser = subparsers.add_parser("get", help="get highest tag for repos")

    create_parser = subparsers.add_parser(
        "create", help="create tag for repos")
    delete_parser = subparsers.add_parser(
        "delete", help="delete tag for repos")

    for subparser in (create_parser, delete_parser):
        subparser.add_argument(
            "--repository", help="Specify repository.", required=True, choices=ALL_REPOS
        )
        subparser.add_argument(
            "--branch", help="branch to create tag", default="master"
        )
        subparser.add_argument(
            "--tag", help="tag to process", required=True
        )

    create_parser.add_argument(
        "--migrations", help="Specify api migration folder.", nargs="+"
    )
    create_parser.add_argument(
        "--migration_type", help="migration type, old or new. default: old", default="old"
    )

    get_parser.add_argument(
        "--repositories", help="Specify repositories.",  nargs='+', required=True, choices=ALL_REPOS
    )

    get_parser.add_argument(
        "--bump_type", help="Specify version type. default: patch", default="patch", choices=BUMP_TYPES
    )
    get_parser.add_argument(
        "--semver_tag", help="semver tag for prerelease version. default: beta", default="beta"
    )
    get_parser.add_argument(
        "--token", help="tag. default: null", default="null"
    )
    return parser.parse_args()


def get_product_highest_tags(repo):
    return get_remote_highest_tags(repo)


def get_remote_highest_tags(repository):
    tag_infos = get_tags(repository)

    tags = []
    for tag_info in tag_infos:
        matchobj = re.match(
            r"^refs/tags/(v)?((\d+\.\d+\.\d+).*)$", tag_info["ref"])
        if matchobj is not None:
            version = matchobj.group(2)
            try:
                semver.parse(str(version))
            except ValueError:
                pass
            else:
                tags.append(str(version))

    tags.sort(key=cmp_to_key(semver.compare), reverse=True)
    return tags[0]


def get_yaml_content(repository, branch, path):
    print(path)
    file_content, sha = get_contents(repository, branch, path)
    result = yaml.load(file_content, Loader=yaml.SafeLoader)
    return result, sha


def compare_upgrade(new, old):
    if new is None and old is None:
        return True

    if new is None or old is None:
        return False
    new_keys = new.keys()
    old_keys = old.keys()

    if len(new_keys) != len(old_keys):
        return False

    for key in new_keys:
        if key not in old:
            return False
        if new[key] != old[key]:
            return False

    return True


def is_new_migration_type(migration_type):
    return migration_type == "new"


def update_upgrade_file(repository, branch, tag, migration_folders, migration_type):
    files = get_files(repository, branch, "migration")
    all_upgrade, file_sha = get_yaml_content(
        repository, branch, "migration/upgrade.yaml")

    folders = set(migration_folders)

    upgrade_version = semver.finalize_version(tag[1:])

    old_upgrade = None

    for index, upgrade in enumerate(all_upgrade["versions"]):
        if upgrade["version"] == upgrade_version:
            old_upgrade = all_upgrade["versions"].pop(index)
            break

    found = False
    new_upgrade = {
        "version": upgrade_version,
        "features": [],
        "config_params": []
    }

    for file in files:
        if file["type"] != "dir":
            continue
        name = file["name"]
        if name in folders:
            found = True
            feature = {"name": str(name), "run_command_params": {
            }, "migration_type": migration_type}
            try:
                migration, _ = get_yaml_content(
                    repository, branch, "migration/{}/upgrade.yaml".format(name))
            except requests.exceptions.HTTPError as e:
                response = e.response
                if response.status_code == 404:
                    print("No upgrade.yaml found under migration folder!!!!")
                    print("Automatically create features with name!!!!!!")
                else:
                    raise e
            else:
                if "run_command_params" in migration:
                    feature.update({
                        "run_command_params": migration["run_command_params"]
                    })

                if "config_params" in migration:
                    new_upgrade["config_params"].extend(
                        migration['config_params'])

            new_upgrade["features"].append(feature)

    # new migration type will still generate migration info if migration folder not found
    if not found and is_new_migration_type(migration_type):
        for migration_name in folders:
            feature = {"name": migration_name, "run_command_params": {
            }, "migration_type": migration_type}
            new_upgrade["features"].append(feature)

    if found or is_new_migration_type(migration_type):
        print("current upgrade: {}, old upgrade: {}".format(
            new_upgrade, old_upgrade))
        if not compare_upgrade(new_upgrade, old_upgrade):
            print("Start updating upgrade.yaml...")
            all_upgrade["versions"].append(new_upgrade)
            file_result = yaml.dump(
                all_upgrade, allow_unicode=True, default_flow_style=False)

            params = {
                "content": file_result,
                "message": "other: Update upgrade.yaml to version %s by CI Bot" % upgrade_version,
                "branch": branch,
                "committer": {
                    "name": "CI Bot",
                    "email": "ci@ones.ai"
                },
                "sha": file_sha
            }

            result = update_contents(
                repository, branch, "migration/upgrade.yaml", params)
            print("finished updating upgrade.yaml...")
            return result
        else:
            print("Upgrade did not change, ")
    else:
        print("No migration folder found!!!")

    return

# command method


def delete(options):
    repo_list = options.repositories
    for repo in repo_list:
        print("Start deleting tag {} for {} ...".format(options.tag, repo))
        delete_tag_reference(repo, options.tag)
        print("Finished deleting tag {} for {}...".format(options.tag, repo))


def get_highest_tags(options):
    output_strs = []
    for repo in options.repositories:
        highest_tag = get_product_highest_tags(repo)
        version = bump_version(
            options.bump_type, highest_tag, options.semver_tag)
        output_strs.append("{}=v{}".format(repo, version))
    return " ".join(output_strs)


def create(options):
    info_mapping = generate_repo_info_mapping(config)
    tag = options.tag
    repo = options.repository
    print("Start creating tag {} for repo {}...".format(tag, repo))
    commit = get_branch_commit(repo, options.branch)

    print("Get branch commit: {}".format(commit))
    if options.migrations and repo in info_mapping and info_mapping[repo]["type"] == "API":
        update_result = update_upgrade_file(
            repo, options.branch, tag, options.migrations, options.migration_type)
        if update_result:
            commit = update_result["commit"]["sha"]
            print("Update upgrade.yaml success!! commit: {}".format(commit))
    create_new_tag(repo, tag, commit)
    create_tag_reference(repo, tag, commit)
    print("Finished creating tag {} for repo {}...".format(tag, repo))


if __name__ == "__main__":
    options = parse_options()
    if options.action == "get":
        output_str = get_highest_tags(options)
        print(output_str)
    elif options.action == "delete":
        delete(options)
    elif options.action == "create":
        create(options)
