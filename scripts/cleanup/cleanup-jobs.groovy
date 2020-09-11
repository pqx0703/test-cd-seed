// 多分支 pipeline 清理脚本。
// 清理一定时间（7 天）前的所有 build，如果清理后 job 已经没有任何 build，则清理 workspace。

import com.cloudbees.hudson.plugins.folder.AbstractFolder
import hudson.model.AbstractItem
import groovy.transform.Field

// 可以指定具体 job，也可以指定一个目录
def jobNames = [
    "development",
    "kubernetes-dev",
    "kubernetes-release"
]
def now = new Date()
def endTime = now.getTime() - 7 * 24 * 60 * 60 * 1000 // 7 days

for (jobName in jobNames) {
    removeBuilds(Jenkins.instance.getItemByFullName(jobName), endTime)
}

def removeBuilds(job, endTime) {
    if (job instanceof AbstractFolder) {
        for (subJob in job.getItems()) {
            removeBuilds(subJob, endTime)
        }
    } else if (job instanceof Job) {
        buildsDeleted = false
        workspaceDeleted = false
        job.getBuilds().byTimestamp(0, endTime).each {
            it.delete()
            buildsDeleted = true
        }
        if (job.getBuilds().isEmpty()) {
            Jenkins.instance.computers.each {
                if (it.online) {
                    deleteWorkspace(it.node, job)
                    workspaceDeleted = true
                }
            }
        }
        if (buildsDeleted || workspaceDeleted) {
            println "Job " + job.fullDisplayName + " cleaned successfully.\n"
        }
    } else {
        // do nothing
    }
}

def deleteWorkspace(node, job) {
    workspace = node.getWorkspaceFor(job)
    workspace.deleteContents()
    tempWorkspaces = workspace.parent.list { file ->
        file.name.startsWith(workspace.name)
    }
    for (tmp in tempWorkspaces) {
        tmp.deleteContents()
    }
}
