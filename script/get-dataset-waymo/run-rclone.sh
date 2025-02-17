cmd="rclone sync mlc-waymo:waymo_preprocessed_dataset/kitti_format ${MLC_DATASET_WAYMO_PATH} -P"
echo $cmd
eval $cmd
test $? -eq 0 || exit $?