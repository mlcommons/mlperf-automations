"""
mlperf inference benchmarking tool
"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import array
import collections
import json
import logging
import os
import sys
import threading
import time
from queue import Queue
from PIL import Image
import mlperf_loadgen as lg
import numpy as np
import cv2
import glob
import dataset
import cognata
import cognata_labels

# import imagenet
# import coco
# import openimages

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("main")

NANO_SEC = 1e9
MILLI_SEC = 1000

# pylint: disable=missing-docstring

# the datasets we support
SUPPORTED_DATASETS = {
    "cognata-4mp-pt":
        (cognata.Cognata, None, cognata.PostProcessCognataPt(0.5, 200, 0.05, 1440, 2560),
         {"image_size": [1440, 2560, 3]}),
    "cognata-8mp-pt":
        (cognata.Cognata, None, cognata.PostProcessCognataPt(0.5, 200, 0.05, 2160, 3840),
         {"image_size": [2160, 3840, 3]})
}

# pre-defined command line options so simplify things. They are used as defaults and can be
# overwritten from command line

SUPPORTED_PROFILES = {
    "defaults": {
        "dataset": "imagenet",
        "backend": "tensorflow",
        "cache": 0,
        "max-batchsize": 32,
    },

    # retinanet
    "retinanet-pytorch": {
        "inputs": "image",
        "outputs": "boxes,labels,scores",
        "dataset": "openimages-800-retinanet",
        "backend": "pytorch-native",
        "model-name": "retinanet",
    },
}

SCENARIO_MAP = {
    "SingleStream": lg.TestScenario.SingleStream,
    "MultiStream": lg.TestScenario.MultiStream,
    "Server": lg.TestScenario.Server,
    "Offline": lg.TestScenario.Offline,
}

last_timeing = []


def get_args():
    """Parse commandline."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        choices=SUPPORTED_DATASETS.keys(),
        help="dataset")
    parser.add_argument(
        "--dataset-path",
        required=True,
        help="path to the dataset")
    parser.add_argument("--dataset-list", help="path to the dataset list")
    parser.add_argument(
        "--data-format",
        choices=[
            "NCHW",
            "NHWC"],
        help="data format")
    parser.add_argument(
        "--profile",
        choices=SUPPORTED_PROFILES.keys(),
        help="standard profiles")
    parser.add_argument("--scenario", default="SingleStream",
                        help="mlperf benchmark scenario, one of " + str(list(SCENARIO_MAP.keys())))
    parser.add_argument(
        "--max-batchsize",
        type=int,
        help="max batch size in a single inference")
    parser.add_argument("--model", required=True, help="model file")
    parser.add_argument("--output", default="output", help="test results")
    parser.add_argument("--inputs", help="model inputs")
    parser.add_argument("--outputs", help="model outputs")
    parser.add_argument("--backend", help="runtime to use")
    parser.add_argument(
        "--model-name",
        help="name of the mlperf model, ie. resnet50")
    parser.add_argument(
        "--threads",
        default=os.cpu_count(),
        type=int,
        help="threads")
    parser.add_argument("--qps", type=int, help="target qps")
    parser.add_argument("--cache", type=int, default=0, help="use cache")
    parser.add_argument(
        "--cache_dir",
        type=str,
        default=None,
        help="dir path for caching")
    parser.add_argument(
        "--preprocessed_dir",
        type=str,
        default=None,
        help="dir path for storing preprocessed images (overrides cache_dir)")
    parser.add_argument(
        "--use_preprocessed_dataset",
        action="store_true",
        help="use preprocessed dataset instead of the original")
    parser.add_argument(
        "--accuracy",
        action="store_true",
        help="enable accuracy pass")
    parser.add_argument(
        "--find-peak-performance",
        action="store_true",
        help="enable finding peak performance pass")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="debug, turn traces on")

    # file for user LoadGen settings such as target QPS
    parser.add_argument(
        "--user_conf",
        default="user.conf",
        help="user config for user LoadGen settings such as target QPS")
    # file for LoadGen audit settings
    parser.add_argument(
        "--audit_conf",
        default="audit.config",
        help="config for LoadGen audit settings")

    # below will override mlperf rules compliant settings - don't use for
    # official submission
    parser.add_argument("--time", type=int, help="time to scan in seconds")
    parser.add_argument("--count", type=int, help="dataset items to use")
    parser.add_argument(
        "--performance-sample-count",
        type=int,
        help="performance sample count")
    parser.add_argument(
        "--max-latency",
        type=float,
        help="mlperf max latency in pct tile")
    parser.add_argument(
        "--samples-per-query",
        default=8,
        type=int,
        help="mlperf multi-stream samples per query")
    args = parser.parse_args()

    # don't use defaults in argparser. Instead we default to a dict, override that with a profile
    # and take this as default unless command line give
    defaults = SUPPORTED_PROFILES["defaults"]

    if args.profile:
        profile = SUPPORTED_PROFILES[args.profile]
        defaults.update(profile)
    for k, v in defaults.items():
        kc = k.replace("-", "_")
        if getattr(args, kc) is None:
            setattr(args, kc, v)
    if args.inputs:
        args.inputs = args.inputs.split(",")
    if args.outputs:
        args.outputs = args.outputs.split(",")

    if args.scenario not in SCENARIO_MAP:
        parser.error("valid scanarios:" + str(list(SCENARIO_MAP.keys())))
    return args


