import uuid
from agents.profiler import inspect_files_tool, profiler_tool
from agents.sttm_generator import generate_bronze_sttm_tool,generate_silver_sttm_tool,generate_gold_sttm_tool,inspect_context_tool
from agents.silver_agent import silver_ingestion_tool
from agents.bronze_agent import bronze_ingestion_tool
from agents.gold_agent import gold_ingestion_tool
from agents.reporter import load_data, execute_query as execute_sql_query, generate_html_report
from core.audit import log_event


class PipelineError(Exception):
    """Raised when a pipeline phase fails, so later phases are not run."""


def new_state(object_name):
    return {
        "object": object_name,
        "run_id": uuid.uuid4(),
        "status": "started",
        "bronze_sttm_path": None,
        "bronze_parquet_path": None,
        "silver_sttm_path": None,
        "silver_parquet_path": None,
        "gold_sttm_path": None,
    }

def run_phase1(state):
    state["status"]="phase 1 started"
    raw_csv_path=f"data/raw/{state['object']}.csv"
    # print(inspect_files_tool(path=raw_csv_path))
    result=profiler_tool(raw_csv_path, state["object"])
    # print(result["path"])
    state["profile_path"]=result["path"]
    profile_json=inspect_context_tool(state["profile_path"])

    bst_result=generate_bronze_sttm_tool(result=profile_json, run_id=state["run_id"])
    if bst_result:    
        state["status"]="phase 1 completed"
        state["bronze_sttm_path"]=bst_result
        log_event(state["run_id"], "phase1", "completed")
    else:
        log_event(state["run_id"], "phase1", "failed", "generate_bronze_sttm_tool")
        raise PipelineError("phase 1 failed at generate_bronze_sttm_tool")
    return state

def run_phase2(state):
    state["status"]="phase 2 started"
    raw_csv_path=f"data/raw/{state['object']}.csv"
    bronze_ingestion_pq=bronze_ingestion_tool(raw_csv_path, state["bronze_sttm_path"], state["object"])
    if bronze_ingestion_pq:    
        state["status"]="bronze_ingestion_pq completed"
        state["bronze_parquet_path"]=bronze_ingestion_pq
    else:
        log_event(state["run_id"], "phase2", "failed", "bronze_ingestion_tool")
        raise PipelineError("phase 2 failed at bronze_ingestion_tool")

    sst_result=generate_silver_sttm_tool(state["bronze_parquet_path"], run_id=state["run_id"])
    if sst_result:    
        state["status"]="phase 2 completed"
        state["silver_sttm_path"]=sst_result
        log_event(state["run_id"], "phase2", "completed")
    else:
        log_event(state["run_id"], "phase2", "failed", "generate_silver_sttm_tool")
        raise PipelineError("phase 2 failed at generate_silver_sttm_tool")
    return state

def run_phase3(state):
    state["status"]="phase 3 started"
    silver_ingestion_pq=silver_ingestion_tool(state["bronze_parquet_path"], state["silver_sttm_path"], state["object"])
    if silver_ingestion_pq:    
        state["status"]="silver_ingestion_pq completed"
        state["silver_parquet_path"]=silver_ingestion_pq
    else:
        log_event(state["run_id"], "phase3", "failed", "silver_ingestion_tool")
        raise PipelineError("phase 3 failed at silver_ingestion_tool")

    gst_result=generate_gold_sttm_tool(state["silver_parquet_path"], run_id=state["run_id"])
    if gst_result:    
        state["status"]="phase 3 completed"
        state["gold_sttm_path"]=gst_result
        log_event(state["run_id"], "phase3", "completed")
    else:
        log_event(state["run_id"], "phase3", "failed", "generate_gold_sttm_tool")
        raise PipelineError("phase 3 failed at generate_gold_sttm_tool")
    return state

def run_phase4(state):
    state["status"]="phase 4 started"
    gold_ingestion_pq=gold_ingestion_tool(state["silver_parquet_path"], state["gold_sttm_path"], state["object"])
    if gold_ingestion_pq:    
        state["status"]="gold_ingestion_pq completed"
        state["gold_pq_folder"]=gold_ingestion_pq
        log_event(state["run_id"], "phase4", "completed")
    else:
        log_event(state["run_id"], "phase4", "failed", "gold_ingestion_tool")
        raise PipelineError("phase 4 failed at gold_ingestion_tool")

    return state

def execute_query(gold_pq_folder, question, object_name="pipeline"):
    db=load_data(gold_pq_folder)
    result_df=execute_sql_query(db, question)
    report_path=generate_html_report(question, result_df, object_name)
    return result_df, report_path

def execute_pipeline(object_name):
    state = new_state(object_name=object_name)
    log_event(state["run_id"], "pipeline", "started", f"object={object_name}")
    try:
        state = run_phase1(state)
        state = run_phase2(state)
        state = run_phase3(state)
        state = run_phase4(state)
    except PipelineError as e:
        print(f"Pipeline aborted: {e}")
        log_event(state["run_id"], "pipeline", "aborted", str(e))
        return None
    log_event(state["run_id"], "pipeline", "completed")
    return state

def main():
    object_name="products"
    question="Which product has the least sales?"
    state=execute_pipeline(object_name)
    # print(execute_query("data/gold", question))


if __name__=="__main__":
    main()
