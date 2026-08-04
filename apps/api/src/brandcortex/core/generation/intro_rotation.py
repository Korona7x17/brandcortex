"""No-repeat intro selection (spec §6.4, §6.5).

The intro bank lives in `brand_config.intro_bank`, keyed by locale. ThaiSwim's starting bank (Thai):

    ทุกฤดูกาลมีนักว่ายน้ำที่ทำให้เราต้องหยุดมอง
    บางคนไม่เคยหยุดพัฒนา ไม่ว่าอายุจะเท่าไหร่
    อีกหนึ่งชื่อที่คนรักว่ายน้ำควรรู้จัก
    นักว่ายน้ำมาสเตอร์ที่พิสูจน์ว่าการฝึกซ้อมไม่มีวันสาย
    ในสระว่ายน้ำ ประสบการณ์คือพลังอย่างหนึ่ง

Rotation exists because a Page that opens every swimmer post the same way starts reading like a form
letter, which is the opposite of recognition. The bank is meant to grow over time, and the reflection
agent tracks fatigue per line (spec §10.2) — a line that used to travel and no longer does should fall
out of rotation rather than being trusted forever.
"""


def pick_intro(*, bank: list[str], recent: list[str], lookback: int = 5) -> str:
    """Choose an intro not used within the last `lookback` posts.

    `recent` comes from `intro_history`, most recent first.

    When every line in the bank falls inside the lookback window — a small bank and a busy week — it
    returns the least recently used rather than failing. A repeat beats a blocked post, and it is the
    signal that the bank needs extending.
    """
    if not bank:
        raise ValueError("intro bank is empty for this locale")

    blocked = set(recent[:lookback])
    for line in bank:
        if line not in blocked:
            return line

    # Everything is blocked: fall back to whichever bank line was used longest ago.
    order = {line: i for i, line in enumerate(recent)}
    return max(bank, key=lambda line: order.get(line, len(recent)))
