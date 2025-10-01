# scripts/demo_task.py
import argparse
import time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--msg", default="hello", help="출력할 메시지")
    p.add_argument("--sleep", type=float, default=0.5, help="실행 대기 시간(초)")
    args = p.parse_args()

    time.sleep(max(0.0, args.sleep))
    print(f"[demo_task] msg={args.msg}")

if __name__ == "__main__":
    main()
