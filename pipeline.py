import uuid

from langchain_core.runnables import RunnableConfig

from backends.vectorstore import case_collection_name, delete_collection
from graph import build_graph
from logging_config import get_logger
from schemas import PipelineResult
from steps.ingestion import load_document_texts


logger = get_logger(__name__)


def run_pipeline(
    requirements_paths: list[str],
    application_paths: list[str],
) -> PipelineResult:
    requirements_documents = load_document_texts(requirements_paths)
    application_documents = load_document_texts(application_paths)
    compiled_graph = build_graph()
    thread_id = str(uuid.uuid4())
    collection_name = case_collection_name(thread_id)
    run_config: RunnableConfig = {
        "configurable": {"thread_id": thread_id}
    }
    initial_state = {
        "collection_name": collection_name,
        "requirements_documents": requirements_documents,
        "application_documents": application_documents,
    }
    logger.info("Starting pipeline run %s", thread_id)
    try:
        final_state = compiled_graph.invoke(initial_state, run_config)
    finally:
        delete_collection(collection_name)
    logger.info("Finished pipeline run %s", thread_id)
    return PipelineResult(
        report=final_state["report"],
        requirements=final_state["requirements"],
        verdicts=final_state["verdicts"],
        retrieved_context=final_state["retrieved_context"],
    )
