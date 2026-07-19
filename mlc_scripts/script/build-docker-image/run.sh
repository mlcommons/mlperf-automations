#!/bin/bash

if [ -f "${MLC_DOCKERFILE_WITH_PATH}" ]; then
#  echo ".git" > .dockerignore

#  echo ""
#  echo "docker build ${MLC_DOCKER_CACHE_ARG}  ${MLC_DOCKER_BUILD_ARGS} -f ${MLC_DOCKERFILE_WITH_PATH} -t ${MLC_DOCKER_IMAGE_REPO}/${MLC_DOCKER_IMAGE_NAME}:${MLC_DOCKER_IMAGE_TAG} ."

#  docker build ${MLC_DOCKER_CACHE_ARG}  ${MLC_DOCKER_BUILD_ARGS} -f "${MLC_DOCKERFILE_WITH_PATH}" -t "${MLC_DOCKER_IMAGE_REPO}/${MLC_DOCKER_IMAGE_NAME}:${MLC_DOCKER_IMAGE_TAG}" .

  eval "${MLC_DOCKER_BUILD_CMD}"
  test $? -eq 0 || exit 1

  echo ""
fi
