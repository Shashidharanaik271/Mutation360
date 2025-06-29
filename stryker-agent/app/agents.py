import os
import json
import re
import textwrap
import subprocess
import traceback
import time # NEW: For timing the run
from collections import Counter
from jinja2 import Environment, FileSystemLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser # NEW: For structured output
from state import AgentState, SurvivedMutation, GeneratedTest, UnfixedMutation
from tools import read_file, find_test_file, write_file, GitTool, GitHubApiTool

# --- Initialize Gemini Model ---
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.2)

# --- Helper function to clean LLM output (NO LONGER NEEDED FOR TEST GEN) ---
# We will use JSON output parser instead for more robust extraction.

def mutation_runner_agent(state: AgentState) -> AgentState:
    print("--- AGENT: Running Mutation Tests ---")
    state['run_stats'] = { "analysis_time_seconds": 0 } # Initialize
    start_time = time.time()
    try:
        command = [
            "dotnet", "stryker",
            "--project", state["project_path"],
            "--config-file", "stryker-config.json"
        ]
        print(f"Executing command: {' '.join(command)}")

        result = subprocess.run(
            command,
            cwd="/repo", capture_output=True, text=True
        )

        print("--- Stryker STDOUT ---")
        print(result.stdout)
        print("--- Stryker STDERR ---")
        if result.stderr:
            print(result.stderr)
        print("----------------------")

        report_file_name = "stryker-report.json"
        stryker_output_dir = "/repo/StrykerOutput"
        found_report_path = None

        print(f"Searching for '{report_file_name}' in '{stryker_output_dir}'...")
        if os.path.exists(stryker_output_dir):
            for root, _, files in os.walk(stryker_output_dir):
                if report_file_name in files:
                    full_path = os.path.join(root, report_file_name)
                    found_report_path = os.path.relpath(full_path, "/repo")
                    break
        
        if found_report_path:
            print(f"✅ Stryker report found at: {found_report_path}")
            state["stryker_report_path"] = found_report_path
        else:
            state["error_message"] = (
                "Stryker run did not produce a 'stryker-report.json' file. "
                f"Stryker exited with code {result.returncode}. "
                "Please check the STDOUT and STDERR logs above for details."
            )

    except Exception as e:
        state["error_message"] = f"An unexpected error occurred in the mutation runner: {str(e)}"
    finally:
        end_time = time.time()
        state['run_stats']['analysis_time_seconds'] = int(end_time - start_time)
    
    return state

def _assess_risk(mutator_name: str) -> tuple[str, str]:
    """Assigns a risk level based on the mutator type."""
    high_risk = ["Block", "Statement", "Linq", "Equality", "Arithmetic"]
    if any(term in mutator_name for term in high_risk):
        return ('HIGH', '🔥')
    
    medium_risk = ["Method", "Update", "Boolean"]
    if any(term in mutator_name for term in medium_risk):
        return ('MEDIUM', '⚠️')
        
    return ('LOW', '⚪')

