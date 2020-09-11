#!/bin/bash
set -e

FOLDER="generate_tag"

SCRIPTS_FOLDER="${JENKINS_HOME}/scripts/$FOLDER"


install_dependencies(){
  echo "pip install -r ./${FOLDER}/scripts/requirements.txt --user"
  pip install -r ./${FOLDER}/scripts/requirements.txt --user
}

deploy_script(){
  echo "[ -e $SCRIPTS_FOLDER ] && rm -rf $SCRIPTS_FOLDER"
  [ -e $SCRIPTS_FOLDER ] && rm -rf $SCRIPTS_FOLDER
  echo "mkdir $SCRIPTS_FOLDER"
  mkdir $SCRIPTS_FOLDER
  echo "cp -r ${WORKSPACE}/${FOLDER}/scripts/* ${SCRIPTS_FOLDER}"
  cp -r ${WORKSPACE}/${FOLDER}/scripts/* ${SCRIPTS_FOLDER}
}

modify_config_by_jenkins_variables(){
  echo "Starting replace config by jenkins variables..."
  sed -i '/"GITHUB_TOKEN"/ s#:.*#: "'${GITHUB_TOKEN}'",#' ${WORKSPACE}/${FOLDER}/scripts/release_config.json
  sed -i '/"EMAIL"/ s#:.*#: "'${USER_EMAIL}'",#' ${WORKSPACE}/${FOLDER}/scripts/release_config.json
  sed -i '/"PASSWORD"/ s#:.*#: "'${USER_PASSWORD}'",#' ${WORKSPACE}/${FOLDER}/scripts/release_config.json
  echo "Finished replace config by jenkins variables..."
}

install_dependencies
modify_config_by_jenkins_variables
deploy_script
