import code.common.constants as C
import code.llmlib.fields as llm_fields
import code.fields.models as model_fields
import code.fields.loadgen as loadgen_fields
import code.fields.harness as harness_fields

EXPORTS = {
    C.WorkloadSetting(C.HarnessType.Custom, C.AccuracyTarget(0.99), C.PowerSetting.MaxP): {
        llm_fields.llm_gen_config_path: 'code/llama2-70b/tensorrt/generation_config.json',
    },
    C.WorkloadSetting(C.HarnessType.Custom, C.AccuracyTarget(0.999), C.PowerSetting.MaxP): {
        llm_fields.llm_gen_config_path: 'code/llama2-70b/tensorrt/generation_config.json',
    },
}
