import gradio as gr
import ollama
from logic import decide, swap, sets_for

LIFTS = ["bench press", "squat", "barbell row"]
MODEL = "gemma3:4b"  # run once: ollama pull gemma3:4b

SYSTEM = """You are a friendly gym coach. Decisions were already made by a rules engine.
Do NOT change any numbers or add exercises. For each lift, explain in 2 sentences why.
If a swap list is given, say briefly why those options train the same muscles.
If anything sounds like pain, advise stopping and seeing a professional."""


def parse(text):
    out = []
    for line in text.strip().splitlines():
        p = line.split()
        if len(p) >= 2:
            try:
                out.append({"weight": float(p[0]), "reps": [int(x) for x in p[1:]]})
            except ValueError:
                pass
    return out


def run(t1, l1, t2, l2, t3, l3):
    facts = []
    for name, text, liked in zip(LIFTS, (t1, t2, t3), (l1, l2, l3)):
        s = parse(text)[-3:]
        if not s:
            return f"Please enter sessions for {name} (format: weight rep rep rep)."
        d = decide(name, s)
        sets = sets_for(s, d)
        line = (f"{name}: next {d['weight']} kg, {sets} sets x "
                f"{d['target_reps']}+ reps ({d['action']})")
        if not liked:
            line += f" | lifter dislikes it; swap options: {swap(name)}"
        facts.append(line)
    try:
        reply = ollama.chat(model=MODEL, messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "\n".join(facts)}])["message"]["content"]
    except Exception as e:
        reply = f"(Coach unavailable: is Ollama running? {e})"
    return ("### Plan\n" + "\n".join(f"- {f}" for f in facts)
            + "\n\n### Coach says\n" + reply)


with gr.Blocks(title="LiftCoach") as demo:
    gr.Markdown("# LiftCoach (runs 100% locally)\n"
                "One line per session: `weight rep rep rep` (kg)")
    inputs = []
    for n in LIFTS:
        with gr.Row():
            inputs += [
                gr.Textbox(label=f"{n}: last 3 sessions", lines=3,
                           placeholder="60 10 9 8\n60 11 10 9\n60 12 12 12"),
                gr.Checkbox(label="Liked it?", value=True),
            ]
    out = gr.Markdown()
    gr.Button("Get my plan").click(run, inputs, out)

if __name__ == "__main__":
    demo.launch()  # for phone on same Wi-Fi: demo.launch(server_name="0.0.0.0")