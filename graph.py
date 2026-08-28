import inspect
import logging

from langgraph.graph import END, START, StateGraph

from agents.evaluator import evaluator
from agents.planner import planner
from agents.publisher import publisher
from agents.reranker import reranker
from agents.researcher import researcher
from agents.writer import writer
from helpers.state import State

logger = logging.getLogger(__name__)


def _logged_node(name, node):
    async def run(state: State):
        logger.info("[%s] started", name)
        try:
            result = node(state)
            if inspect.isawaitable(result):
                result = await result
            logger.info("[%s] completed; current_step=%s", name, result.get("current_step", "unchanged"))
            return result
        except Exception:
            logger.exception("[%s] failed", name)
            raise

    return run


def build_graph():
    graph_builder = StateGraph(State)

    graph_builder.add_node("planner", _logged_node("planner", planner))
    graph_builder.add_node("researcher", _logged_node("researcher", researcher))
    graph_builder.add_node("reranker", _logged_node("reranker", reranker))
    graph_builder.add_node("writer", _logged_node("writer", writer))
    graph_builder.add_node("evaluator", _logged_node("evaluator", evaluator))
    graph_builder.add_node("publisher", _logged_node("publisher", publisher))

    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner","researcher")
    graph_builder.add_edge("researcher","reranker")
    graph_builder.add_edge("reranker","writer")
    graph_builder.add_edge("writer","evaluator")
    graph_builder.add_edge("evaluator","publisher")
    graph_builder.add_edge("publisher",END)


    return graph_builder.compile()
