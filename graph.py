import operator
import sqlite3
from typing import Annotated, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Send

from backends.vectorstore import index_chunks
from config import CHECKPOINT_DATABASE_PATH
from logging_config import get_logger
from schemas import (
    Chunk,
    DocumentInput,
    Requirement,
    RequirementDraft,
    RetrievedContextRecord,
    Verdict,
)
from steps.chunking import (
    split_application_document,
    split_requirements_document,
)
from steps.conditions import extract_conditions
from steps.deduplication import deduplicate_requirements
from steps.evidence_retrieval import retrieve_context_chunks
from steps.report import build_report
from steps.requirements_extraction import extract_requirements_from_chunk
from steps.verdicts import generate_verdict


logger = get_logger(__name__)


class PipelineState(TypedDict):
    collection_name: str
    requirements_documents: list[DocumentInput]
    application_documents: list[DocumentInput]
    requirement_chunks: list[Chunk]
    requirement_drafts: Annotated[list[RequirementDraft], operator.add]
    deduplicated_drafts: list[RequirementDraft]
    requirements: list[Requirement]
    application_chunks: list[Chunk]
    verdicts: Annotated[list[Verdict], operator.add]
    retrieved_context: Annotated[
        list[RetrievedContextRecord], operator.add
    ]
    report: str


class ChunkExtractionInput(TypedDict):
    chunk: Chunk


class RequirementVerdictInput(TypedDict):
    requirement: Requirement
    collection_name: str


def split_requirements_node(
    state: PipelineState,
) -> dict[str, list[Chunk]]:
    chunks = []
    for document in state["requirements_documents"]:
        chunks.extend(
            split_requirements_document(document.text, document.path)
        )
    return {"requirement_chunks": chunks}


def route_to_extraction(state: PipelineState) -> list[Send]:
    requirement_chunks = state["requirement_chunks"]
    if not requirement_chunks:
        raise ValueError(
            "No requirements chunks were produced; cannot extract "
            "requirements from an empty document."
        )
    sends = []
    for chunk in requirement_chunks:
        sends.append(Send("extract_requirements_node", {"chunk": chunk}))
    return sends


def extract_requirements_node(
    state: ChunkExtractionInput,
) -> dict[str, list[RequirementDraft]]:
    requirement_drafts = extract_requirements_from_chunk(
        state["chunk"]
    )
    return {"requirement_drafts": requirement_drafts}


def deduplicate_requirements_node(
    state: PipelineState,
) -> dict[str, list[RequirementDraft]]:
    deduplicated_drafts = deduplicate_requirements(
        state["requirement_drafts"]
    )
    return {"deduplicated_drafts": deduplicated_drafts}


def extract_conditions_node(
    state: PipelineState,
) -> dict[str, list[Requirement]]:
    requirements = extract_conditions(state["deduplicated_drafts"])
    return {"requirements": requirements}


def index_application_node(
    state: PipelineState,
) -> dict[str, list[Chunk]]:
    application_chunks = []
    for document in state["application_documents"]:
        application_chunks.extend(
            split_application_document(document.text, document.path)
        )
    index_chunks(state["collection_name"], application_chunks)
    return {"application_chunks": application_chunks}


def route_to_verdicts(state: PipelineState) -> list[Send]:
    requirements = state["requirements"]
    if not requirements:
        raise ValueError(
            "No requirements were extracted; cannot generate verdicts "
            "for an empty requirements list."
        )
    collection_name = state["collection_name"]
    sends = []
    for requirement in requirements:
        sends.append(
            Send(
                "generate_verdict_node",
                {
                    "requirement": requirement,
                    "collection_name": collection_name,
                },
            )
        )
    return sends


def generate_verdict_node(
    state: RequirementVerdictInput,
) -> dict[str, list[Verdict] | list[RetrievedContextRecord]]:
    requirement = state["requirement"]
    context_chunks = retrieve_context_chunks(
        requirement.text, state["collection_name"]
    )
    retrieved_context_record = RetrievedContextRecord(
        requirement_id=requirement.requirement_id,
        retrieved_context=context_chunks,
    )
    if not requirement.is_text_verifiable:
        return {"retrieved_context": [retrieved_context_record]}
    verdict = generate_verdict(requirement, context_chunks)
    return {
        "verdicts": [verdict],
        "retrieved_context": [retrieved_context_record],
    }


def build_report_node(state: PipelineState) -> dict[str, str]:
    report_text = build_report(state["requirements"], state["verdicts"])
    return {"report": report_text}


def _get_checkpointer() -> SqliteSaver:
    connection = sqlite3.connect(
        CHECKPOINT_DATABASE_PATH, check_same_thread=False
    )
    return SqliteSaver(connection)


def _register_nodes(builder: StateGraph) -> None:
    builder.add_node("split_requirements_node", split_requirements_node)
    builder.add_node(
        "extract_requirements_node", extract_requirements_node
    )
    builder.add_node(
        "deduplicate_requirements_node", deduplicate_requirements_node
    )
    builder.add_node("extract_conditions_node", extract_conditions_node)
    builder.add_node("index_application_node", index_application_node)
    builder.add_node("generate_verdict_node", generate_verdict_node)
    builder.add_node("build_report_node", build_report_node)


def _register_edges(builder: StateGraph) -> None:
    builder.add_edge(START, "split_requirements_node")
    builder.add_conditional_edges(
        "split_requirements_node",
        route_to_extraction,
        ["extract_requirements_node"],
    )
    builder.add_edge(
        "extract_requirements_node", "deduplicate_requirements_node"
    )
    builder.add_edge(
        "deduplicate_requirements_node", "extract_conditions_node"
    )
    builder.add_edge(
        "extract_conditions_node", "index_application_node"
    )
    builder.add_conditional_edges(
        "index_application_node",
        route_to_verdicts,
        ["generate_verdict_node"],
    )
    builder.add_edge("generate_verdict_node", "build_report_node")
    builder.add_edge("build_report_node", END)


def build_graph() -> CompiledStateGraph:
    builder = StateGraph(PipelineState)
    _register_nodes(builder)
    _register_edges(builder)
    logger.info("Compiled pipeline graph")
    checkpointer = _get_checkpointer()
    return builder.compile(checkpointer=checkpointer)
