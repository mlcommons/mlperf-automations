cd ${MLC_HARNESS_CODE_ROOT}
if [ ! -e ILSVRC2012_img_val ]; then
  ln -s ${MLC_DATASET_IMAGENET_VAL_PATH} ILSVRC2012_img_val
fi

bash prepare_calibration_dataset.sh
cd -