def report_analyst_agent(state: AgentState) -> AgentState:
    print("--- AGENT: Analyzing Report ---")
    if state.get("error_message"): return state
    
    report_content = json.loads(read_file.invoke(state["stryker_report_path"]))
    state["mutation_score"] = report_content.get("mutationScore", 0.0)
    
    all_mutants = []
    for file_report in report_content.get("files", {}).values():
        all_mutants.extend(file_report.get("mutants", []))

    status_counts = Counter(m["status"] for m in all_mutants)
    
    state["mutation_stats"] = {
        "total_mutants": len(all_mutants),
        "killed": status_counts.get("Killed", 0),
        "survived": status_counts.get("Survived", 0),
        "no_coverage": status_counts.get("NoCoverage", 0),
        "compile_error": status_counts.get("CompileError", 0)
    }

    survived_mutations: list[SurvivedMutation] = []
    unfixed_mutants: list[UnfixedMutation] = []
    survived_mutator_names = []
    survived_file_paths = []

    for file_path, file_report in report_content.get("files", {}).items():
        relative_path = os.path.relpath(file_path, "/repo")
        source_context = read_file.invoke(relative_path)
        source_lines = source_context.splitlines()
        
        for mutant in file_report.get("mutants", []):
            start_line = mutant["location"]["start"]["line"]
            end_line = mutant["location"]["end"]["line"]
            original_code_lines = source_lines[start_line - 1 : end_line]
            original_code = "\n".join(original_code_lines)

            if mutant["status"] in ["Survived", "NoCoverage"]:
                risk_level, risk_icon = _assess_risk(mutant["mutatorName"])
                unfixed_mutants.append({
                    "file_path": relative_path,
                    "mutator_name": mutant["mutatorName"],
                    "status": mutant["status"],
                    "line": start_line,
                    "original_code": original_code,
                    "mutated_code": mutant["replacement"],
                    "risk_level": risk_level,
                    "risk_icon": risk_icon
                })

            if mutant["status"] == "Survived":
                survived_mutations.append({
                    "file_path": relative_path,
                    "mutator_name": mutant["mutatorName"],
                    "original_code": original_code,
                    "mutated_code": mutant["replacement"],
                    "location": mutant["location"],
                    "source_code_context": source_context
                })
                survived_mutator_names.append(mutant["mutatorName"])
                survived_file_paths.append(relative_path)

    state["survived_mutations"] = survived_mutations
    state["unfixed_mutants"] = unfixed_mutants
    state["survived_by_mutator"] = Counter(survived_mutator_names)
    state["survived_by_file"] = Counter(survived_file_paths)
    
    # --- NEW: Calculate Projected Score ---
    stats = state["mutation_stats"]
    valid_mutants = stats["total_mutants"] - stats["no_coverage"] - stats["compile_error"]
    if valid_mutants > 0:
        # The projected score assumes all 'Survived' mutants will be 'Killed'
        projected_killed = stats["killed"] + stats["survived"]
        state["projected_score"] = (projected_killed / valid_mutants) * 100
    else:
        state["projected_score"] = state["mutation_score"]

    print(f"Analysis complete. Survived: {len(survived_mutations)}. Unfixed: {len(unfixed_mutants)}")
    return state

def test_generator_agent(state: AgentState) -> AgentState:
    print("--- AGENT: Generating Unit Tests ---")
    if state.get("error_message"): return state

    generated_tests: list[GeneratedTest] = []
    for mutation in state["survived_mutations"]:
        target_test_file = find_test_file.invoke(mutation["file_path"])
        
        if target_test_file is None:
            print(f"INFO: No corresponding test file found for {mutation['file_path']}. Skipping.")
            continue
        
        try:
            existing_tests = read_file.invoke(target_test_file)
            
            print(f"--- Preparing to generate test for {mutation['file_path']} ---")
            prompt_data = {
                "file_path": mutation["file_path"],
                "existing_tests": existing_tests,
                "original_code": mutation["original_code"],
                "mutated_code": mutation["mutated_code"],
                "mutator_name": mutation["mutator_name"],
                "line": mutation["location"]["start"]["line"]
            }
            
            if not all(prompt_data.values()):
                print("ERROR: One of the prompt variables is empty. Skipping this mutation.")
                continue

            # NEW: Updated prompt for JSON output
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a C# expert specializing in writing concise, effective unit tests using xUnit.
Your goal is to write a single, complete C# xUnit test method to kill a specific mutation.

**Instructions:**
1.  **Analyze:** Understand why the mutated code was not caught by existing tests.
2.  **Explain:** Write a brief, one-sentence explanation for *why* this new test is necessary. Focus on the specific scenario or edge case it covers.
3.  **Code:** Write a single, complete C# xUnit test method. The method MUST have a unique and descriptive name.
4.  **Format:** Respond with a single JSON object containing two keys: "explanation" and "code". Do NOT output any other text or markdown.

