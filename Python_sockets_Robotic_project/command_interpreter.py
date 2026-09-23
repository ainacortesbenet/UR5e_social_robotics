#!/usr/bin/env python3
import re
from config import ACTIVATION_WORD
from typing import Optional


class VoiceInterpreter:

    @staticmethod
    def normalize_text(text: str) -> str:
        text = text.lower().strip()
        text = text.replace("-", " ")
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def interpret(self, text: Optional[str]) -> Optional[str]:
        if text is None:
            return None

        text = self.normalize_text(text)

        if not text.startswith(ACTIVATION_WORD):
            return None

        text = text[len(ACTIVATION_WORD):].strip()

        if any(k in text for k in ["exit", "quit", "close"]):
            return "exit"

        if any(k in text for k in [
            "init",
            "in it",
            "home",
            "go home",
            "initial position",
            "start position"
        ]):
            return "init"

        if any(k in text for k in [
            "hand shake",
            "handshake",
            "shake hand",
            "shake my hand"
        ]):
            return "handshake"

        if any(k in text for k in [
            "give me five",
            "give 5",
            "give me 5",
            "high five",
            "d5",
            "give me a high five"
        ]):
            return "give5"

        if any(k in text for k in [
            "wave",
            "wife",
            "gave",
            "say hello",
            "say hi",
            "hello",
            "hi"
        ]):
            return "wave"
        
        return "unknown"
