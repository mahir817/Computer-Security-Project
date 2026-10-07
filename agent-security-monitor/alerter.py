"""
alerter.py — as provided by the user — for baseline testing
"""
 
import json
import time
import sqlite3
from typing import Optional, List, Dict
 
 
class Alerter:
    def __init__(self, alert_db_path: Optional[str] = "alerts.db"):
        self.alerts: List[Dict] = []
        self.db = None
        if alert_db_path:
            self.db = sqlite3.connect(alert_db_path)
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts          REAL    NOT NULL,
                    task_id     TEXT,
                    agent_identity TEXT,
                    tool        TEXT,
                    params      TEXT,
                    reason      TEXT,
                    severity    TEXT,
                    narrative   TEXT
                )
            """)
            self.db.commit()
 
    def raise_alert(self, task_id: str, agent_identity: str, tool: str,
                    params: dict, reason: str) -> dict:
        severity = self._classify_severity(reason)
        narrative = self._build_narrative(agent_identity, tool, params, reason)
        alert = {
            "timestamp": time.time(),
            "task_id": task_id,
            "agent": agent_identity,
            "triggering_tool": tool,
            "params": params,
            "reason": reason,
            "severity": severity,
            "narrative": narrative,
        }
        self.alerts.append(alert)
        self._print_alert(alert)
        if self.db:
            self.db.execute(
                "INSERT INTO alerts "
                "(ts, task_id, agent_identity, tool, params, reason, severity, narrative) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (alert["timestamp"], task_id, agent_identity, tool,
                 json.dumps(params), reason, severity, narrative)
            )
            self.db.commit()
        return alert
 
    def _classify_severity(self, reason: str) -> str:
        reason_lower = reason.lower()
        if "sequence abuse" in reason_lower:
            return "CRITICAL"
        elif "scope abuse" in reason_lower:
            return "HIGH"
        elif "rate abuse" in reason_lower:
            return "MEDIUM"
        return "INFO"
 
    def _build_narrative(self, agent: str, tool: str, params: dict, reason: str) -> str:
        reason_lower = reason.lower()
        if "sequence abuse" in reason_lower:
            return (
                f"ATTACK CHAIN DETECTED: Agent '{agent}' executed a forbidden "
                f"sequence of tool calls ending with '{tool}'. Parameters: {json.dumps(params)}."
            )
        elif "scope abuse" in reason_lower:
            target = params.get("table") or params.get("url") or "unknown"
            return (
                f"UNAUTHORIZED ACCESS: Agent '{agent}' used tool '{tool}' to "
                f"access '{target}', which is outside its permitted scope."
            )
        elif "rate abuse" in reason_lower:
            return (
                f"ABNORMAL ACTIVITY RATE: Agent '{agent}' is calling '{tool}' "
                f"at an unusually high rate, exceeding configured thresholds."
            )
        else:
            return f"Agent '{agent}' triggered tool '{tool}' with {json.dumps(params)} — {reason}."
 
    def _print_alert(self, alert: dict):
        severity_icons = {"CRITICAL": "!!", "HIGH": "!", "MEDIUM": "~", "INFO": "i"}
        icon = severity_icons.get(alert["severity"], "?")
        print(f"\n[{icon}] [{alert['severity']}] ALERT")
        print(f"   Agent:   {alert['agent']}")
        print(f"   Task:    {alert['task_id']}")
        print(f"   Tool:    {alert['triggering_tool']}")
        print(f"   Reason:  {alert['reason']}")
        print(f"   Story:   {alert['narrative']}")
 
    def get_alerts(self) -> List[Dict]:
        return self.alerts
 
    def get_alerts_by_severity(self, severity: str) -> List[Dict]:
        return [a for a in self.alerts if a["severity"] == severity]
 
    def close(self):
        if self.db:
            self.db.close()