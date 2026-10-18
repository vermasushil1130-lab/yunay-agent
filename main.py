import subprocess
import os
import re

APP_NAME = "YUNAY AI Agent"
VERSION = "1.0.0"
PROJECT_DIR = "/root/yunay-agent"
MAX_FIX_ATTEMPTS = 3


def ask_ai(message, silent=False):
    if not silent:
        print("\n⏳ DeepSeek AI soch raha hai...")

    try:
        result = subprocess.run(
            [
                "opencode",
                "run",
                "--dir",
                PROJECT_DIR,
                message,
            ],
            capture_output=True,
            text=True,
            timeout=240,
            cwd=PROJECT_DIR,
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            if not silent:
                print("\n🤖 YUNAY AI:")
                print(output)
            return output
        else:
            err = result.stderr.strip() or result.stdout.strip()
            print("\n❌ OpenCode error:")
            print(err)
            return None

    except subprocess.TimeoutExpired:
        print("\n⏳ Jawab aane mein zyada samay laga (Timeout)!")
        return None
    except FileNotFoundError:
        print("\n❌ OpenCode command nahi mili!")
        return None


def extract_code(text):
    pattern = r"```(?:python)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()
    return None


def show_project_info():
    print("\n📁 Project Directory:", PROJECT_DIR)
    try:
        for root, dirs, files in os.walk(PROJECT_DIR):
            dirs[:] = [d for d in dirs if d not in [".git", ".venv", "__pycache__"]]
            level = root.replace(PROJECT_DIR, "").count(os.sep)
            indent = "  " * level
            folder_name = os.path.basename(root) or "yunay-agent"
            print(f"{indent}📂 {folder_name}/")
            subindent = "  " * (level + 1)
            for f in sorted(files)[:25]:
                if not f.startswith("main_backup"):
                    print(f"{subindent}📄 {f}")
    except OSError as error:
        print("Error:", error)


def create_or_edit_file():
    filename = input("\nFile ka naam likho (e.g. calc.py): ").strip()
    if not filename:
        print("❌ File ka naam zaroori hai!")
        return

    task = input("Is file mein kya banwana ya badalna hai?: ").strip()
    if not task:
        print("❌ Task batana zaroori hai!")
        return

    filepath = os.path.join(PROJECT_DIR, filename)

    prompt = (
        f"Create or update the file '{filename}' in the project directory for this task: {task}. "
        f"Also provide the complete Python code inside a ```python ... ``` block."
    )

    response = ask_ai(prompt)

    if response:
        code = extract_code(response)
        if code:
            os.makedirs(os.path.dirname(filepath) or PROJECT_DIR, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code + "\n")
            print(f"\n✅ '{filename}' save ho gayi hai!")


def build_multi_file_project():
    print("\n--- 🏗️ AI Multi-File Project Architect ---")
    proj_name = input("Naye sub-project folder ka naam (e.g. notes_app): ").strip()
    if not proj_name:
        print("❌ Folder ka naam zaroori hai!")
        return

    idea = input("Project mein kya-kya hona chahiye? Detail batao: ").strip()
    if not idea:
        print("❌ Project idea batana zaroori hai!")
        return

    target_dir = os.path.join(PROJECT_DIR, proj_name)
    os.makedirs(target_dir, exist_ok=True)

    prompt = (
        f"Create a complete, modular multi-file Python project inside the folder '{proj_name}' for this idea: {idea}.\n"
        f"Create at least 2-3 files (for example: '{proj_name}/main.py', '{proj_name}/helper.py', '{proj_name}/README.md').\n"
        f"Directly write the files to disk in '{proj_name}/', and also output each file clearly in this exact format:\n"
        f"### FILE: {proj_name}/filename.ext\n```python\n...code...\n```"
    )

    response = ask_ai(prompt)

    if response:
        # Fallback parser agar AI response mein files bhejta hai
        pattern = r"### FILE:\s*([^\n]+)\n```[a-zA-Z]*\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        for rel_path, content in matches:
            rel_path = rel_path.strip().strip("`'\"")
            full_path = os.path.join(PROJECT_DIR, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            print(f"📄 Saved: {rel_path}")

    print(f"\n✅ Multi-file project '{proj_name}' ready hai! Option 2 se tree structure dekhein.")


def auto_install_missing_module(error_text):
    match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_text)
    if match:
        mod_name = match.group(1).split(".")[0]
        print(f"\n📦 Missing library mili: '{mod_name}'. Auto-installing...")
        res = subprocess.run(["pip", "install", mod_name], cwd=PROJECT_DIR)
        if res.returncode == 0:
            print(f"✅ '{mod_name}' install ho gayi!")
            return True
    return False


def run_and_debug():
    filename = input("\nKaunsi Python file run karni hai? (e.g. test_app.py ya notes_app/main.py): ").strip()
    if not filename:
        return

    filepath = os.path.join(PROJECT_DIR, filename)
    if not os.path.exists(filepath):
        print(f"\n❌ '{filename}' nahi mili! Option 2 se files check karo.")
        return

    attempt = 1
    while attempt <= MAX_FIX_ATTEMPTS:
        print(f"\n🚀 Running {filename} (Attempt {attempt}/{MAX_FIX_ATTEMPTS})...\n" + "-" * 40)
        try:
            result = subprocess.run(
                ["python", filepath],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=PROJECT_DIR,
            )

            if result.returncode == 0:
                print(result.stdout or "(No output)")
                print("-" * 40)
                print(f"✅ Super! '{filename}' bina kisi error ke run hua!")
                return
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                print("❌ Error aaya:\n", error_msg)
                print("-" * 40)

                if auto_install_missing_module(error_msg):
                    print("🔄 Module install hone ke baad dobara run kar rahe hain...")
                    continue

                if attempt < MAX_FIX_ATTEMPTS:
                    print(f"\n🔧 AI khud error fix kar raha hai (Auto-Heal Attempt {attempt})...")
                    with open(filepath, "r", encoding="utf-8") as f:
                        old_code = f.read()

                    fix_prompt = (
                        f"The Python file '{filename}' has this code:\n```python\n{old_code}\n```\n\n"
                        f"Running it produced this error:\n{error_msg}\n\n"
                        f"Fix the bug in '{filename}' and return the full corrected Python code inside a ```python ... ``` block."
                    )
                    response = ask_ai(fix_prompt)
                    if response:
                        fixed_code = extract_code(response)
                        if fixed_code:
                            with open(filepath, "w", encoding="utf-8") as f:
                                f.write(fixed_code + "\n")
                            print(f"✅ '{filename}' update ho gayi! Ab dobara test kar rahe hain...")
                            attempt += 1
                            continue

                print("\n⚠️ Max attempts poore ho gaye. Manual check ki zaroorat hai.")
                return

        except subprocess.TimeoutExpired:
            print("\n⚠️ Program timeout ho gaya (Shayad code user input maang raha hai).")
            return


def git_manager():
    print("\n--- 🐙 Smart GitHub Manager ---")
    print("1. Git Status dekho")
    print("2. Git Diff dekho")
    print("3. 🤖 AI Smart Commit & Push (Automatic)")
    sub = input("Option chuno (1/2/3): ").strip()

    if sub == "1":
        subprocess.run(["git", "status"], cwd=PROJECT_DIR)
    elif sub == "2":
        subprocess.run(["git", "diff"], cwd=PROJECT_DIR)
    elif sub == "3":
        subprocess.run(["git", "add", "."], cwd=PROJECT_DIR)
        diff_res = subprocess.run(
            ["git", "diff", "--cached", "--stat"],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
        )
        diff_text = diff_res.stdout.strip()
        if not diff_text:
            print("\nℹ️ Koi naya change nahi mila commit karne ke liye!")
            return

        print("\n⏳ AI changes dekh kar Commit Message bana raha hai...")
        msg_prompt = (
            f"Generate a short, clean 1-line git commit message (e.g. 'feat: added multi-file project builder') "
            f"for these file changes:\n{diff_text}\nReturn ONLY the commit message text without quotes."
        )
        ai_msg = ask_ai(msg_prompt, silent=True)
        commit_msg = ai_msg.splitlines()[-1].strip().strip('"`\'') if ai_msg else f"feat: updated via YUNAY AI Agent v{VERSION}"

        print(f"📝 AI Commit Message: {commit_msg}")
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=PROJECT_DIR)

        push_q = input("\n🚀 Kya abhi GitHub par push karein? (y/n): ").strip().lower()
        if push_q == "y":
            subprocess.run(["git", "push", "origin", "main"], cwd=PROJECT_DIR)


