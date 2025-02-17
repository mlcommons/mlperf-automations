cmd="rclone sync mlc-waymo:waymo_preprocessed_dataset/model ${MLC_ML_MODEL_POINT_PAINTING_TMP_PATH} -P"
echo $cmd
eval $cmd
test $? -eq 0 || exit $?