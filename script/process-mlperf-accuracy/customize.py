from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    xsep = ';' if os_info['platform'] == 'windows' else ':'

    env = i['env']
    logger = i['automation'].logger

    results_dir = env.get("MLC_MLPERF_ACCURACY_RESULTS_DIR", "")

    if results_dir == "":
        logger.error("Please set MLC_MLPERF_ACCURACY_RESULTS_DIR")
        return {'return': -1}

    # In fact, we expect only 1 command line here
    run_cmds = []

    if env.get('MLC_MAX_EXAMPLES', '') != '' and env.get(
            'MLC_MLPERF_RUN_STYLE', '') != 'valid':
        max_examples_string = " --max_examples " + env['MLC_MAX_EXAMPLES']
    else:
        max_examples_string = ""

    results_dir_split = results_dir.split(xsep)
    dataset = env['MLC_DATASET']
    regenerate_accuracy_file = env.get(
        'MLC_MLPERF_REGENERATE_ACCURACY_FILE', env.get(
            'MLC_RERUN', False))

    for result_dir in results_dir_split:

        out_file = os.path.join(result_dir, 'accuracy.txt')

        if os.path.exists(out_file) and (
                os.stat(out_file).st_size != 0) and not regenerate_accuracy_file:
            continue

        if dataset == "openimages":
            if env.get('MLC_DATASET_PATH_ROOT', '') != '':
                dataset_dir = env['MLC_DATASET_PATH_ROOT']
                if 'DATASET_ANNOTATIONS_FILE_PATH' in env:
                    del (env['DATASET_ANNOTATIONS_FILE_PATH'])
            else:
                env['DATASET_ANNOTATIONS_FILE_PATH'] = env['MLC_DATASET_ANNOTATIONS_FILE_PATH']
                dataset_dir = os.getcwd()  # not used, just to keep the script happy
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " " + "'" + os.path.join(env['MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH'], "tools",
                                                                             "accuracy-openimages.py") + "'" + " --mlperf-accuracy-file " + "'" + os.path.join(result_dir,
                                                                                                                                                               "mlperf_log_accuracy.json") + "'" + " --openimages-dir " + "'" + dataset_dir + "'" + " --verbose > " + "'" + \
                out_file + "'"

        elif dataset == "imagenet":
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH'], "tools",
                                                                        "accuracy-imagenet.py") + "' --mlperf-accuracy-file '" + os.path.join(result_dir,
                                                                                                                                              "mlperf_log_accuracy.json") + "' --imagenet-val-file '" + os.path.join(env['MLC_DATASET_AUX_PATH'],
                                                                                                                                                                                                                     "val.txt") + "' --dtype " + env.get('MLC_ACCURACY_DTYPE', "float32") + " > '" + out_file + "'"

        elif dataset == "squad":
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_BERT_PATH'],
                                                                        "accuracy-squad.py") + "' --val_data '" + env['MLC_DATASET_SQUAD_VAL_PATH'] + \
                "' --log_file '" + os.path.join(result_dir, "mlperf_log_accuracy.json") + \
                "' --vocab_file '" + env['MLC_ML_MODEL_BERT_VOCAB_FILE_WITH_PATH'] + \
                "' --out_file '" + os.path.join(result_dir, 'predictions.json') + \
                "' --features_cache_file '" + os.path.join(env['MLC_MLPERF_INFERENCE_BERT_PATH'], 'eval_features.pickle') + \
                "' --output_dtype " + env['MLC_ACCURACY_DTYPE'] + env.get(
                'MLC_OUTPUT_TRANSPOSED', '') + max_examples_string + " > '" + out_file + "'"

        elif dataset == "cnndm":
            if env.get('MLC_MLPERF_IMPLEMENTATION', '') == 'intel':
                accuracy_checker_file = env['MLC_MLPERF_INFERENCE_INTEL_GPTJ_ACCURACY_FILE_WITH_PATH']
                env['+PYTHONPATH'] = [os.path.dirname(env['MLC_MLPERF_INFERENCE_INTEL_GPTJ_DATASET_FILE_WITH_PATH'])] + [
                    os.path.dirname(env['MLC_MLPERF_INFERENCE_INTEL_GPTJ_DATASET_ITEM_FILE_WITH_PATH'])] + env['+PYTHONPATH']
                suffix_string = " --model-name-or-path '" + \
                    env['GPTJ_CHECKPOINT_PATH'] + "'"
            else:
                accuracy_checker_file = os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "language", "gpt-j",
                                                     "evaluation.py")
                suffix_string = " --dtype " + \
                    env.get('MLC_ACCURACY_DTYPE', "float32")
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + accuracy_checker_file + "' --mlperf-accuracy-file '" + os.path.join(result_dir, "mlperf_log_accuracy.json") + \
                "' --dataset-file '" + \
                env['MLC_DATASET_EVAL_PATH'] + "'" + \
                suffix_string + " > '" + out_file + "'"

        elif dataset == "openorca":
            accuracy_checker_file = os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "language", "llama2-70b",
                                                 "evaluate-accuracy.py")
            if env.get('MLC_VLLM_SERVER_MODEL_NAME', '') == '':
                checkpoint_path = env['MLC_ML_MODEL_LLAMA2_FILE_WITH_PATH']
            else:
                checkpoint_path = env['MLC_VLLM_SERVER_MODEL_NAME']
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + accuracy_checker_file + "' --checkpoint-path '" + checkpoint_path + "' --mlperf-accuracy-file '" + os.path.join(result_dir, "mlperf_log_accuracy.json") + \
                "' --dataset-file '" + env['MLC_DATASET_PREPROCESSED_PATH'] + "'" + " --dtype " + env.get(
                    'MLC_ACCURACY_DTYPE', "int32") + " > '" + out_file + "'"

        elif dataset == "openorca-gsm8k-mbxp-combined":
            accuracy_checker_file = os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "language", "mixtral-8x7b",
                                                 "evaluate-accuracy.py")
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + accuracy_checker_file + "' --checkpoint-path '" + env['MIXTRAL_CHECKPOINT_PATH'] + "' --mlperf-accuracy-file '" + os.path.join(result_dir, "mlperf_log_accuracy.json") + \
                "' --dataset-file '" + env['MLC_DATASET_MIXTRAL_PREPROCESSED_PATH'] + "'" + \
                " --dtype " + env.get('MLC_ACCURACY_DTYPE',
                                      "float32") + " > '" + out_file + "'"

        elif dataset == "coco2014":
            env['+PYTHONPATH'] = [
                os.path.join(
                    env['MLC_MLPERF_INFERENCE_SOURCE'],
                    "text_to_image",
                    "tools"),
                os.path.join(
                    env['MLC_MLPERF_INFERENCE_SOURCE'],
                    "text_to_image",
                    "tools",
                    "fid")]
            extra_options = ""

            if env.get('MLC_SDXL_STATISTICS_FILE_PATH', '') != '':
                extra_options += (
                    f""" --statistics-path '{
                        env['MLC_SDXL_STATISTICS_FILE_PATH']}'"""
                )

            if env.get('MLC_SDXL_COMPLIANCE_IMAGES_PATH', '') != '':
                extra_options += (
                    f""" --compliance-images-path '{
                        env['MLC_SDXL_COMPLIANCE_IMAGES_PATH']}' """
                )
            else:
                extra_options += f""" --compliance-images-path '{
                    os.path.join(
                        result_dir, "images")}' """

            if env.get('MLC_COCO2014_SAMPLE_ID_PATH', '') != '':
                extra_options += (
                    f" --ids-path '{env['MLC_COCO2014_SAMPLE_ID_PATH']}' "
                )

            if env.get('MLC_SDXL_ACCURACY_RUN_DEVICE', '') != '':
                extra_options += (
                    f" --device '{env['MLC_SDXL_ACCURACY_RUN_DEVICE']}' "
                )

            # env['DATASET_ANNOTATIONS_FILE_PATH'] = env['MLC_DATASET_ANNOTATIONS_FILE_PATH']
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "text_to_image", "tools",
                                                                        "accuracy_coco.py") + "' --mlperf-accuracy-file '" + os.path.join(result_dir, "mlperf_log_accuracy.json") + \
                "' --caption-path '" + os.path.join(
                env['MLC_MLPERF_INFERENCE_SOURCE'],
                "text_to_image",
                "coco2014",
                "captions",
                "captions_source.tsv") + "'" + extra_options + " > '" + out_file + "'"

        elif dataset == "kits19":
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_3DUNET_PATH'],
                                                                        "accuracy_kits.py") + \
                "' --preprocessed_data_dir '" + env['MLC_DATASET_PREPROCESSED_PATH'] +\
                "' --postprocessed_data_dir '" + result_dir +\
                "' --log_file '" + os.path.join(result_dir, "mlperf_log_accuracy.json") + \
                "' --output_dtype " + \
                env['MLC_ACCURACY_DTYPE'] + " > '" + out_file + "'"

        elif dataset == "librispeech":
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_RNNT_PATH'],
                                                                        "accuracy_eval.py") + \
                "' --dataset_dir '" + os.path.join(env['MLC_DATASET_PREPROCESSED_PATH'], "..") +\
                "' --manifest '" + env['MLC_DATASET_PREPROCESSED_JSON'] +\
                "' --log_dir '" + result_dir + \
                "' --output_dtype " + \
                env['MLC_ACCURACY_DTYPE'] + " > '" + out_file + "'"

        elif dataset == "terabyte":
            extra_options = ""
            if env.get('MLC_DLRM_V2_AGGREGATION_TRACE_FILE_PATH', '') != '':
                extra_options += (
                    f""" --aggregation-trace-file '{
                        env['MLC_DLRM_V2_AGGREGATION_TRACE_FILE_PATH']}' """
                )
            if env.get('MLC_DLRM_V2_DAY23_FILE_PATH', '') != '':
                extra_options += (
                    f""" --day-23-file '{
                        env['MLC_DLRM_V2_DAY23_FILE_PATH']}' """
                )
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_DLRM_V2_PATH'], "pytorch", "tools",
                                                                        "accuracy-dlrm.py") + "' --mlperf-accuracy-file '" + os.path.join(result_dir,
                                                                                                                                          "mlperf_log_accuracy.json") + "'" + extra_options + \
                " --dtype " + env.get('MLC_ACCURACY_DTYPE',
                                      "float32") + " > '" + out_file + "'"

        elif dataset == "igbh":
            if env.get('MLC_DATASET_IGBH_SIZE', '') == '':
                if env.get('MLC_MLPERF_SUBMISSION_GENERATION_STYLE',
                           '') == "full":
                    env['MLC_DATASET_IGBH_SIZE'] = "full"
                else:
                    env['MLC_DATASET_IGBH_SIZE'] = "tiny"
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "graph", "R-GAT", "tools", "accuracy_igbh.py") + "' --mlperf-accuracy-file '" + os.path.join(
                result_dir, "mlperf_log_accuracy.json") + "' --dataset-path '" + env['MLC_DATASET_IGBH_PATH'] + "' --dataset-size '" + env['MLC_DATASET_IGBH_SIZE'] + "' --output-file '" + out_file + "'"

        elif dataset == "dataset_llama3":
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "language", "llama3.1-405b", "evaluate-accuracy.py") + "' --checkpoint-path '" + env['MLC_ML_MODEL_LLAMA3_CHECKPOINT_PATH'] + "' --mlperf-accuracy-file '" + os.path.join(
                result_dir, "mlperf_log_accuracy.json") + "' --dtype '" + env['MLC_ACCURACY_DTYPE'] + "' --dataset-file '" + env['MLC_DATASET_LLAMA3_PATH'] + "' > '" + out_file + "'"

        elif dataset == "waymo":
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "automotive", "3d-object-detection", "accuracy_waymo.py") + "' --mlperf-accuracy-file '" + os.path.join(
                result_dir, "mlperf_log_accuracy.json") + "' --waymo-dir '" + env['MLC_DATASET_WAYMO_PATH'] + "' > '" + out_file + "'"

        elif dataset == "nuscenes":
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_AUTOMOTIVE_BEVFORMER_PATH'], "accuracy_nuscenes_cpu.py") + "' --mlperf-accuracy-file '" + os.path.join(
                result_dir, "mlperf_log_accuracy.json") + "' --nuscenes-dir '" + env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'] + "' --config '" + os.path.join(env['MLC_MLPERF_AUTOMOTIVE_BEVFORMER_PATH'], "projects" + "configs" + "bevformer" + "bevformer_tiny.py") + "' > '" + out_file + "'"
        
        elif dataset == "cognata_ssd":
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_AUTOMOTIVE_SSD_RESNET50_PATH'], "accuracy_cognata.py") + "' --mlperf-accuracy-file '" + os.path.join(
                result_dir, "mlperf_log_accuracy.json") + "' --dataset-path '" + env['MLC_PREPROCESSED_DATASET_COGNATA_PATH'] + "' --dataset cognata --config '" + "baseline_8MP_ss_scales_fm1_5x5_all" + "' > '" + out_file + "'"
            
        elif dataset == "cognata_deeplab":
            CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + " '" + os.path.join(env['MLC_MLPERF_AUTOMOTIVE_DEEPLABV3PLUS_PATH'], "accuracy_cognata.py") + "' --mlperf-accuracy-file '" + os.path.join(
                result_dir, "mlperf_log_accuracy.json") +  "' --dataset-path '" + env['MLC_PREPROCESSED_DATASET_COGNATA_PATH'] + "' > '" + out_file + "'"
    
        else:
            return {'return': 1, 'error': 'Unsupported dataset'}

        run_cmds.append(CMD)

    if os_info['platform'] == 'windows':
        env['MLC_RUN_CMDS'] = (
            '\n'.join(run_cmds)).replace(
            "'",
            '"').replace(
            '>',
            '^>')
    else:
        env['MLC_RUN_CMDS'] = "??".join(run_cmds)

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']
    env = i['env']
    state = i['state']
    logger = i['automation'].logger
    xsep = ';' if os_info['platform'] == 'windows' else ':'

    results_dir = env.get("MLC_MLPERF_ACCURACY_RESULTS_DIR", "")

    results_dir_split = results_dir.split(xsep)

    for result_dir in results_dir_split:
        accuracy_file = os.path.join(result_dir, "accuracy.txt")

        if os.path.exists(accuracy_file):
            logger.info('')
            logger.info('Accuracy file: {}'.format(accuracy_file))
            logger.info('')

            x = ''
            with open(accuracy_file, "r") as fp:
                x = fp.read()

            if x != '':
                logger.info(f"{x}")

                # Trying to extract accuracy dict
                for y in x.split('\n'):
                    if y.startswith('{') and y.endswith('}'):

                        import json

                        try:
                            z = json.loads(y)
                            state['app_mlperf_inference_accuracy'] = z

                            break
                        except ValueError as e:
                            pass

            logger.info('')
    return {'return': 0}
