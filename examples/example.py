import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np

from datetime import datetime
from plot_agent.graph import PlotAgent
import plotly.io as pio


def main() -> None:
    # Load environment variables (OPENAI_API_KEY)
    load_dotenv()

    # Generate a random time series dataframe similar to example_0.ipynb
    data = {
        "date": pd.date_range(start="2023-01-01", periods=1000),
        "sales": np.random.randint(100, 1000, size=1000),
        "region": np.random.choice(["North", "South", "East", "West"], size=1000),
        "product": np.random.choice(["A", "B", "C"], size=1000),
    }
    df = pd.DataFrame(data)

    print(f"DataFrame shape: {df.shape}")
    print(df.head().to_string(index=False))

    # Initialize the agent (uses default ChatOpenAI if not provided)
    # Enable checkpointing to maintain multi-turn continuity
    checkpoint_path = os.environ.get("PLOT_AGENT_EXAMPLE_CHECKPOINT", "sqlite:///examples/checkpoint_temp.db")
    agent = PlotAgent(df=df, checkpoint_path=checkpoint_path)
    thread_id = "example-script"

    # Conversation steps analogous to the notebook
    prompts = [
        "Create a line chart showing sales over time, colored by region",
        "Add a title 'Sales Trends by Region' and smooth the lines with a 7-day moving average",
        "Apply a dark theme to the plot",
        "Make a 2x2 subplot grid, one subplot per region",
    ]

    for step, user_msg in enumerate(prompts, start=1):
        print("\n" + "=" * 80)
        print(f"[{datetime.now().isoformat(timespec='seconds')}] Step {step} - User message:\n{user_msg}")
        result = agent.run(user_msg, thread_id=thread_id)
        fig_json = (result or {}).get("fig", {}).get("fig_json")
        
        # Display generated code
        generated_code = agent.get_last_code()
        if generated_code:
            print("\n--- Generated Code ---")
            # Limit display to first 1000 chars if code is very long
            if len(generated_code) > 1000:
                print(generated_code[:1000])
                print(f"... (truncated, {len(generated_code)} total characters)")
            else:
                print(generated_code)
            print("--- End Code ---\n")
        
        print("- Has fig:", bool(fig_json))
        # Optionally reconstruct a plotly Figure (headless environments won't render)
        if fig_json:
            fig = pio.from_json(fig_json)
            # Avoid fig.show() in headless runs; just confirm object type
            print("- Figure type:", type(fig).__name__)

    print("\nDone.")


if __name__ == "__main__":
    main()