def get_backend(backend):
    if backend == "null":
        from backend_null import BackendNull
        backend = BackendNull()
    elif backend == "pytorch":
        from backend_pytorch import BackendPytorch
        backend = BackendPytorch()
    elif backend == "pytorch-native":
        from backend_pytorch_native import BackendPytorchNative
        backend = BackendPytorchNative()
    else:
        raise ValueError("unknown backend: " + backend)
    return backend


class Item:
    """An item that we queue for processing by the thread pool."""

    def __init__(self, query_id, content_id, img, label=None):
        self.query_id = query_id
        self.content_id = content_id
        self.img = img
        self.label = label
        self.start = time.time()


class RunnerBase:
    def __init__(self, model, ds, threads, post_proc=None, max_batchsize=128):
        self.take_accuracy = False
        self.ds = ds
        self.model = model
        self.post_process = post_proc
        self.threads = threads
        self.take_accuracy = False
        self.max_batchsize = max_batchsize
        self.result_timing = []
        self.proc_results = []

    def handle_tasks(self, tasks_queue):
        pass

    def start_run(self, result_dict, take_accuracy):
        self.result_dict = result_dict
        self.result_timing = []
        self.take_accuracy = take_accuracy
        self.post_process.start()

    def run_one_item(self, qitem):
        # run the prediction
        processed_results = []
        try:
            results = self.model.predict({self.model.inputs[0]: qitem.img})

            processed_results = self.post_process(
                results, qitem.content_id, qitem.label, self.result_dict)
            if self.take_accuracy:
                self.post_process.add_results(processed_results)

            self.result_timing.append(time.time() - qitem.start)

        except Exception as ex:  # pylint: disable=broad-except
            src = [self.ds.get_item_loc(i) for i in qitem.content_id]
            log.error("thread: failed on contentid=%s, %s", src, ex)
            # since post_process will not run, fake empty responses
            processed_results = [[]] * len(qitem.query_id)
        finally:
            response_array_refs = []
            response = []
            for idx, query_id in enumerate(qitem.query_id):

                # Temporal hack for Cognata to add only boxes - fix
                processed_results2 = [x['boxes'].numpy()
                                      for x in processed_results[idx]]
                self.proc_results.append([{'boxes': x['boxes'].tolist(), 'scores': x['scores'].tolist(), 'labels': x['labels'].tolist(), 'id': x['id']}
                                          for x in processed_results[idx]])
                response_array = array.array("B", np.array(
                    processed_results2, np.float32).tobytes())
                response_array_refs.append(response_array)
                bi = response_array.buffer_info()
                response.append(lg.QuerySampleResponse(query_id, bi[0], bi[1]))
            lg.QuerySamplesComplete(response)

    def enqueue(self, query_samples):
        idx = [q.index for q in query_samples]
        query_id = [q.id for q in query_samples]
        if len(query_samples) < self.max_batchsize:
            data, label = self.ds.get_samples(idx)
            self.run_one_item(Item(query_id, idx, data, label))
        else:
            bs = self.max_batchsize
            for i in range(0, len(idx), bs):
                data, label = self.ds.get_samples(idx[i:i + bs])
                self.run_one_item(
                    Item(query_id[i:i + bs], idx[i:i + bs], data, label))

    def finish(self):
        pass