Example Response:
```json
{{
  "explanation": "This test validates that the method correctly handles null input for the customer name, which was not previously covered.",
  "code": "[Fact]\\npublic void Calculate_WhenCustomerNameIsNull_ThrowsArgumentNullException()\\n{{\\n    // ... test code ...\\n}}"
}}
```"""),
                ("user", """
                **Source File:** `{file_path}`
                **Existing Test File Content (to ensure name is unique):**
                ```csharp
                {existing_tests}
                ```
                ---
                **Mutation to Kill**
                - **Original Code:** `{original_code}`
                - **Mutated Code (that survived):** `{mutated_code}`
                - **Mutator Type:** `{mutator_name}`
                - **Location:** Line {line}
                ---
                Please provide the JSON object containing the explanation and the new xUnit test method.
                """)]
            )
            
            # NEW: Using JSON output parser
            parser = JsonOutputParser()
            chain = prompt | llm | parser
            response_json = chain.invoke(prompt_data)

            if not response_json.get("code") or not response_json.get("explanation"):
                print(f"ERROR: LLM returned incomplete JSON for mutation in {mutation['file_path']}. Skipping.")
                continue

            generated_tests.append({
                "target_test_file": target_test_file,
                "generated_test_code": response_json["code"],
                "explanation": response_json["explanation"]
            })
            print(f"✅ Successfully generated test for mutation in {mutation['file_path']}")
        except Exception as e:
            print(f"ERROR: Failed to generate test for {mutation['file_path']} due to: {e}")

    state["generated_tests"] = generated_tests
    # NEW: Populate final run stat
    if state.get('run_stats'):
        state['run_stats']['tests_generated'] = len(generated_tests)
        state['run_stats']['mutants_generated'] = state['mutation_stats']['total_mutants']
        state['run_stats']['survivors_found'] = state['mutation_stats']['survived']

    return state

def code_integration_agent(state: AgentState) -> AgentState:
    print("--- AGENT: Integrating Code and Creating PR ---")
    if state.get("error_message") or not state.get("generated_tests"):
        if not state.get("generated_tests"):
            print("INFO: No new tests were generated. Skipping code integration.")
        return state

    branch_name = f"feature/stryker-fixes-pr-{state['pr_number']}"
    state["new_branch_name"] = branch_name
    
    try:
        print("--- Configuring Git user and safe directory ---")
        subprocess.run(["git", "config", "--global", "user.email", "stryker.agent@example.com"], cwd="/repo", check=True)
        subprocess.run(["git", "config", "--global", "user.name", "Stryker AI Agent"], cwd="/repo", check=True)
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", "/repo"], cwd="/repo", check=True)
        print("--- Git configuration complete. ---")

        GitTool.create_and_checkout_branch.invoke(branch_name)

        for test in state["generated_tests"]:
            file_path = test["target_test_file"]
            content = read_file.invoke(file_path)
            last_brace_index = content.rfind("}")

            if last_brace_index != -1:
                indentation = "    "
                indented_test_code = textwrap.indent(test["generated_test_code"], indentation)
                new_content = (
                    content[:last_brace_index].rstrip() +
                    f"\n\n{indented_test_code}\n" +
                    content[last_brace_index:]
                )
                write_file.invoke({ "file_path": file_path, "content": new_content })
            else:
                raise ValueError(f"Could not find closing brace in {file_path}")

        commit_message = f"feat: Add unit tests to kill {len(state['generated_tests'])} survived mutations"
        
        GitTool.add_commit_and_push.invoke({
            "branch_name": branch_name,
            "commit_message": commit_message
        })

        github_tool = GitHubApiTool(state["repo_slug"], os.environ["GITHUB_TOKEN"])
        pr_title = f"AI-Generated Tests for PR #{state['pr_number']}"
        pr_body = f"""
        This PR was automatically generated by the AI Mutation Testing Agent.
        
        It includes **{len(state['generated_tests'])}** new unit test(s) to improve the mutation score. These tests target mutations that survived the existing test suite.
        
        **Action Required:**
        Please review and merge this PR into your feature branch (`{state['source_branch']}`) to ensure your changes are robust before merging to `master`.
        """
        
        pr_url = github_tool.create_pull_request.func(
            github_tool,
            head_branch=branch_name,
            base_branch=state["source_branch"],
            title=pr_title,
            body=pr_body
        )

        state["new_pr_url"] = pr_url
        print(f"✅ Successfully created PR: {pr_url}")

    except Exception as e:
        state["error_message"] = f"Code integration failed: {str(e)}\n{traceback.format_exc()}"
    
    return state

def dashboard_generator_agent(state: AgentState) -> AgentState:
    print("--- AGENT: Generating Dashboard ---")
    env = Environment(loader=FileSystemLoader('/app/templates'))
    env.globals['zip'] = zip
    
    template = env.get_template('report_template.html')
    
    html_output = template.render(state=state)
    
    with open("/repo/mutation-dashboard.html", "w") as f:
        f.write(html_output)
    print("Dashboard 'mutation-dashboard.html' created successfully.")
    return state
