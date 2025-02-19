import re
from typing import Optional

import requests
from IPython import get_ipython
from IPython.core.interactiveshell import ExecutionResult, traceback


def register_to_slack_exception_handler(
    slack_webhook_url: str,
    slack_message_title: str,
    notebook_url: Optional[str] = None,
) -> None:
    exception_handler = ToSlackExceptionHandler(
        slack_webhook_url=slack_webhook_url,
        slack_message_title=slack_message_title,
        notebook_url=notebook_url,
    )

    def handle_post_run_cell(result: ExecutionResult) -> None:
        error_in_exec = result.error_in_exec

        if error_in_exec:
            exception_handler(exception=error_in_exec, tb=error_in_exec.__traceback__)

    get_ipython().events.register("post_run_cell", handle_post_run_cell)


class ToSlackExceptionHandler:
    def __init__(
        self,
        slack_webhook_url: str,
        slack_message_title: str,
        notebook_url: Optional[str],
    ) -> None:
        super().__init__()
        self.notebook_url = notebook_url
        self.slack_webhook_url = slack_webhook_url
        self.slack_message_title = slack_message_title

    def __call__(
        self,
        exception: BaseException,
        tb: traceback,
    ) -> None:
        text = "".join(traceback.format_exception(type(exception), exception, tb))

        result = requests.post(
            url=self.slack_webhook_url,
            json={
                "attachments": [
                    {
                        "color": "#f2c744",
                        "blocks": [
                            {
                                "type": "header",
                                "text": {
                                    "type": "plain_text",
                                    "text": self.slack_message_title,
                                },
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "plain_text",
                                    "text": str(exception),
                                },
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"```{re.sub('^[-]*', '', text)}```",
                                },
                            },
                            *(
                                [
                                    {
                                        "type": "section",
                                        "text": {"type": "mrkdwn", "text": "👉"},
                                        "accessory": {
                                            "type": "button",
                                            "text": {
                                                "type": "plain_text",
                                                "text": "Go to notebook",
                                            },
                                            "url": self.notebook_url,
                                        },
                                    }
                                ]
                                if self.notebook_url
                                else []
                            ),
                        ],
                    }
                ]
            },
        )

        result.raise_for_status()
