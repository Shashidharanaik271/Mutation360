from typing import TypedDict, List, Optional, Dict

# NEW: Added the missing SurvivedMutation definition
class SurvivedMutation(TypedDict):
    file_path: str
    mutator_name: str
    original_code: str
    mutated_code: str
    location: Dict
    source_code_context: str

class UnfixedMutation(TypedDict):
    file_path: str
    mutator_name: str
    status: str # e.g., "NoCoverage", "Survived"
    line: int
    original_code: str
    mutated_code: str
    # For the workbench risk assessment
    risk_level: str # 'HIGH', 'MEDIUM', 'LOW'
    risk_icon: str # '🔥', '⚠️', '⚪'

class GeneratedTest(TypedDict):
    target_test_file: str
    generated_test_code: str
    # For the "Test Case Story"
    explanation: str

class MutationStats(TypedDict):
    total_mutants: int
    killed: int
    survived: int
    no_coverage: int
    compile_error: int

# For the performance stats widget
class RunStats(TypedDict):
    analysis_time_seconds: int
    mutants_generated: int
    survivors_found: int
    tests_generated: int

class AgentState(TypedDict):
    # Inputs
    project_path: str
    repo_slug: str
    source_branch: str
    pr_number: int

    # Core State
    stryker_report_path: Optional[str]
    mutation_score: float
    # UPDATED: Changed from List[Dict] to the new, specific type
    survived_mutations: List[SurvivedMutation] 
    generated_tests: List[GeneratedTest]
    new_branch_name: Optional[str]
    new_pr_url: Optional[str]
    error_message: Optional[str]
    
    # --- NEW INTELLIGENCE & REPORTING FIELDS ---
    mutation_stats: Optional[MutationStats]
    survived_by_mutator: Optional[Dict[str, int]]
    
    # For the "File Hotspots" chart
    survived_by_file: Optional[Dict[str, int]]
    
    # For the "Projected Impact" scorecard
    projected_score: Optional[float]
    
    # For the top performance widget
    run_stats: Optional[RunStats]
    
    # For the "Mutation Workbench"
    unfixed_mutants: List[UnfixedMutation]
