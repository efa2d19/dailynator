from typing import Sequence

from slack_sdk.models.blocks import Block
from slack_sdk.models.blocks import SectionBlock
from slack_sdk.models.blocks import ContextBlock

from slack_sdk.models.attachments import BlockAttachment
from slack_sdk.models.blocks import MarkdownTextObject
from slack_sdk.models.blocks import DividerBlock
from slack_sdk.models.blocks import HeaderBlock


def report_attachment_block(
        header_text: str,
        body_text: str,
        color: str,
) -> BlockAttachment:
    return BlockAttachment(
        blocks=[
            HeaderBlock(text=header_text),
            SectionBlock(text=MarkdownTextObject(text=body_text))
        ],
        color=color
    )


def start_daily_block(
        header_text: str,
        body_text: str,
        first_question: str,
) -> Sequence[Block, Block]:
    return [
        ContextBlock(
            elements=[
                MarkdownTextObject(
                    text=header_text,
                ),
            ]
        ),
        DividerBlock(),
        MarkdownTextObject(
            text=body_text,
        ),
        MarkdownTextObject(
            text=first_question,
        ),
    ]


def end_daily_block(
        start_body_text: str,
        end_body_text: str,
) -> Sequence[Block, Block]:
    # TODO add link to the channel here
    return [
        MarkdownTextObject(
            text=start_body_text,
        ),
        MarkdownTextObject(
            text=end_body_text,
        ),
        DividerBlock()
    ]


def question_list_block(
        question_list: list[str, str],
) -> Sequence[Block, Block]:
    field_list = list()

    for idx, question in enumerate(question_list):
        field_list.append(
            MarkdownTextObject(
                text=f"{idx}.\t{question}",
            )
        )

    return [
        HeaderBlock(
            text="Question list",
        ),
        DividerBlock(),
        SectionBlock(
            fields=field_list,
        ),
    ]


def error_block(
        header_text: str,
        body_text: str,
) -> Sequence[Block, Block]:
    return [
        HeaderBlock(
            text=":x:" + header_text,
        ),
        DividerBlock(),
        SectionBlock(
            fields=[
                MarkdownTextObject(
                    text=body_text,
                )
            ],
        ),
    ]


def success_block(
        header_text: str,
) -> Sequence[Block, Block]:
    return [
        HeaderBlock(
            text=":white_check_mark:" + header_text,
        ),
        DividerBlock(),
    ]
