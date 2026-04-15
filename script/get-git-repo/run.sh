CUR_DIR=$PWD
echo "$CUR_DIR"
SCRIPT_DIR=${MLC_TMP_CURRENT_SCRIPT_PATH}
ENV_OUT_FILE="$CUR_DIR/tmp-run-env.out"

folder=${MLC_GIT_CHECKOUT_FOLDER}
if [ ! -e "${MLC_TMP_GIT_PATH}" ]; then
  cmd="rm -rf ${folder}"
  echo $cmd
  eval $cmd
  echo "******************************************************"
  echo "Current directory: ${CUR_DIR}"
  echo ""
  echo "Cloning ${MLC_GIT_REPO_NAME} from ${MLC_GIT_URL}"
  echo ""
  echo "${MLC_GIT_CLONE_CMD}";
  echo ""

  ${MLC_GIT_CLONE_CMD}
  rcode=$?

  if [ ! $rcode -eq 0 ]; then #try once more
    rm -rf $folder
    ${MLC_GIT_CLONE_CMD}
    test $? -eq 0 || exit $?
  fi

  cd ${folder}

  if [ ! -z ${MLC_GIT_SHA} ]; then

    echo ""
    cmd="git checkout -b ${MLC_GIT_SHA} ${MLC_GIT_SHA}"
    echo "$cmd"
    eval "$cmd"
    test $? -eq 0 || exit $?

  elif [ ! -z ${MLC_GIT_CHECKOUT_TAG} ]; then

    echo ""
    cmd="git fetch --all --tags"
    echo "$cmd"
    eval "$cmd"
    cmd="git checkout tags/${MLC_GIT_CHECKOUT_TAG} -b ${MLC_GIT_CHECKOUT_TAG}"
    echo "$cmd"
    eval "$cmd"
    test $? -eq 0 || exit $?

  fi
  # Note: The `else` block outputting to `../tmp-mlc-git-hash.out` has been removed.
  # The hash is now captured dynamically below.

else
  cd ${folder}
fi

# ---------------------------------------------------------
# Capture Checkout & SHA information
# ---------------------------------------------------------
# Determine the active branch name (or fallback to detached HEAD hash)
ACTUAL_CHECKOUT=$(git rev-parse --abbrev-ref HEAD)
if [ "$ACTUAL_CHECKOUT" == "HEAD" ]; then
  ACTUAL_CHECKOUT=$(git rev-parse HEAD)
fi

CURRENT_SHA=$(git rev-parse HEAD)

echo "MLC_GIT_CHECKOUT=${ACTUAL_CHECKOUT}" >> "$ENV_OUT_FILE"
echo "MLC_GIT_SHA=${CURRENT_SHA}" >> "$ENV_OUT_FILE"

# ---------------------------------------------------------
# Apply PR, Cherry-picks, and Patches
# ---------------------------------------------------------
if [ ! -z ${MLC_GIT_PR_TO_APPLY} ]; then
  echo ""
  echo "Fetching from ${MLC_GIT_PR_TO_APPLY}"
  git fetch origin ${MLC_GIT_PR_TO_APPLY}:tmp-apply
  
  # Log the PR applied
  echo "MLC_GIT_APPLIED_PR=${MLC_GIT_PR_TO_APPLY}" >> "$ENV_OUT_FILE"
fi

if [ ! -z "${MLC_GIT_CHERRYPICKS}" ]; then
  # Log the cherry-picks applied
  echo "MLC_GIT_APPLIED_CHERRYPICKS=${MLC_GIT_CHERRYPICKS}" >> "$ENV_OUT_FILE"
  
  IFS=';' read -r -a cherrypicks <<< "${MLC_GIT_CHERRYPICKS}"
  for cherrypick in "${cherrypicks[@]}"
  do
    echo ""
    echo "Applying cherrypick $cherrypick"
    git cherry-pick -n $cherrypick
    test $? -eq 0 || exit $?
  done
fi

if [ ! -z "${MLC_GIT_SUBMODULES}" ]; then
  IFS=';' read -r -a submodules <<< "${MLC_GIT_SUBMODULES}"
  for submodule in "${submodules[@]}"
  do
      echo ""
      echo "Initializing submodule ${submodule}"
      git submodule update --init --recursive --checkout --force "${submodule}"
      test $? -eq 0 || exit $?
  done
fi

if [ "${MLC_GIT_PATCH}" == "yes" ]; then
  # Log the patches applied
  echo "MLC_GIT_APPLIED_PATCHES=${MLC_GIT_PATCH_FILEPATHS}" >> "$ENV_OUT_FILE"
  
  IFS=';' read -r -a patch_files <<< "${MLC_GIT_PATCH_FILEPATHS}"
  for patch_file in "${patch_files[@]}"
  do
    echo ""
    echo "Applying patch $patch_file"
    git apply "$patch_file"
    test $? -eq 0 || exit $?
  done
fi

cd "$CUR_DIR"
