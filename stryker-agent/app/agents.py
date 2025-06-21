import os
import json
import re # Import the regular expression module
import textwrap 
import subprocess
import traceback
from jinja2 import Environment, FileSystemLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.string import StrOutputParser
from state import AgentState, SurvivedMutation, GeneratedTest
from tools import read_file, find_test_file, write_file, GitTool, GitHubApiTool

# --- Initialize Gemini Model ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.2)

# --- Helper function to clean LLM output ---
def _extract_csharp_code(raw_output: str) -> str:
    """
    Extracts C# code from a raw LLM output string.
    It looks for a ```csharp ... ``` block and returns its content.
    If no block is found, it assumes the entire string is the code.
    """
    # Regex to find code inside ```csharp ... ```, handling potential newlines
    match = re.search(r"```csharp\s*(.*?)\s*```", raw_output, re.DOTALL)
    if match:
        # If a markdown block is found, return its content, stripped of whitespace
        return match.group(1).strip()
    else:
        # Otherwise, assume the entire raw output is the code and strip it
        return raw_output.strip()

def mutation_runner_agent(state: AgentState) -> AgentState:
    print("--- AGENT: Running Mutation Tests ---")
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

        # Always print the output for debugging
        print("--- Stryker STDOUT ---")
        print(result.stdout)
        print("--- Stryker STDERR ---")
        if result.stderr:
            print(result.stderr)
        print("----------------------")

        # --- REVISED LOGIC: Prioritize finding the report file ---
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
        
        # Now, check if we found what we need
        if found_report_path:
            # SUCCESS! We have the report, so we can continue.
            print(f"✅ Stryker report found at: {found_report_path}")
            state["stryker_report_path"] = found_report_path
        else:
            # FAILURE! The report was not generated.
            # Now we create a detailed error message.
            state["error_message"] = (
                "Stryker run did not produce a 'stryker-report.json' file. "
                f"Stryker exited with code {result.returncode}. "
                "Please check the STDOUT and STDERR logs above for details."
            )

    except Exception as e:
        state["error_message"] = f"An unexpected error occurred in the mutation runner: {str(e)}"
    
    return state

def report_analyst_agent(state: AgentState) -> AgentState:
    print("--- AGENT: Analyzing Report ---")
    if state.get("error_message"): return state
    
    report_content = json.loads(read_file.invoke(state["stryker_report_path"]))
    state["mutation_score"] = report_content.get("mutationScore", 0.0)
    
    survived: list[SurvivedMutation] = []
    for file_path, file_report in report_content.get("files", {}).items():
        relative_path = os.path.relpath(file_path, "/repo")
        source_context = read_file.invoke(relative_path)
        source_lines = source_context.splitlines()
        
        for mutant in file_report.get("mutants", []):
            if mutant["status"] == "Survived":
                start_line = mutant["location"]["start"]["line"]
                end_line = mutant["location"]["end"]["line"]
                # Adjust for 0-based list indexing and slice to get the relevant lines
                original_code_lines = source_lines[start_line - 1 : end_line]
                original_code = "\n".join(original_code_lines)

                survived.append({
                    "file_path": relative_path,
                    "mutator_name": mutant["mutatorName"],
                    "original_code": original_code,  # Use the correctly extracted code
                    "mutated_code": mutant["replacement"], # This key is correct
                    "location": mutant["location"],
                    "source_code_context": source_context
                })

    state["survived_mutations"] = survived
    print(f"Analysis complete. Mutation Score: {state['mutation_score']}. Survived: {len(survived)}")
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
                "mutator_name": mutation["mutator_name"], # Provide mutator for context
                "line": mutation["location"]["start"]["line"]
            }
            
            # Check for empty or None values that could cause an invalid request
            if not all(prompt_data.values()):
                print("ERROR: One of the prompt variables is empty. Skipping this mutation.")
                continue

            # The fix is in the system prompt below
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a C# expert specializing in writing concise, effective unit tests using xUnit.
Your goal is to write a single, complete C# xUnit test method to kill a specific mutation.

**Instructions:**
1.  **Unique Naming:** The test method MUST have a unique and descriptive name that follows the `MethodName_Scenario_ExpectedBehavior` convention. For example: `Calculate_WhenInputIsNegative_ThrowsException`. Use the mutator type to help describe the scenario.
2.  **Correctness:** The test must use assertions that would FAIL with the mutated code but PASS with the original code.
3.  **Format:** Do NOT provide any explanation, comments, or surrounding text. Output ONLY the raw C# code for the new method, starting with `[Fact]` or `[Theory]` and ending with the closing brace `}}`."""),
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
                Please provide one new, complete xUnit test method to kill this mutation.
                """)]
            )
            
            chain = prompt | llm | StrOutputParser()
            raw_llm_output = chain.invoke(prompt_data)

            # --- ADDED CLEANUP AND VALIDATION STEP ---
            new_test_code = _extract_csharp_code(raw_llm_output)

            if not new_test_code:
                print(f"ERROR: LLM returned an empty or invalid code block for mutation in {mutation['file_path']}. Skipping.")
                continue

            generated_tests.append({
                "target_test_file": target_test_file,
                "generated_test_code": new_test_code
            })
            print(f"✅ Successfully generated test for mutation in {mutation['file_path']}")
        except Exception as e:
            print(f"ERROR: Failed to generate test for {mutation['file_path']} due to: {e}")

    state["generated_tests"] = generated_tests
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
                # --- CORRECTED INDENTATION LOGIC ---
                # Define the standard indentation (4 spaces is a common C# standard)
                indentation = "    "
                
                # Indent every line of the generated test code
                indented_test_code = textwrap.indent(test["generated_test_code"], indentation)

                # Insert the correctly indented code block
                new_content = (
                    content[:last_brace_index].rstrip() + # Get content before the last brace
                    f"\n\n{indented_test_code}\n" +      # Add a blank line and the new indented method
                    content[last_brace_index:]           # Add the final brace back
                )
                
                write_file.invoke({
                    "file_path": file_path,
                    "content": new_content
                })
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
    
    # Add the built-in zip function to the template environment
    env.globals['zip'] = zip
    
    template = env.get_template('report_template.html')
    
    html_output = template.render(state=state)
    
    with open("/repo/mutation-dashboard.html", "w") as f:
        f.write(html_output)
    print("Dashboard 'mutation-dashboard.html' created successfully.")
    return state
