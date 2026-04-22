#!/usr/bin/env python3
"""
Mock AI Teacher agent loop for Phase 1 (W1).

This is intentionally lightweight and local-only:
- Reads user text from stdin.
- Responds in hint-first style by default.
- Supports direct-answer mode via `/direct`.
"""

from __future__ import annotations


def hint_first_response(question: str) -> str:
    return (
        "Goi y truoc khi tra loi: hay xac dinh boi canh lich su, "
        "quan sat ky hinh tuong tren Cuu Dinh, va lien he voi y nghia bieu trung. "
        f"Cau hoi cua ban: '{question.strip()}'. "
        "Ban thu neu 1-2 gia thuyet truoc, roi toi se sua va bo sung."
    )


def direct_answer_response(question: str) -> str:
    return (
        "Tra loi truc tiep (direct mode): "
        f"voi cau hoi '{question.strip()}', can doi chieu theo nguon noi dung di san "
        "trong LMS de dam bao chinh xac. Trong W1 day la mock response."
    )


def main() -> None:
    print("AI Teacher Mock da san sang. Nhap /quit de thoat.")
    while True:
        try:
            text = input("> ").strip()
        except EOFError:
            print()
            break

        if not text:
            continue
        if text.lower() in {"/quit", "quit", "exit"}:
            break

        if text.startswith("/direct"):
            question = text[len("/direct") :].strip() or "Cau hoi trong direct mode"
            print(direct_answer_response(question))
        else:
            print(hint_first_response(text))

    print("AI Teacher Mock da dung.")


if __name__ == "__main__":
    main()
