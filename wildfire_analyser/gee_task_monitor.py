# python3 -m wildfire_analyser.gee_task_monitor \
#   --gee-task-id GWPUZIDAD4TGMXCLWOJNBRFT \
#   --deliverable DNBR \
#   --user-email user@email.com

import argparse
import time
import ee

from wildfire_analyser.fire_assessment.auth import authenticate_gee

POLL_INTERVAL_SECONDS = 15


def wait_for_task(gee_task_id: str):
    while True:
        statuses = ee.data.getTaskStatus(gee_task_id)

        if not statuses:
            raise RuntimeError(f"Task {gee_task_id} not found")

        status = statuses[0]
        state = status["state"]

        print(f"[GEE] task={gee_task_id} state={state}")

        if state == "COMPLETED":
            return

        if state in ("FAILED", "CANCELLED"):
            error = status.get("error_message", "Unknown error")
            raise RuntimeError(f"Task failed: {error}")

        time.sleep(POLL_INTERVAL_SECONDS)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor a Google Earth Engine task until completion"
    )

    parser.add_argument("--gee-task-id", required=True)
    parser.add_argument("--deliverable", required=True)
    parser.add_argument("--user-email", required=True)

    args = parser.parse_args()

    authenticate_gee()

    wait_for_task(args.gee_task_id)

    print(f"Deliverable '{args.deliverable}' completed.")
    print(f"User: {args.user_email}")
    print("Email sending not implemented yet.")


if __name__ == "__main__":
    main()
