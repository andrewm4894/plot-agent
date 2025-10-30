import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import uuid

from datetime import datetime
from plot_agent.agent import PlotAgent


def main() -> None:
    # Load environment variables (OPENAI_API_KEY)
    load_dotenv()

    # Generate a session ID to group all traces from this example run
    # Set as env var so PostHog can automatically track it
    session_id = str(uuid.uuid4())
    os.environ["POSTHOG_AI_SESSION_ID"] = session_id
    print(f"🔗 AI Session ID: {session_id}")
    print("All traces in this session will be grouped together in PostHog.\n")

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

    # Initialize the agent; allow more iterations to avoid premature recursion limits
    agent = PlotAgent(
        max_iterations=20,
        llm_timeout=45,
        llm_max_retries=0,
        debug=True
    )
    agent.set_df(df)

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
        response = agent.process_message(user_msg)
        print("- Agent response (truncated):")
        print(response[:500] if isinstance(response, str) else str(response)[:500])

        # Print the latest generated code from the tool
        code = agent.view_generated_code() or ""
        print("\n- Generated code:")
        print("" if code else "<no code captured>")
        if code:
            print(code)

        # Check if a figure object exists
        print("\n- does_fig_exist():", agent.does_fig_exist())

    # Optionally retrieve the final figure
    fig = agent.get_figure()
    print("\nFinal figure available:", fig is not None)


if __name__ == "__main__":
    main()

