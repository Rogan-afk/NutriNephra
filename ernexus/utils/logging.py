import sys

def log(*args):
    print("[ER-NEXUS]", *args, file=sys.stderr)
