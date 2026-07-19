echo ${JAVA_HOME}
echo ${MLC_ANDROID_SDK_MANAGER_BIN_WITH_PATH}

${MLC_ANDROID_SDK_MANAGER_BIN_WITH_PATH} --version > tmp-ver.out
cat tmp-ver.out

${MLC_ANDROID_SDK_MANAGER_BIN_WITH_PATH} --licenses
test $? -eq 0 || exit 1

${MLC_ANDROID_SDK_MANAGER_BIN_WITH_PATH} \
    "tools" \
    "platform-tools" \
    "extras;android;m2repository" \
    "extras;google;m2repository" \
    "extras;google;google_play_services" \
    "build-tools;${MLC_ANDROID_BUILD_TOOLS_VERSION}"
test $? -eq 0 || exit 1

${MLC_ANDROID_SDK_MANAGER_BIN_WITH_PATH} "platforms;android-${MLC_ANDROID_VERSION}"
test $? -eq 0 || exit 1

${MLC_ANDROID_SDK_MANAGER_BIN_WITH_PATH} "cmake;${MLC_ANDROID_CMAKE_VERSION}"
test $? -eq 0 || exit 1

${MLC_ANDROID_SDK_MANAGER_BIN_WITH_PATH} "ndk;${MLC_ANDROID_NDK_VERSION}"
test $? -eq 0 || exit 1
