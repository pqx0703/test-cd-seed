
# -*- coding: utf-8 -*-
import semver

def bump_version(bump_type, version, tag="beta"):
    if bump_type == "prerelease":
        return semver.bump_prerelease(version, tag)

    bump_method_name = bump_type
    if bump_type.startswith("pre"):
        bump_method_name = bump_type[3:]
    bump_method = getattr(semver, "bump_%s" % bump_method_name)
    version = bump_method(version)
    if bump_type.startswith("pre"):
        version = semver.bump_prerelease(version, tag)
    return version
