# name: (muscle group, movement pattern, equipment, weight step in kg; 0 = bodyweight)
EX = {
    "bench press":         ("chest", "horizontal push", "barbell", 2.5),
    "dumbbell press":      ("chest", "horizontal push", "dumbbell", 2.0),
    "push-up":             ("chest", "horizontal push", "bodyweight", 0),
    "machine chest press": ("chest", "horizontal push", "machine", 5.0),
    "cable fly":           ("chest", "fly", "cable", 2.5),
    "squat":               ("legs", "squat", "barbell", 5.0),
    "goblet squat":        ("legs", "squat", "dumbbell", 2.0),
    "leg press":           ("legs", "squat", "machine", 5.0),
    "romanian deadlift":   ("legs", "hinge", "barbell", 5.0),
    "dumbbell RDL":        ("legs", "hinge", "dumbbell", 2.0),
    "lunge":               ("legs", "single leg", "dumbbell", 2.0),
    "pull-up":             ("back", "vertical pull", "bodyweight", 0),
    "lat pulldown":        ("back", "vertical pull", "machine", 5.0),
    "barbell row":         ("back", "horizontal pull", "barbell", 2.5),
    "dumbbell row":        ("back", "horizontal pull", "dumbbell", 2.0),
    "seated cable row":    ("back", "horizontal pull", "cable", 5.0),
    "plank":               ("abs", "hold", "bodyweight", 0),
    "crunch":              ("abs", "flexion", "bodyweight", 0),
    "cable crunch":        ("abs", "flexion", "cable", 2.5),
    "hanging knee raise":  ("abs", "flexion", "bodyweight", 0),
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