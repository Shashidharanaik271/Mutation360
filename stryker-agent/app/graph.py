from langgraph.graph import StateGraph, END
from state import AgentState
from agents import (
    mutation_runner_agent,
    report_analyst_agent,
    test_generator_agent,
    code_integration_agent,
    dashboard_generator_agent
)

def should_generate_tests(state: AgentState) -> str:
    if state.get("error_message"):
        print("Error detected. Routing to dashboard generation.")
        return "generate_dashboard"
    if not state.get("survived_mutations"):
        print("No survived mutations. Routing to dashboard generation.")
        return "generate_dashboard"
    return "generate_tests"

def create_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("run_mutation_test", mutation_runner_agent)
    workflow.add_node("analyze_report", report_analyst_agent)
    workflow.add_node("generate_tests", test_generator_agent)
    workflow.add_node("integrate_code_and_create_pr", code_integration_agent)
    workflow.add_node("generate_dashboard", dashboard_generator_agent)
    workflow.set_entry_point("run_mutation_test")
    workflow.add_edge("run_mutation_test", "analyze_report")
    workflow.add_conditional_edges(
        "analyze_report",
        should_generate_tests,
        {
            "generate_tests": "generate_tests",
            "generate_dashboard": "generate_dashboard"
        }
    )
    workflow.add_edge("generate_tests", "integrate_code_and_create_pr")
    workflow.add_edge("integrate_code_and_create_pr", "generate_dashboard")
    workflow.add_edge("generate_dashboard", END)
    return workflow.compile()