def show_menu():
    print("\n" + "=" * 44)
    print(f"  🤖 {APP_NAME} v{VERSION} (Project Architect)")
    print("=" * 44)
    print("1. AI se baat karo (Chat)")
    print("2. Project File Tree dekho")
    print("3. Single File banwao / Edit karo")
    print("4. 🏗️ AI Multi-File Project Builder (New!)")
    print("5. File Run & Auto-Heal (3x Auto Bug Fix)")
    print("6. Smart GitHub Manager (AI Commit & Push)")
    print("7. 🌐 Launch YUNAY Web Coding Studio (Browser UI)")
    print("8. Exit")


def main():
    print(f"\nNamaste! Main {APP_NAME} v{VERSION} hu.")
    while True:
        show_menu()
        choice = input("\nApna option chuno (1-7): ").strip()

        if choice == "1":
            message = input("\nTumhara sawal: ").strip()
            if message:
                ask_ai(message)
        elif choice == "2":
            show_project_info()
        elif choice == "3":
            create_or_edit_file()
        elif choice == "4":
            build_multi_file_project()
        elif choice == "5":
            run_and_debug()
        elif choice == "6":
            git_manager()
        elif choice == "7":
            import studio
            studio.start_studio()
        elif choice == "8":
            print("\nYUNAY AI Agent band ho raha hai. Bye! 👋")
            break
        else:
            print("\n❌ Galat option! 1 se 7 ke beech chuno.")


if __name__ == "__main__":
    main()
