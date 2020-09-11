## 工具使用说明
### 目录结构

+deploy_bot<br>
+----deploy<br>
----------deploy.sh: 通过 ci 自动部署代码至 ci 的制定文件夹<br>
+----scripts<br>
+--------util: 一些帮助方法<br>
-------------github_api.py: 操作 github 的 api 相关，包含 v3, v4 的数据<br>
-------------load_config.py: 加载配置文件的帮助方法<br>
-------------ones_api.py: 访问 ones_api.py 相关<br>
-------------request.py: 发送请求基础库相关<br>
-------------ones_api.py: 访问 ones_api.py 相关<br>
-------------scan_deploy_application.py: 扫描发布申请, 获取正常发布的版本信息和 changelog<br>
-------------scan_for_stable_deployment.py: 判断指定版本是否满足「稳定版本」的要求，并设置稳定版本的属性<br>
-------------scan_private_deploy.py: 获取需要填写 changlog 的实施申请<br>
-------------task_utils.py: 任务相关的帮助方法<br>
---------config.json: 配置文件，包含账号等<br>
---------create_deploy_task.py: 创建发布任务命令行工具<br>
---------generate_tag.py: 自动检测最高版本tag，创建tag等命令行工具<br>
---------scan_deploy_task.py: 扫描发布申请，生成版本信息。扫描实施申请，填写 changelog。有新版本发布时扫描 desk 任务，查看是否需要自动更新<br>
---------scan_for_stable_deployment.py: 扫描发布申请，确认稳定版本 <br>
----Jenkinsfile: 自动打 tag，创建发布申请相关内容

### 自动打tag

自动打 tag 的主要功能是获取到当前有多模块的产品的模块之间的最高版本，以保证在多模块的产品发布时的混乱情况。

同时，在后端有数据迁移的内容时，该脚本会扫描 migration 目录下是否存在目标文件夹，如果有该文件夹，则认为当前有数据迁移，如果该文件夹下有 upgrade.yaml，则把内容和迁移相关内容整合起来合并进 upgrade.yaml

例如：
```
bang-api v2.45.6
ones-project-web v2.46.0

get 的结果为 v2.46.0
create minor 版本的结果为创建 v2.47.0
create patch 版本的结果为创建 v2.46.1

```

总共分为3个命令，get，create，delete
```
usage: generate_tag.py [-h] {get,create,delete} ...

positional arguments:
  {get,create,delete}
    get                get highest tag for repos
    create             create tag for repos
    delete             delete tag for repos

optional arguments:
  -h, --help           show this help message and exit
```

__获取当前 web 和 api 库相关的最高版本 tag__
```
usage: generate_tag.py get [-h] --repositories
                           {bang-api,ones-project-web,wiki-api,wiki-web,ones.ai}
                           [{bang-api,ones-project-web,wiki-api,wiki-web,ones.ai} ...]
                           [--bump_type {patch,minor,major,prepatch,preminor,premajor,prerelease}]
                           [--semver_tag SEMVER_TAG]

optional arguments:
  -h, --help            show this help message and exit
  --repositories {bang-api,ones-project-web,wiki-api,wiki-web,ones.ai} [{bang-api,ones-project-web,wiki-api,wiki-web,ones.ai} ...]
                        Specify repositories.
  --bump_type {patch,minor,major,prepatch,preminor,premajor,prerelease}
                        Specify version type. default: patch
  --semver_tag SEMVER_TAG
                        semver tag for prerelease version. default: beta
```
__创建 tag__
```
usage: generate_tag.py create [-h] --repository
                              {bang-api,ones-project-web,wiki-api,wiki-web,ones.ai}
                              [--branch BRANCH] --tag TAG
                              [--migrations MIGRATIONS [MIGRATIONS ...]]

optional arguments:
  -h, --help            show this help message and exit
  --repository {bang-api,ones-project-web,wiki-api,wiki-web,ones.ai}
                        Specify repository.
  --branch BRANCH       branch to create tag
  --tag TAG             tag to process
  --migrations MIGRATIONS [MIGRATIONS ...]
                        Specify api migration folder.
```
__删除tag__
```
usage: generate_tag.py delete [-h] --repository
                              {bang-api,ones-project-web,wiki-api,wiki-web,ones.ai}
                              [--branch BRANCH] --tag TAG

optional arguments:
  -h, --help            show this help message and exit
  --repository {bang-api,ones-project-web,wiki-api,wiki-web,ones.ai}
                        Specify repository.
  --branch BRANCH       branch to create tag
  --tag TAG             tag to process
```



### 创建发布申请任务

创建发布申请任务会自动创建符合 [产品发布流程 2.3] (https://ones.ai/wiki/#/team/RDjYMhKq/space/DCBqNWkS/page/G6wxqiAi)的申请任务

命令行说明
```
usage: create_deploy_task.py [-h] --repo_tags REPO_TAGS [REPO_TAGS ...]
                             [--bump_type {patch,minor,major,prepatch,preminor,premajor,prerelease}]

optional arguments:
  -h, --help            show this help message and exit
  --repo_tags REPO_TAGS [REPO_TAGS ...]
                        tag for repositories,example: bang-api=v2.40.0
  --bump_type {patch,minor,major,prepatch,preminor,premajor,prerelease}
                        Specify version type. default: patch
```

### 扫描私有部署版本及更新desk任务

主要行为：
1. 扫描实施申请，找到需要处理的实施申请，并根据版本信息生成 changelog 填写，同时更新 KA 客户的实施时间
2. 扫描 desk 任务，找到 desk 任务关联的需求和 bug，如果关联的需求和 bug 已经上线，则更改状态

__命令行说明__
```
usage: scan_deploy_task.py [-h] --deploy_application_infos
                           DEPLOY_APPLICATION_INFOS [--email EMAIL]
                           [--password PASSWORD]

optional arguments:
  -h, --help            show this help message and exit
  --deploy_application_infos DEPLOY_APPLICATION_INFOS
                        File contains deploy application info of all versions
  --email EMAIL         ONES User email
  --password PASSWORD   ONES User password
```

### 扫描稳定版本

主要行为：
* 找到满足三天稳定期条件的发布申请，并设置该版本为稳定版本

直接运行即可，无需说明