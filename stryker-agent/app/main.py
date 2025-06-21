import os
import sys
from graph import create_graph
from state import AgentState

def find_main_project_file() -> str:
    csproj_files = []
    for root, _, files in os.walk("/repo"):
        for file in files:
            if file.endswith(".csproj"):
                csproj_files.append(os.path.join(root, file))
    non_test_projects = [p for p in csproj_files if "test" not in p.lower()]
    if len(non_test_projects) == 1:
        return os.path.relpath(non_test_projects[0], "/repo")
    elif len(non_test_projects) == 0:
        raise FileNotFoundError("Auto-discovery failed: No non-test .csproj file found.")
    else:
        raise FileNotFoundError(
            f"Auto-discovery failed: Found multiple non-test .csproj files. Found: {non_test_projects}"
        )

def main():
    try:
        project_path = find_main_project_file()
        print(f"✅ Automatically discovered project file: {project_path}")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
        
    initial_state: AgentState = {
        # Inputs
        "project_path": project_path,
        "repo_slug": os.environ["GITHUB_REPOSITORY"],
        "source_branch": os.environ["SOURCE_BRANCH"],
        "pr_number": int(os.environ["PR_NUMBER"]),
        # Core State
        "stryker_report_path": None,
        "mutation_score": 0.0,
        "survived_mutations": [],
        "generated_tests": [],
        "new_branch_name": None,
        "new_pr_url": None,
        "error_message": None,
        # New Reporting Fields
        "mutation_stats": None,
        "survived_by_mutator": None,
        "survived_by_file": None,
        "projected_score": None,
        "run_stats": None,
        "unfixed_mutants": [],
    }
    app = create_graph()
    app.invoke(initial_state)

if __name__ == "__main__":
    main()
