import asyncio

from langchain_openai import ChatOpenAI

from plot_agent.graph import PlotAgent


async def main():
    llm = ChatOpenAI(model="gpt-4o-mini")
    agent = PlotAgent(llm, df=None)

    async for ev in agent.astream(
        "Make a scatter of sepal_length vs sepal_width from the iris dataset"
    ):
        if ev.get("event") in {"on_tool_start", "on_tool_end", "on_llm_new_token"}:
            print(ev)


if __name__ == "__main__":
    asyncio.run(main())

