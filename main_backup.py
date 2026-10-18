import subprocess
import os

APP_NAME = "YUNAY AI Agent"
VERSION = "0.2.0"
PROJECT_DIR = "/root/yunay-agent"


def ask_ai(message):
    print("\n⏳ DeepSeek AI जवाब दे रहा है...")

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
            print("\n🤖 YUNAY AI:")
            print(result.stdout.strip())
        else:
            print("\n❌ OpenCode error:")
            print(result.stderr.strip() or result.stdout.strip())

    except subprocess.TimeoutExpired:
        print("\n⏳ जवाब आने में ज्यादा समय लगा।")
    except FileNotFoundError:
        print("\n❌ OpenCode command नहीं मिली।")


def show_menu():
    print("\n" + "=" * 35)
    print(f"  {APP_NAME} v{VERSION}")
    print("=" * 35)
    print("1. AI से बात करो")
    print("2. Project की जानकारी")
    print("3. Exit")


def show_project_info():
    print("\n📂 Project:", PROJECT_DIR)

    try:
        for name in os.listdir(PROJECT_DIR)[:20]:
            print(" -", name)
    except OSError as error:
        print("Error:", error)


def main():
    print(f"\nनमस्ते! मैं {APP_NAME} हूँ।")
    print("AI Model: OpenCode का configured model")

    while True:
        show_menu()
        choice = input("\nअपना option चुनो: ").strip()

        if choice == "1":
            message = input("\nतुम्हारा सवाल: ").strip()
            if message:
                ask_ai(message)
            else:
                print("पहले सवाल लिखो।")

        elif choice == "2":
            show_project_info()

        elif choice == "3":
            print("\nYUNAY AI Agent बंद हो रहा है।")
            break

        else:
            print("\nगलत option। 1, 2 या 3 चुनो।")


if __name__ == "__main__":
    main()
