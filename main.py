import subprocess
import os
import re

APP_NAME = "YUNAY AI Agent"
VERSION = "0.3.0"
PROJECT_DIR = "/root/yunay-agent"


def ask_ai(message):
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
            timeout=180,
            cwd=PROJECT_DIR,
        )

        if result.returncode == 0:
            output = result.stdout.strip()
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
    print("\n📁 Project:", PROJECT_DIR)
    try:
        for name in sorted(os.listdir(PROJECT_DIR))[:30]:
            print(" -", name)
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

    # Kyunki OpenCode khud bhi files edit kar sakta hai, hum usko clear instruction denge
    prompt = (
        f"Create or update the file '{filename}' in the project directory for this task: {task}. "
        f"Also show the complete Python code inside a ```python ... ``` block."
    )

    response = ask_ai(prompt)

    # Agar OpenCode ne file khud nahi banayi, toh hum response se code nikaal kar save kar denge
    if response and not os.path.exists(filepath):
        code = extract_code(response)
        if code:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code + "\n")
            print(f"\n✅ File save ho gayi: {filepath}")
    elif os.path.exists(filepath):
        print(f"\n✅ '{filename}' project mein ready hai!")


def run_and_debug():
    filename = input("\nKaunsi Python file run karni hai? (e.g. calc.py): ").strip()
    if not filename:
        return

    filepath = os.path.join(PROJECT_DIR, filename)
    if not os.path.exists(filepath):
        print(f"\n❌ '{filename}' nahi mili! Option 2 se files check karo.")
        return

    print(f"\n🚀 Running {filename}...\n" + "-" * 35)
    try:
        # Interactive input support ke liye pehle normal run ya capture check
        result = subprocess.run(
            ["python", filepath],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=PROJECT_DIR,
        )

        if result.returncode == 0:
            print(result.stdout or "(No output)")
            print("-" * 35)
            print("✅ Code bina kisi error ke run hua!")
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            print("❌ Error aaya:\n", error_msg)
            print("-" * 35)

            fix = input("\n🔧 Kya AI se ye error automatic fix karwana hai? (y/n): ").strip().lower()
            if fix == "y":
                with open(filepath, "r", encoding="utf-8") as f:
                    old_code = f.read()

                fix_prompt = (
                    f"The file '{filename}' has the following code:\n```python\n{old_code}\n```\n\n"
                    f"When running it, this error occurred:\n{error_msg}\n\n"
                    f"Please fix the error in '{filename}' and also provide the full fixed code inside a ```python ... ``` block."
                )
                response = ask_ai(fix_prompt)
                if response:
                    fixed_code = extract_code(response)
                    if fixed_code:
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(fixed_code + "\n")
                        print(f"\n✅ '{filename}' mein error fix karke save kar diya gaya hai! Dobara Option 4 se run karein.")
    except subprocess.TimeoutExpired:
        print("\n⚠️ Program timeout ho gaya (Shayad code `input()` maang raha tha).")
        print("Interactive file chalane ke liye: Direct terminal mein `python " + filename + "` chalayein.")


def git_manager():
    print("\n--- 🐙 GitHub / Git Manager ---")
    print("1. Git Status dekho")
    print("2. Git Diff (Kya badla hai)")
    print("3. Auto Commit & Push")
    sub = input("Option chuno (1/2/3): ").strip()

    if sub == "1":
        subprocess.run(["git", "status"], cwd=PROJECT_DIR)
    elif sub == "2":
        subprocess.run(["git", "diff"], cwd=PROJECT_DIR)
    elif sub == "3":
        msg = input("Commit message likho (khali chhodne par default lagega): ").strip()
        if not msg:
            msg = "Updated project via YUNAY AI Agent"
        subprocess.run(["git", "add", "."], cwd=PROJECT_DIR)
        subprocess.run(["git", "commit", "-m", msg], cwd=PROJECT_DIR)
        push_q = input("Kya GitHub par push bhi karna hai? (y/n): ").strip().lower()
        if push_q == "y":
            subprocess.run(["git", "push"], cwd=PROJECT_DIR)


def show_menu():
    print("\n" + "=" * 38)
    print(f"  🤖 {APP_NAME} v{VERSION}")
    print("=" * 38)
    print("1. AI se baat karo (Chat)")
    print("2. Project ki files dekho")
    print("3. AI se Code File banwao / Edit karo")
    print("4. File Run karo & Error Auto-Fix karo")
    print("5. Git / GitHub Manager")
    print("6. Exit")


def main():
    print(f"\nNamaste! Main {APP_NAME} v{VERSION} hu.")
    print("AI Model: OpenCode configured model")

    while True:
        show_menu()
        choice = input("\nApna option chuno (1-6): ").strip()

        if choice == "1":
            message = input("\nTumhara sawal: ").strip()
            if message:
                ask_ai(message)
            else:
                print("Pehle sawal likho!")

        elif choice == "2":
            show_project_info()

        elif choice == "3":
            create_or_edit_file()

        elif choice == "4":
            run_and_debug()

        elif choice == "5":
            git_manager()

        elif choice == "6":
            print("\nYUNAY AI Agent band ho raha hai. Bye! 👋")
            break

        else:
            print("\n❌ Galat option! 1 se 6 ke beech chuno.")


if __name__ == "__main__":
    main()
