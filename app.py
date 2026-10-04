import gradio as gr
import ollama
from logic import EX, decide, swap, sets_for, weight_cap

MODEL = "gemma3:4b"  # to install model: "ollama pull gemma3:4b"

SYSTEM = """You are a friendly gym coach. Decisions were already made by a rules engine.
Do NOT change any numbers or add exercises.
The weights shown are the NEXT targets, not what the lifter did today.
For each exercise, explain in 2 sentences why. Do not comment on form or technique,
and do not assume why a lifter dislikes a lift.
If a swap list is given, say briefly why those options train the same muscles.
If a safety warning is given, mention it kindly.
Mention pain only to say: if anything hurts, stop and see a professional.
If the lifter is under 18, suggest training with supervision."""


def add_entry(state, ex, w1, a1, b1, c1, w2, a2, b2, c2, liked):
    state = list(state)
    if not ex:
        return state, "Pick an exercise first.", render(state)
    step = EX[ex][3]

    def ok_reps(*r):
        return all(x is not None and 0 <= x <= 50 for x in r)

    if w1 is None or not (0 < w1 <= 400 or (step == 0 and w1 == 0)):
        return state, "Latest session: enter a weight between 0 and 400 kg.", render(state)
    if not ok_reps(a1, b1, c1):
        return state, "Latest session: enter reps (0-50) for all 3 sets.", render(state)
    sessions = []
    # optional earlier session, only used if filled in
    if w2 is not None and ok_reps(a2, b2, c2) and (0 < w2 <= 400 or (step == 0 and w2 == 0)):
        sessions.append({"weight": float(w2), "reps": [int(a2), int(b2), int(c2)]})
    sessions.append({"weight": float(w1), "reps": [int(a1), int(b1), int(c1)]})
    state = [e for e in state if e["name"] != ex]  # re-adding replaces
    state.append({"name": ex, "sessions": sessions, "liked": bool(liked)})
    return state, f"Added {ex}.", render(state)


def render(state):
    if not state:
        return "_No exercises added yet._"
    return "\n".join(
        f"- **{e['name']}** ({len(e['sessions'])} session(s), "
        f"{'liked' if e['liked'] else 'not liked'})" for e in state)


def clear():
    return [], "Cleared.", render([])


def run(name, age, body_kg, state):
    if not name or not name.strip():
        return "Please enter your name."
    if age is None or not (10 <= age <= 100):
        return "Please enter an age between 10 and 100."
    if body_kg is None or not (30 <= body_kg <= 300):
        return "Please enter a body weight between 30 and 300 kg."
    if not state:
        return "Add at least one exercise first."

    facts, warnings = [], []
    for e in state:
        n, s = e["name"], e["sessions"]
        d = decide(n, s)
        sets = sets_for(s, d)
        cap = weight_cap(n, body_kg)
        warn = ""
        if cap and d["weight"] > cap:
            if s[-1]["weight"] > cap:
                warn = (f"Logged weight {s[-1]['weight']} kg is unusually high for "
                        f"{body_kg} kg body weight. Double-check the input.")
            else:
                warn = (f"{d['weight']} kg is a big load for your body weight. "
                        f"Safer to hold at {s[-1]['weight']} kg and build reps first.")
                d = {**d, "weight": s[-1]["weight"], "target_reps": d["target_reps"]}
            warnings.append(f"{n}: {warn}")
        line = (f"{n}: next {d['weight']} kg, {sets} sets x "
                f"{d['target_reps']}+ reps ({d['action']})")
        if warn:
            line += f" | SAFETY WARNING: {warn}"
        if not e["liked"]:
            line += f" | lifter dislikes it; swap options: {swap(n)}"
        facts.append(line)

    prompt = f"Lifter: {name.strip()}, age {int(age)}, {body_kg} kg.\n" + "\n".join(facts)
    try:
        reply = ollama.chat(model=MODEL, messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}])["message"]["content"]
    except Exception as ex:
        reply = f"(Coach unavailable: is Ollama running? {ex})"
    out = f"### Plan for {name.strip()}\n" + "\n".join(f"- {f}" for f in facts)
    if warnings:
        out += "\n\n### Warnings\n" + "\n".join(f"- {w}" for w in warnings)
    return out + "\n\n### Coach says\n" + reply


with gr.Blocks(title="LiftCoach") as demo:
    gr.Markdown("# LiftCoach \nYour data never leaves this computer.")
    state = gr.State([])

    gr.Markdown("### 1. About you")
    with gr.Row():
        name = gr.Textbox(label="Name")
        age = gr.Number(label="Age", precision=0)
        body = gr.Number(label="Body weight (kg)")

    gr.Markdown("### 2. Add exercises (only the ones you want)")
    ex = gr.Dropdown(sorted(EX), label="Exercise")
    gr.Markdown("**Latest session** (dumbbells: weight per dumbbell)")
    with gr.Row():
        w1 = gr.Number(label="Weight (kg)")
        a1 = gr.Number(label="Set 1 reps", precision=0)
        b1 = gr.Number(label="Set 2 reps", precision=0)
        c1 = gr.Number(label="Set 3 reps", precision=0)
    gr.Markdown("**Previous session** (optional, helps spot a plateau)")
    with gr.Row():
        w2 = gr.Number(label="Weight (kg)")
        a2 = gr.Number(label="Set 1 reps", precision=0)
        b2 = gr.Number(label="Set 2 reps", precision=0)
        c2 = gr.Number(label="Set 3 reps", precision=0)
    liked = gr.Checkbox(label="I like this exercise", value=True)
    with gr.Row():
        add = gr.Button("Add exercise")
        clr = gr.Button("Clear all")
    msg = gr.Markdown()
    added = gr.Markdown("_No exercises added yet._")

    gr.Markdown("### 3. Your plan")
    go = gr.Button("Get my plan", variant="primary")
    out = gr.Markdown()

    add.click(add_entry, [state, ex, w1, a1, b1, c1, w2, a2, b2, c2, liked],
              [state, msg, added])
    clr.click(clear, None, [state, msg, added])
    go.click(run, [name, age, body, state], out)

if __name__ == "__main__":
    demo.launch()  # for phone on same Wi-Fi: To create a public link, set `share=True` in `launch()`