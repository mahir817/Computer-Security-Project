"""
detector.py — Rule engine that checks agent behavior against YAML profiles.
(original, unmodified, as provided by the user — for baseline testing)
"""

import yaml
import time
import json
from typing import List, Optional, Dict, Any


class Detector:
    def __init__(self, profile_path: str):
        with open(profile_path, "r") as f:
            self.profile: Dict[str, Any] = yaml.safe_load(f)

    def check(self, logger, agent_identity: str, tool: str, params: dict) -> List[str]:
        alerts: List[str] = []
        alerts.extend(self._check_scope(tool, params))
        alerts.extend(self._check_sequence(logger, agent_identity, tool))
        alerts.extend(self._check_rate(logger, agent_identity, tool))
        return alerts

    def _check_scope(self, tool: str, params: dict) -> List[str]:
        alerts: List[str] = []
        allowed_tools = self.profile.get("allowed_tools", [])
        if allowed_tools and tool not in allowed_tools:
            alerts.append(
                f"SCOPE ABUSE: tool '{tool}' is not in the allowed tools list "
                f"{allowed_tools}"
            )
            # The tool itself is already fully unauthorized -- skip the
            # target check below so the same call doesn't also get reported
            # as "forbidden target", which is a redundant restatement of
            # the same violation.
            return alerts
        allowed_targets = self.profile.get("allowed_targets", {})
        if tool in allowed_targets:
            permitted = allowed_targets[tool]
            target = self._extract_target(tool, params)
            if permitted == []:
                alerts.append(
                    f"SCOPE ABUSE: '{tool}' is forbidden for this agent "
                    f"(allowed targets: none)"
                )
            elif permitted is not None and target and target not in permitted:
                alerts.append(
                    f"SCOPE ABUSE: '{tool}' used on out-of-policy target "
                    f"'{target}' (allowed: {permitted})"
                )
        return alerts

    def _check_sequence(self, logger, agent_identity: str, tool: str) -> List[str]:
        """Check if a forbidden chain of tool calls has just completed.

        Looks for the forbidden tools appearing IN ORDER within a rolling
        time window (`sequence_window_seconds`, default 120s) rather than
        requiring them to be strictly back-to-back -- so
        query_db -> search_kb -> http_post still trips [query_db, http_post]
        even though an unrelated call sits between them.

        Only fires when the CURRENT call is the one that completes a
        forbidden sequence (tool == seq[-1]), so the same completed chain
        doesn't re-alert on every later call while it's still in the window.
        """
        alerts: List[str] = []
        forbidden = self.profile.get("forbidden_sequences", [])
        if not forbidden:
            return alerts

        window_seconds = self.profile.get("sequence_window_seconds", 120)
        cutoff = time.time() - window_seconds

        recent = logger.recent_events(agent_identity, limit=200)
        history = [t for ts, t, _ in reversed(recent) if ts >= cutoff]

        for seq in forbidden:
            if not seq or seq[-1] != tool:
                continue
            if self._is_ordered_subsequence(seq, history):
                alerts.append(
                    f"SEQUENCE ABUSE: forbidden chain detected "
                    f"[{' -> '.join(seq)}] within {window_seconds}s"
                )
        return alerts

    @staticmethod
    def _is_ordered_subsequence(seq: List[str], history: List[str]) -> bool:
        """True if `seq` appears in `history`, in order, not necessarily
        contiguous (e.g. seq=['a','c'] matches history=['a','b','c'])."""
        it = iter(history)
        return all(item in it for item in seq)

    def _check_rate(self, logger, agent_identity: str, tool: str) -> List[str]:
        alerts: List[str] = []
        rate_limits = self.profile.get("rate_limits", {})
        limit_config = rate_limits.get(tool)
        if not limit_config:
            return alerts
        max_calls = limit_config["max_calls"]
        window_seconds = limit_config["window_seconds"]
        window_start = time.time() - window_seconds
        recent = logger.recent_events(agent_identity, limit=200)
        count = sum(1 for ts, t, _ in recent if t == tool and ts >= window_start)
        if count > max_calls:
            alerts.append(
                f"RATE ABUSE: '{tool}' called {count}x in "
                f"{window_seconds}s (limit: {max_calls})"
            )
        return alerts

    def _extract_target(self, tool: str, params: dict) -> Optional[str]:
        if tool == "query_db":
            return params.get("table")
        elif tool == "http_post":
            return params.get("url")
        elif tool == "search_kb":
            return params.get("query")
        elif tool == "read_ticket":
            return params.get("ticket_id")
        return None

    def get_profile(self) -> Dict[str, Any]:
        return self.profile