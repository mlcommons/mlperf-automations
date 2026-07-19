#!/bin/bash
#${MLC_PYTHON_BIN_WITH_PATH} ${MLC_MLPERF_INFERENCE_VISION_PATH}/tools/retinanet_pytorch_to_onnx.py --weights ${MLC_ML_MODEL_FILE_WITH_PATH}
cmd="${MLC_PYTHON_BIN_WITH_PATH} ${MLC_MLPERF_TRAINING_SOURCE}/single_stage_detector/ssd/pth_to_onnx.py --num-classes 264 --image-size 800 800 --input ${MLC_ML_MODEL_FILE_WITH_PATH} --output retinanet_resnext50_32x4d_fpn.opset11.dyn_bs.800x800.onnx --device ${MLC_TORCH_DEVICE}"
echo $cmd
eval $cmd
test $? -eq 0 || exit $?
if [[ ${MLC_NVIDIA_EFFICIENT_NMS} == "yes" ]]; then
  cmd="bash ${MLC_TMP_CURRENT_SCRIPT_PATH}/polygraphy_script.sh retinanet_resnext50_32x4d_fpn.opset11.dyn_bs.800x800.onnx folded.onnx backend.onnx nms.onnx"
  echo $cmd
  eval $cmd
  test $? -eq 0 || exit $?
  cmd="${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/nvidia_patch_retinanet_efficientnms.py"
  echo $cmd
  eval $cmd
  test $? -eq 0 || exit $?
fi
