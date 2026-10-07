"""
demo_benign.py — Benign scenario demonstration. (as provided by the user)
"""

from logger import EventLogger
from detector import Detector
from alerter import Alerter
from agent import run_agent_manual


def main():
    print("=" * 60)
    print("  DEMO: Benign Support Agent Scenario")
    print("=" * 60)
    print()

    logger = EventLogger(db_path="demo_benign_events.db")
    logger.clear()
    detector = Detector("profiles/support_agent.yaml")
    alerter = Alerter(alert_db_path=None)

    steps = [
        ("read_ticket",  {"ticket_id": "T-102"}),
        ("search_kb",    {"query": "login error 500"}),
        ("query_db",     {"table": "tickets", "query": "SELECT * WHERE id='T-102'"}),
        ("search_kb",    {"query": "password reset steps"}),
    ]

    print("Running agent steps:\n")
    alerts = run_agent_manual(
        task_id="benign-demo-1",
        agent_identity="support-agent-v3",
        steps=steps,
        logger=logger,
        detector=detector,
        alerter=alerter,
    )

    print()
    print("-" * 60)
    if not alerts:
        print("RESULT: No alerts raised — agent behavior is within profile.")
    else:
        print(f"UNEXPECTED: {len(alerts)} alert(s) raised during benign scenario!")
        for a in alerts:
            print(f"  [{a['severity']}] {a['reason']}")
    print()

    events = logger.get_events_by_task("benign-demo-1")
    print(f"Events logged: {len(events)}")
    for ev in events:
        print(f"   [{ev[0]}] {ev[3]}({ev[4][:60]}...)")

    logger.close()
    print()


if __name__ == "__main__":
    main()