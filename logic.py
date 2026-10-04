# name: (muscle group, movement pattern, equipment, weight step in kg; 0 = bodyweight)
EX = {
    "Bench Press":         ("chest", "horizontal push", "barbell", 2.5),
    "Dumbbell Press":      ("chest", "horizontal push", "dumbbell", 2.0),
    "Push-up":             ("chest", "horizontal push", "bodyweight", 0),
    "Machine Chest Press": ("chest", "horizontal push", "machine", 5.0),
    "Cable Fly":           ("chest", "fly", "cable", 2.5),
    "Squat":               ("legs", "squat", "barbell", 5.0),
    "Goblet Squat":        ("legs", "squat", "dumbbell", 2.0),
    "Leg Press":           ("legs", "squat", "machine", 5.0),
    "Romanian Deadlift":   ("legs", "hinge", "barbell", 5.0),
    "Dumbbell RDL":        ("legs", "hinge", "dumbbell", 2.0),
    "Lunge":               ("legs", "single leg", "dumbbell", 2.0),
    "Pull-up":             ("back", "vertical pull", "bodyweight", 0),
    "Lat Pulldown":        ("back", "vertical pull", "machine", 5.0),
    "Barbell Row":         ("back", "horizontal pull", "barbell", 2.5),
    "Dumbbell Row":        ("back", "horizontal pull", "dumbbell", 2.0),
    "Seated Cable Row":    ("back", "horizontal pull", "cable", 5.0),
    "Plank":               ("abs", "hold", "bodyweight", 0),
    "Crunch":              ("abs", "flexion", "bodyweight", 0),
    "Cable Crunch":        ("abs", "flexion", "cable", 2.5),
    "Hanging Knee Raise":  ("abs", "flexion", "bodyweight", 0),
}
LOW, HIGH = 8, 12  # rep range


def swap(name, equip_avoid=None):
    """Same muscle + same pattern first, then same muscle, different pattern."""
    g, p, _, _ = EX[name]
    same = [n for n, v in EX.items() if n != name and v[0] == g and v[1] == p]
    rest = [n for n, v in EX.items() if n != name and v[0] == g and v[1] != p]
    out = same + rest
    if equip_avoid:
        out = [n for n in out if EX[n][2] != equip_avoid]
    return out[:3]


def decide(name, sessions):
    """Double progression. Plain Python, so the numbers are always reliable."""
    step = EX[name][3]
    last = sessions[-1]
    w, reps = last["weight"], last["reps"]
    if min(reps) >= HIGH:
        if step == 0:
            return {"weight": 0, "target_reps": min(reps) + 2,
                    "action": "add reps (or try a harder variation)"}
        return {"weight": w + step, "target_reps": LOW, "action": "increase weight"}
    if min(reps) >= LOW:
        return {"weight": w, "target_reps": min(reps) + 1,
                "action": "same weight, add a rep"}
    prev = sessions[-2] if len(sessions) > 1 else None
    if prev and prev["weight"] == w and min(prev["reps"]) < LOW and step:
        return {"weight": round(w * 0.9 / step) * step, "target_reps": LOW,
                "action": "deload"}
    return {"weight": w, "target_reps": LOW, "action": "repeat the weight"}


def sets_for(sessions, d):
    n = len(sessions[-1]["reps"])
    return max(2, n - 1) if d["action"] == "deload" else n

# Rough "double-check" ceilings (multiple of body weight, 8 reps).
# Heuristic, based on common strength-standard tables. NOT an official standard.
GROUP_RATIO = {
    "male":   {"chest": 1.4, "legs": 2.0, "back": 1.2, "abs": 0.6},
    "female": {"chest": 0.8, "legs": 1.5, "back": 0.8, "abs": 0.4},
}

def weight_cap(name, body_kg, gender="other"):
    g, _, equip, step = EX[name]
    if step == 0:
        return None  # bodyweight move
    if gender in GROUP_RATIO:
        ratio = GROUP_RATIO[gender][g]
    else:  # other / prefer not to say: use the more cautious value
        ratio = min(GROUP_RATIO["male"][g], GROUP_RATIO["female"][g])
    if equip == "dumbbell":
        ratio *= 0.4   # entered per dumbbell
    elif equip in ("machine", "cable"):
        ratio *= 1.5
    return max(step, round(body_kg * ratio / step) * step)