import pathlib
import uuid

from langchain_core.runnables import RunnableConfig

from graph import build_graph
from logging_config import get_logger
from schemas import PipelineResult


logger = get_logger(__name__)


def _read_document_text(file_path: str) -> str:
    document_text = pathlib.Path(file_path).read_text(encoding="utf-8")
    if not document_text.strip():
        raise ValueError(f"Document at {file_path} is empty.")
    return document_text


def run_pipeline(
    requirements_path: str,
    application_path: str,
) -> PipelineResult:
    requirements_document_text = _read_document_text(requirements_path)
    application_document_text = _read_document_text(application_path)
    compiled_graph = build_graph()
    thread_id = str(uuid.uuid4())
    run_config: RunnableConfig = {
        "configurable": {"thread_id": thread_id}
    }
    initial_state = {
        "requirements_document_text": requirements_document_text,
        "requirements_document_path": requirements_path,
        "application_document_text": application_document_text,
        "application_document_path": application_path,
    }
    logger.info("Starting pipeline run %s", thread_id)
    final_state = compiled_graph.invoke(initial_state, run_config)
    logger.info("Finished pipeline run %s", thread_id)
    return PipelineResult(
        report=final_state["report"],
        requirements=final_state["requirements"],
        verdicts=final_state["verdicts"],
        retrieved_evidence=final_state["retrieved_evidence"],
    )
