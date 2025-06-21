from typing import TypedDict, List, Optional, Dict

class UnfixedMutation(TypedDict):
    file_path: str
    mutator_name: str
    status: str # e.g., "NoCoverage", "Survived"
    line: int
    original_code: str
    mutated_code: str

class GeneratedTest(TypedDict):
    target_test_file: str
    generated_test_code: str
    explanation: str

class MutationStats(TypedDict):
    total_mutants: int
    killed: int
    survived: int
    no_coverage: int
    compile_error: int

class AgentState(TypedDict):
    # Inputs
    project_path: str
    repo_slug: str
    source_branch: str
    pr_number: int

    # Core State
    stryker_report_path: Optional[str]
    mutation_score: float
    survived_mutations: List[Dict] # Using Dict for flexibility with 'ai_reason'
    generated_tests: List[GeneratedTest]
    new_branch_name: Optional[str]
    new_pr_url: Optional[str]
    error_message: Optional[str]
    
    # --- NEW INTELLIGENCE & REPORTING FIELDS ---
    mutation_stats: Optional[MutationStats]
    survived_by_mutator: Optional[Dict[str, int]]
    
    # For "Projected Impact"
    projected_score: Optional[float]
    
    # For "Mission Log"
    mission_log: List[str]
    
    # For "Mutation Workbench"
    unfixed_mutants: List[UnfixedMutation]