class QueueRunner(RunnerBase):
    def __init__(self, model, ds, threads, post_proc=None, max_batchsize=128):
        super().__init__(model, ds, threads, post_proc, max_batchsize)
        self.tasks = Queue(maxsize=threads * 4)
        self.workers = []
        self.result_dict = {}

        for _ in range(self.threads):
            worker = threading.Thread(
                target=self.handle_tasks, args=(
                    self.tasks,))
            worker.daemon = True
            self.workers.append(worker)
            worker.start()

    def handle_tasks(self, tasks_queue):
        """Worker thread."""
        while True:
            qitem = tasks_queue.get()
            if qitem is None:
                # None in the queue indicates the parent want us to exit
                tasks_queue.task_done()
                break
            self.run_one_item(qitem)
            tasks_queue.task_done()

    def enqueue(self, query_samples):
        idx = [q.index for q in query_samples]
        query_id = [q.id for q in query_samples]

        if len(query_samples) < self.max_batchsize:
            data, label = self.ds.get_samples(idx)
            self.tasks.put(Item(query_id, idx, data, label))
        else:
            bs = self.max_batchsize
            for i in range(0, len(idx), bs):
                ie = i + bs

                data, label = self.ds.get_samples(idx[i:ie])
                self.tasks.put(Item(query_id[i:ie], idx[i:ie], data, label))

    def finish(self):
        # exit all threads
        for _ in self.workers:
            self.tasks.put(None)
        for worker in self.workers:
            worker.join()


def add_results(final_results, name, result_dict,
                result_list, took, show_accuracy=False):
    percentiles = [50., 80., 90., 95., 99., 99.9]
    buckets = np.percentile(result_list, percentiles).tolist()
    buckets_str = ",".join(["{}:{:.4f}".format(p, b)
                           for p, b in zip(percentiles, buckets)])

    if result_dict["total"] == 0:
        result_dict["total"] = len(result_list)
    # this is what we record for each run
    result = {
        "took": took,
        "mean": np.mean(result_list),
        "percentiles": {str(k): v for k, v in zip(percentiles, buckets)},
        "qps": len(result_list) / took,
        "count": len(result_list),
        "good_items": result_dict["good"],
        "total_items": result_dict["total"],
    }
    acc_str = ""
    if show_accuracy:
        result["accuracy"] = 100. * result_dict["good"] / result_dict["total"]
        acc_str = ", acc={:.3f}%".format(result["accuracy"])
        if "mAP" in result_dict:
            result["mAP"] = 100. * result_dict["mAP"]
            acc_str += ", mAP={:.3f}%".format(result["mAP"])
            if os.environ.get('MLC_COGNATA_ACCURACY_DUMP_FILE', '') != '':
                accuracy_file = os.environ['MLC_COGNATA_ACCURACY_DUMP_FILE']
                with open(accuracy_file, "w") as f:
                    f.write("{:.3f}%".format(result["mAP"]))

        if "mAP_classes" in result_dict:
            result['mAP_per_classes'] = result_dict["mAP_classes"]
            acc_str += ", mAP_classes={}".format(result_dict["mAP_classes"])

    # add the result to the result dict
    final_results[name] = result

    # to stdout
    print("{} qps={:.2f}, mean={:.4f}, time={:.3f}{}, queries={}, tiles={}".format(
        name, result["qps"], result["mean"], took, acc_str,
        len(result_list), buckets_str))

    print('======================================================================')

