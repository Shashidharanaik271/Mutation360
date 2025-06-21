from typing import TypedDict, List, Optional, Dict

class SurvivedMutation(TypedDict):
    file_path: str
    mutator_name: str
    original_code: str
    mutated_code: str
    location: dict
    source_code_context: str # Full source file content

class GeneratedTest(TypedDict):
    target_test_file: str
    generated_test_code: str
    explanation: str

# NEW: For detailed stats
class MutationStats(TypedDict):
    total_mutants: int
    killed: int
    survived: int
    no_coverage: int
    compile_error: int

class AgentState(TypedDict):
    # Inputs
    project_path: str
    repo_slug: str # e.g., "your-org/your-repo"
    source_branch: str
    pr_number: int

    # State
    stryker_report_path: Optional[str]
    mutation_score: float
    survived_mutations: List[SurvivedMutation]
    generated_tests: List[GeneratedTest]
    new_branch_name: Optional[str]
    new_pr_url: Optional[str]
    error_message: Optional[str]
    
    # NEW: Detailed reporting data
    mutation_stats: Optional[MutationStats]
    survived_by_mutator: Optional[Dict[str, int]]
