"""
demo_rate_abuse.py — Rate abuse demonstration.

An agent makes an excessive number of database queries in a short
time window, exceeding the rate limit defined in the behavior profile.

Expected result: RATE ABUSE alerts fire after the 10th call.

Owner: Member 1
"""

from logger import EventLogger
from detector import Detector
from alerter import Alerter
from agent import run_agent_manual


def main():
    print("=" * 60)
    print("  DEMO: Rate Abuse Scenario")
    print("=" * 60)
    print()
    print("Scenario: Agent rapidly queries the database 15 times within")
    print("seconds, exceeding the rate limit of 10 calls per 60 seconds.")
    print("This pattern may indicate automated data harvesting or a")
    print("stuck/compromised agent loop.")
    print()

    # Initialize components
    logger = EventLogger(db_path="demo_rate_events.db")
    logger.clear()
    detector = Detector("profiles/support_agent.yaml")
    alerter = Alerter(alert_db_path=None)

    # Generate 15 rapid query_db calls (profile limit: 10 per 60s)
    steps = []
    for i in range(15):
        steps.append((
            "query_db",
            {"table": "tickets", "query": f"SELECT * WHERE id='T-{100 + i}'"}
        ))

    print(f"Running {len(steps)} rapid query_db calls:\n")
    alerts = run_agent_manual(
        task_id="rate-demo-1",
        agent_identity="support-agent-v3",
        steps=steps,
        logger=logger,
        detector=detector,
        alerter=alerter,
    )

    # --- Results ---
    print()
    print("-" * 60)
    rate_alerts = [a for a in alerts if "RATE" in a.get("reason", "")]
    if rate_alerts:
        print(f"RESULT: {len(rate_alerts)} rate abuse alert(s) raised!")
        print(f"   First triggered after call #{10 + 1} (limit is 10/60s)")
    else:
        print("UNEXPECTED: No rate abuse alerts raised!")
    print()

    alerter.close()
    logger.close()


if __name__ == "__main__":
    main()
