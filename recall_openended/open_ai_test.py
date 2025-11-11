"""Minimal smoke-test helper for local OpenAI configuration.

This script intentionally avoids hard-coding secrets. Configure your API key
via the OPENAI_API_KEY environment variable (preferred) or pass it explicitly
when instantiating the client. Running the script will issue a single test
prompt and print the model response.
"""

import os

from openai import OpenAI


def main() -> None:
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
    raise RuntimeError(
      "OPENAI_API_KEY not set. Export your key before running this helper."
    )

  client = OpenAI(api_key=api_key)

  response = client.responses.create(
    model="gpt-4.1-mini",
    input="write a haiku about applied neuroscience",
    store=False,
  )

  print(response.output_text)


if __name__ == "__main__":
  main()
