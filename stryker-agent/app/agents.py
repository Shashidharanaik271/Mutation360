import os
import json
import re # Import the regular expression module
import textwrap 
import subprocess
import traceback
from collections import Counter # Add this import at the top of agents.py
from jinja2 import Environment, FileSystemLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.string import StrOutputParser
from state import AgentState, SurvivedMutation, GeneratedTest
from tools import read_file, find_test_file, write_file, GitTool, GitHubApiTool
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# --- Initialize Gemini Model ---
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.2)

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
    
    # --- NEW: Detailed stat collection ---
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
    # --- END NEW ---

    survived: list[SurvivedMutation] = []
    survived_mutator_names = []
    for file_path, file_report in report_content.get("files", {}).items():
        relative_path = os.path.relpath(file_path, "/repo")
        source_context = read_file.invoke(relative_path)
        source_lines = source_context.splitlines()
        
        for mutant in file_report.get("mutants", []):
            if mutant["status"] == "Survived":
                start_line = mutant["location"]["start"]["line"]
                end_line = mutant["location"]["end"]["line"]
                original_code_lines = source_lines[start_line - 1 : end_line]
                original_code = "\n".join(original_code_lines)

                survived.append({
                    "file_path": relative_path,
                    "mutator_name": mutant["mutatorName"],
                    "original_code": original_code,
                    "mutated_code": mutant["replacement"],
                    "location": mutant["location"],
                    "source_code_context": source_context
                })
                survived_mutator_names.append(mutant["mutatorName"])

    state["survived_mutations"] = survived
    # --- NEW: Count survived mutants by type ---
    state["survived_by_mutator"] = Counter(survived_mutator_names)
    
    print(f"Analysis complete. Mutation Score: {state['mutation_score']}. Survived: {len(survived)}")
    print(f"Detailed Stats: {state['mutation_stats']}")
    return state

# NEW: Define the desired JSON output structure for the LLM
class TestAndExplanation(BaseModel):
    test_code: str = Field(description="The complete, raw C# xUnit test method code, starting with [Fact] or [Theory].")
    explanation: str = Field(description="A concise, step-by-step explanation of why this new test kills the mutation. Explain the specific scenario and the assertion.")

def test_generator_agent(state: AgentState) -> AgentState:
    print("--- AGENT: Generating Unit Tests with Explanations ---")
    if state.get("error_message"): return state
    
    # Initialize the JSON parser to guarantee structured output
    parser = JsonOutputParser(pydantic_object=TestAndExplanation)

    generated_tests: list[GeneratedTest] = []
    for mutation in state["survived_mutations"]:
        target_test_file = find_test_file.invoke(mutation["file_path"])
        
        if target_test_file is None:
            print(f"INFO: No corresponding test file found for {mutation['file_path']}. Skipping.")
            continue
        
        try:
            existing_tests = read_file.invoke(target_test_file)
            
            print(f"--- Preparing to generate test & story for {mutation['file_path']} ---")
            
            # UPGRADED PROMPT: Now asks for a JSON object with a specific format
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a C# testing expert. Your task is to write a new xUnit test to kill a mutation AND explain your reasoning.
You must provide your response in a JSON format with two keys: "test_code" and "explanation".

- "test_code": The complete, raw C# test method code. Follow the `MethodName_Scenario_ExpectedBehavior` naming convention.
- "explanation": A short, clear narrative. Describe the specific edge case the original tests missed and how the new assertion explicitly covers that vulnerability."""),
                ("user", """
                **Source File:** `{file_path}`
                **Existing Test File Content:**
                ```csharp
                {existing_tests}
                ```
                ---
                **Mutation to Kill**
                - **Original Code:** `{original_code}`
                - **Mutated Code (that survived):** `{mutated_code}`
                - **Mutator Type:** `{mutator_name}`
                ---
                Please provide the JSON object containing the new test and its explanation.
                """)]
            )
            
            chain = prompt | llm | parser
            
            ai_response = chain.invoke({
                "file_path": mutation["file_path"],
                "existing_tests": existing_tests,
                "original_code": mutation["original_code"],
                "mutated_code": mutation["mutated_code"],
                "mutator_name": mutation["mutator_name"]
            })

            cleaned_code = _extract_csharp_code(ai_response["test_code"])

            if not cleaned_code:
                print(f"ERROR: LLM returned an empty code block. Skipping.")
                continue

            # Append the new structured data to our state
            generated_tests.append({
                "target_test_file": target_test_file,
                "generated_test_code": cleaned_code,
                "explanation": ai_response["explanation"]
            })
            print(f"✅ Successfully generated test and story for mutation in {mutation['file_path']}")
        except Exception as e:
            print(f"ERROR: Failed to generate test story for {mutation['file_path']} due to: {e}")

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
