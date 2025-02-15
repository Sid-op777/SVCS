import argparse

def init():
    print("Initializing repository")
    pass

def status():
    print("Showing status")
    pass

def commit(message):
    print("Committing changes")
    pass

def log():
    print("Showing log")
    pass

def diff(commit_id):
    print("Showing diff")
    pass

def checkout(commit_id):
    print("Checking out commit")
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Very Simplified VCS")
    parser.add_argument("command", choices=["init", "status", "commit", "log", "diff", "checkout"])
    parser.add_argument("message", nargs="?", help="Commit message or commit ID")
    args = parser.parse_args()

    if args.command == "init":
        init()
    elif args.command == "status":
        status()
    elif args.command == "commit":
        commit(args.message)
    elif args.command == "log":
        log()
    elif args.command == "diff":
        diff(args.message)
    elif args.command == "checkout":
        checkout(args.message)