#########################################################################


def main():
    print('======================================================================')

    global last_timeing
    args = get_args()

    log.info(args)

    # Find backend
    backend = get_backend(args.backend)

    # Load model to backend (Grigori moved here before dataset
    #   since we get various info about pre-processing from the model)

    print('')
    print('Loading model ...')
    print('')

    model = backend.load(args.model, inputs=args.inputs, outputs=args.outputs)

#    print (model.num_classes)
#    print (model.image_size)

    # --count applies to accuracy mode only and can be used to limit the number of images
    # for testing.
    count_override = False
    count = args.count
    if count:
        count_override = True

    # dataset to use
    wanted_dataset, pre_proc, post_proc, kwargs = SUPPORTED_DATASETS[args.dataset]
#    if args.use_preprocessed_dataset:
#        pre_proc=None

    print('')
    print('Loading dataset and preprocessing if needed ...')
    print('* Dataset path: {}'.format(args.dataset_path))
    print('* Preprocessed cache path: {}'.format(args.cache_dir))
    print('')

    ds = wanted_dataset(data_path=args.dataset_path,
                        image_list=args.dataset_list,
                        name=args.dataset,
                        pre_process=pre_proc,
                        use_cache=args.cache,
                        count=count,
                        cache_dir=args.cache_dir,
                        preprocessed_dir=args.preprocessed_dir,
                        threads=args.threads,
                        model_config=model.config,           # For ABTF
                        model_num_classes=model.num_classes,  # For ABTF
                        model_image_size=model.image_size,   # For ABTF
                        **kwargs)

    # For ABTF - maybe find cleaner way
    post_proc.encoder = ds.encoder

    final_results = {
        "runtime": model.name(),
        "version": model.version(),
        "time": int(time.time()),
        "args": vars(args),
        "cmdline": str(args),
    }

    user_conf = os.path.abspath(args.user_conf)
    if not os.path.exists(user_conf):
        log.error("{} not found".format(user_conf))
        sys.exit(1)

    audit_config = os.path.abspath(args.audit_conf)

    if args.output:
        output_dir = os.path.abspath(args.output)
        os.makedirs(output_dir, exist_ok=True)
        os.chdir(output_dir)

    #
    # make one pass over the dataset to validate accuracy
    #
    count = ds.get_item_count()

    # warmup
    if os.environ.get('MLC_ABTF_ML_MODEL_SKIP_WARMUP',
                      '').strip().lower() != 'yes':
        ds.load_query_samples([0])
        for _ in range(5):
            img, _ = ds.get_samples([0])
            _ = backend.predict({backend.inputs[0]: img})
        ds.unload_query_samples(None)

    scenario = SCENARIO_MAP[args.scenario]
    runner_map = {
        lg.TestScenario.SingleStream: RunnerBase,
        lg.TestScenario.MultiStream: QueueRunner,
        lg.TestScenario.Server: QueueRunner,
        lg.TestScenario.Offline: QueueRunner
    }

    runner = runner_map[scenario](
        model,
        ds,
        args.threads,
        post_proc=post_proc,
        max_batchsize=args.max_batchsize)

    def issue_queries(query_samples):
        runner.enqueue(query_samples)

    def flush_queries():
        pass

    log_output_settings = lg.LogOutputSettings()
    log_output_settings.outdir = output_dir
    log_output_settings.copy_summary_to_stdout = False
    log_settings = lg.LogSettings()
    log_settings.enable_trace = args.debug
    log_settings.log_output = log_output_settings

    settings = lg.TestSettings()
    settings.FromConfig(user_conf, args.model_name, args.scenario)
    settings.scenario = scenario
    settings.mode = lg.TestMode.PerformanceOnly
    if args.accuracy:
        settings.mode = lg.TestMode.AccuracyOnly
    if args.find_peak_performance:
        settings.mode = lg.TestMode.FindPeakPerformance

    if args.time:
        # override the time we want to run
        settings.min_duration_ms = args.time * MILLI_SEC
        settings.max_duration_ms = args.time * MILLI_SEC

    if args.qps:
        qps = float(args.qps)
        settings.server_target_qps = qps
        settings.offline_expected_qps = qps

    if count_override:
        settings.min_query_count = count
        settings.max_query_count = count

    if args.samples_per_query:
        settings.multi_stream_samples_per_query = args.samples_per_query

    if args.max_latency:
        settings.server_target_latency_ns = int(args.max_latency * NANO_SEC)
        settings.multi_stream_expected_latency_ns = int(
            args.max_latency * NANO_SEC)

    performance_sample_count = args.performance_sample_count if args.performance_sample_count else min(
        count, 500)
    sut = lg.ConstructSUT(issue_queries, flush_queries)
    qsl = lg.ConstructQSL(
        count,
        performance_sample_count,
        ds.load_query_samples,
        ds.unload_query_samples)

    log.info("starting {}".format(scenario))
    result_dict = {"good": 0, "total": 0, "scenario": str(scenario)}
    runner.start_run(result_dict, args.accuracy)

    lg.StartTestWithLogSettings(sut, qsl, settings, log_settings, audit_config)

    if not last_timeing:
        last_timeing = runner.result_timing
    if args.accuracy:
        post_proc.finalize(result_dict, ds, output_dir=args.output)

    add_results(final_results, "{}".format(scenario),
                result_dict, last_timeing, time.time() - ds.last_loaded, args.accuracy)

    runner.finish()
    lg.DestroyQSL(qsl)
    lg.DestroySUT(sut)
    #
    # write final results
    #
    if args.output:
        with open("results.json", "w") as f:
            json.dump(final_results, f, sort_keys=True, indent=4)
        if args.accuracy:
            print('Saving model output examples ...')
            files = glob.glob(
                os.path.join(
                    args.dataset_path,
                    '10002_Urban_Clear_Morning',
                    'Cognata_Camera_01_8M_png',
                    '*.png'))
            files = sorted(files)
            for pred_batch in runner.proc_results:
                for pred in pred_batch:
                    f = files[pred['id']]
                    cls_threshold = 0.3
                    img = Image.open(f).convert("RGB")
                    loc, label, prob = np.array(
                        pred['boxes']), np.array(
                        pred['labels']), np.array(
                        pred['scores'])
                    best = np.argwhere(prob > cls_threshold).squeeze(axis=1)

                    loc = loc[best]
                    label = label[best]
                    prob = prob[best]

                    # Update input image with boxes and predictions
                    output_img = cv2.imread(f)
                    if len(loc) > 0:

                        loc = loc.astype(np.int32)

                        for box, lb, pr in zip(loc, label, prob):
                            category = cognata_labels.label_info[lb]
                            color = cognata_labels.colors[lb]

                            xmin, ymin, xmax, ymax = box

                            cv2.rectangle(
                                output_img, (xmin, ymin), (xmax, ymax), color, 2)

                            text_size = cv2.getTextSize(
                                category + " : %.2f" %
                                pr, cv2.FONT_HERSHEY_PLAIN, 1, 1)[0]

                            cv2.rectangle(
                                output_img, (xmin, ymin), (xmin + text_size[0] + 3, ymin + text_size[1] + 4), color, -1)

                            cv2.putText(
                                output_img, category + " : %.2f" % pr,
                                (xmin, ymin +
                                 text_size[1] +
                                    4), cv2.FONT_HERSHEY_PLAIN, 1,
                                (255, 255, 255), 1)
                        output = "{}_prediction.jpg".format(f[:-4])

                        d1 = os.path.join(os.path.dirname(output), 'output')
                        if not os.path.isdir(d1):
                            os.makedirs(d1)

                        d2 = os.path.basename(output)

                        output = os.path.join(d1, d2)
                        cv2.imwrite(output, output_img)
            with open("preds.json", "w") as f:
                json.dump(runner.proc_results, f, indent=4)


if __name__ == "__main__":
    main()
