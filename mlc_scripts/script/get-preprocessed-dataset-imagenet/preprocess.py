import os
import sys

if os.environ.get('MLC_DATASET_REFERENCE_PREPROCESSOR', '1') == "0":
    import generic_preprocess
    generic_preprocess.preprocess()
else:
    mlperf_src_path = os.environ['MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH']
    python_path = os.path.join(mlperf_src_path, "python")
    sys.path.insert(0, python_path)

    import imagenet
    import dataset

    dataset_path = os.environ['MLC_DATASET_PATH']
    dataset_list = os.environ.get('MLC_DATASET_IMAGES_LIST', None)
    img_format = os.environ.get('MLC_DATASET_DATA_LAYOUT', 'NHWC')
    count = int(os.environ.get('MLC_DATASET_SIZE', 1))
    preprocessed_dir = os.environ.get(
        'MLC_DATASET_PREPROCESSED_PATH', os.getcwd())
    threads = os.environ.get('MLC_NUM_THREADS', os.cpu_count())
    threads = int(os.environ.get('MLC_NUM_PREPROCESS_THREADS', threads))

    if os.environ.get('MLC_MODEL') == 'mobilenet':
        pre_process = dataset.pre_process_mobilenet
    elif os.environ.get('MLC_MODEL', 'resnet50') == 'resnet50' and os.environ.get('MLC_PREPROCESS_PYTORCH', '') == "yes":
        pre_process = dataset.pre_process_imagenet_pytorch
    elif os.environ.get('MLC_MODEL', 'resnet50') == 'resnet50' and os.environ.get('MLC_PREPROCESS_TFLITE_TPU', '') == "yes":
        pre_process = dataset.pre_process_imagenet_tflite_tpu
    else:
        pre_process = dataset.pre_process_vgg

    imagenet.Imagenet(data_path=dataset_path,
                      image_list=dataset_list,
                      name="imagenet",
                      image_format=img_format,
                      pre_process=pre_process,
                      use_cache=True,
                      count=count,
                      threads=threads,
                      preprocessed_dir=preprocessed_dir)
