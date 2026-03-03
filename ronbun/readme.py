from __future__ import annotations
import argparse
import logging
import ssl
import urllib.parse

from glotter_core.project import CoreProject
from snakemd import Document, Inline, MDList, Paragraph, Alert
from subete import LanguageCollection, Repo, Project
from subete.repo import logger as subete_logger


logger = logging.getLogger(__name__)

issue_url_template_base = "https://github.com/TheRenegadeCoder/sample-programs/issues/new"
issue_url_template_query = "?assignees=&labels=enhancement,{label}&template=code-snippet-request.md&title=Add+{project}+in+{language}"


def main():
    """
    The main drop in script for the README generation.
    """
    ssl._create_default_https_context = ssl._create_unverified_context
    args = _get_args()
    numeric_level = getattr(logging, args[1].upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {args[1]}")
    logging.basicConfig(level=numeric_level)
    subete_logger.setLevel(logging.WARNING)  # Turn down the subete logging noise
    logger.info("Loading repos (this may take several minutes)")
    repo = Repo(sample_programs_repo_dir=args[0])
    readme_catalog = ReadMeCatalog(repo)
    for language, page in readme_catalog.pages.items():
        page.dump("README", directory=f"{args[0]}/archive/{language[0]}/{language}")


def _get_args() -> tuple:
    """
    A helper function which gets the log level from 
    the command line. Set as warning from default. 

    :return: the log level provided by the user
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument(
        "-log",
        "--log",
        default="warning",
        help=(
            "Provide logging level. "
            "Example --log debug', default='warning'"
        ),
    )
    options = parser.parse_args()
    return options.path, options.log


def _get_note() -> Alert:
    """
    Generates the text for the note for the README.

    :return: the note alert block in the README
    """
    note = Inline("This page is auto-generated. DO NOT EDIT!", bold=True)
    return Alert(note, Alert.Kind.NOTE)


def _get_intro_text(language: LanguageCollection) -> Paragraph:
    """
    Generates the text for the introduction of the README.

    :param language: the language to generate from the LanguageCollection
    :return: the introduction paragraph in the README
    """
    language_escaped = _markdown_escape(language.name())
    sections = [f"Welcome to Sample Programs in {language_escaped}!"]
    if language.has_docs:
        sections += [
            f" To find documentation related to the {language_escaped} code in this repo, look ",
            Inline("here", link=language.lang_docs_url()),
            "."
        ]

    return Paragraph(sections)


def _generate_program_list(language: LanguageCollection) -> list:
    """
    A helper function which generates a list of programs for the README.

    :param language: a language collection
    :return: a list of sample programs list items
    """
    list_items = list()
    for program in language:
        program_name = _markdown_escape(f"{program}")
        program_line = Paragraph([f":white_check_mark: {program_name} [Requirements]"]) \
            .insert_link(program_name, program.documentation_url()) \
            .insert_link("Requirements", program.project().requirements_url())
        if not program.has_docs():
            program_line.replace(":white_check_mark:", ":warning:") \
                .replace_link(
                    _markdown_escape(program.documentation_url()),
                    _markdown_escape(program.article_issue_query_url())
                )
        list_items.append(program_line)
    return list_items


def _generate_missing_program_list(language: LanguageCollection, missing_programs: list[str]) -> list[Paragraph]:
    """
    Generates the list of programs that are missing in Markdown.

    :param language: the language with missing programs
    :param missing_programs: the list of programs missing from the language collection
    :return: the missing programs lines as Markdown strings
    """
    list_items: list[Paragraph] = list()
    missing_programs.sort(key=lambda x: x.name())
    for program in missing_programs:
        program: Project
        program_name = program.name()
        program_query = "+".join(program_name.split())
        url = issue_url_template_base + issue_url_template_query.format(
            label=program_query.lower(),
            project=program_query,
            language=urllib.parse.quote(_markdown_escape(language.name()))
        )
        program_item = Paragraph([f":x: {program_name} [Requirements]"])\
            .insert_link(program_name, url)\
            .insert_link("Requirements", program.requirements_url())
        list_items.append(program_item)
    return list_items


def _generate_credit() -> Paragraph:
    p = Paragraph([
        """
        This page was generated automatically by the Sample Programs READMEs tool. 
        Find out how to support this project on Github.
        """
    ])
    p.insert_link("this project", "https://github.com/TheRenegadeCoder/sample-programs-readmes")
    return p


def _generate_program_list_header(program_count: int, total_program_count: int) -> str:
    """
    Creates the heading test for the programs list.

    :param program_count: the number of programs completed in the language
    :param total_program_count: the total number of possible programs
    :return: the heading about the program list
    """
    i = int(((program_count / total_program_count) * 4))
    emojis = [":disappointed:", ":thinking:", ":relaxed:", ":smile:", ":partying_face:"]
    return f"Sample Programs List - {program_count}/{total_program_count} {emojis[i]}"


class ReadMeCatalog:
    """
    A representation of the collection of READMEs in the Sample Programs repo.
    """

    def __init__(self, repo: Repo):
        """
        Constructs an instance of a ReadMeCatalog.
        :param repo: a repository instance
        """
        self.repo: Repo = repo
        self.pages: dict[str, Document] = dict()
        self._build_readmes()

    def _build_readme(self, language: LanguageCollection) -> None:
        """
        Creates a README page from a language collection.
        :param language: a programming language collection (e.g., Python)
        :return: None
        """
        page = Document()

        # Introduction
        language_escaped = _markdown_escape(language.name())
        page.add_heading(f"Sample Programs in {language_escaped}")
        page.add_block(_get_note())
        page.add_block(_get_intro_text(language))

        # Sample Programs Section
        program_list = _generate_program_list(language)
        page.add_heading(_generate_program_list_header(
            language.total_programs(),
            self.repo.total_approved_projects()),
            level=2
        )
        page.add_paragraph(
            f"""
            In this section, we feature a list of completed and missing programs in {language_escaped}. See above for the
            current amount of completed programs in {language_escaped}. If you see a program that is missing and would like to 
            add it, please submit an issue, so we can assign it to you. 
            """.strip()
        )

        # Completed Programs List
        page.add_heading("Completed Programs", level=3)
        page.add_paragraph(
            f"""
            Below, you'll find a list of completed code snippets in {language_escaped}. Code snippets preceded by :warning: 
            link to a GitHub issue query featuring a possible article request issue. If an article request issue 
            doesn't exist, we encourage you to create one. Meanwhile, code snippets preceded by :white_check_mark: 
            link to an existing article which provides further documentation. To see the list of approved projects, 
            check out the official Sample Programs projects list. 
            """.strip()
        ).insert_link("Sample Programs project list", "https://sampleprograms.io/projects/")
        page.add_block(MDList(program_list))

        # Missing Programs List
        if language.missing_programs_count() > 0:
            missing_programs_list = _generate_missing_program_list(language, language.missing_programs())
            page.add_heading("Missing Programs", level=3)
            page.add_paragraph(
                f"""
                The following list contains all of the approved programs that are not currently implemented in {language_escaped}.
                Click on the name of the project to easily open an issue in GitHub. Alternatively, click requirements
                to check out the description of the project. 
                """.strip()
            )
            page.add_block(MDList(missing_programs_list))

        # Testing
        page.add_heading("Testing", level=2)
        test_data = language.testinfo()
        untestable_data = language.untestable_info()
        common_data = test_data or untestable_data
        assert common_data is not None

        extension = common_data.file_info.extension
        naming = common_data.file_info.naming.value
        example_filename = (
            CoreProject({"words": ["hello", "world"]}).get_project_name_by_scheme(naming)
            + extension
        )
        page.add_paragraph(
            f"The following list shares details about how we name all Sample Programs in {language_escaped}:"
        )
        page.add_unordered_list([
            f"Extension: {extension}",
            f"Naming Convention: {naming}"
        ])

        page.add_paragraph('For example, the "Hello World" sample would be named this:')
        page.add_unordered_list([example_filename])

        if common_data.is_testable:
            page.add_paragraph(
                f"The following list shares details about what we're using to test all Sample Programs in {language_escaped}:"
            )
            page.add_unordered_list([
                f"Docker Image: {test_data.container_info.image}",
                f"Docker Tag: {test_data.container_info.tag}"
            ])
        else:
            page.add_paragraph(f"{language_escaped} cannot be tested.")

        if common_data.notes:
            page.add_paragraph("Notes:")
            page.add_unordered_list(
                [_markdown_escape(note) for note in common_data.notes]
            )

        if common_data.is_testable:
            glotter = page.add_paragraph("See the Glotter2 project for more information on how to create a testinfo file.")
            glotter.insert_link("Glotter2 project", "https://github.com/rzuckerm/glotter2")

        page.add_horizontal_rule()
        page.add_block(_generate_credit())

        self.pages[language.pathlike_name()] = page

    def _build_readmes(self) -> None:
        """
        Generates all READMEs for the repo.
        :return: None
        """
        for language in self.repo:
            self._build_readme(language)


def _markdown_escape(s: str):
    return s.replace("*", r"\*").replace("`", r"\`")


if __name__ == "__main__":
    main()
