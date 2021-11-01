import argparse
import logging
import ssl

from snakemd import Document, InlineText, MDList, Paragraph
from subete import LanguageCollection, Repo


logger = logging.getLogger(__name__)


issue_url_template_base = "https://github.com/TheRenegadeCoder/sample-programs/issues/new"
issue_url_template_query = "?assignees=&labels=enhancement&template=code-snippet-request.md&title=Add+{project}+in+{language}"


def main():
    ssl._create_default_https_context = ssl._create_unverified_context
    args = _get_args()
    numeric_level = getattr(logging, args[1].upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args[1]}')
    logging.basicConfig(level=numeric_level)
    repo = Repo(source_dir=args[0])
    readme_catalog = ReadMeCatalog(repo)
    for language, page in readme_catalog.pages.items():
        page.output_page(f"{args[0]}/{language[0]}/{language}")


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


def _get_intro_text(language: LanguageCollection) -> Paragraph:
    paragraph = Paragraph([f"Welcome to Sample Programs in {language}! "])
    text = InlineText("here.", url=language.lang_docs_url())
    if text.verify_url():
        paragraph.add(f"To find documentation related to the {language} code in this repo, look ")
        paragraph.add(text)
    return paragraph


def _generate_program_list(language: LanguageCollection) -> list:
    """
    A helper function which generates a list of programs for the README.
    :param language: a language collection
    :return: a list of sample programs list items
    """
    list_items = list()
    for program in language.sample_programs().values():
        program_name = f"{program}"
        program_line = Paragraph([f":white_check_mark: {program_name} [Requirements]"]) \
            .insert_link(program_name, program.documentation_url()) \
            .insert_link("Requirements", program.requirements_url())
        if not program_line.verify_urls()[program.documentation_url()]:
            program_line.replace(":white_check_mark:", ":warning:") \
                .replace_link(program.documentation_url(), program.article_issue_query_url())
        list_items.append(program_line)
    return list_items


def _generate_missing_program_list(language: str, missing_programs: list[str]):
    list_items = list()
    missing_programs.sort()
    for program in missing_programs:
        program_name = " ".join(program.split("-")).title()
        program_query = "+".join(program_name.split())
        url = issue_url_template_base + issue_url_template_query.format(project=program_query, language=language)
        program_item = Paragraph([f":x: {program_name} [Requirements]"])\
            .insert_link(program_name, url)\
            .insert_link("Requirements", f"https://sample-programs.therenegadecoder.com/projects/{program}")
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


def _generate_program_list_header(program_count: int, total_program_count: int):
    i = int(((program_count / total_program_count) * 4))
    emojis = [":disappointed:", ":thinking:", ":relaxed:", ":smile:", ":partying_face:"]
    return f"Sample Programs List - {program_count}/{total_program_count} {emojis[i]}"


class ReadMeCatalog:
    """
    An representation of the collection of READMEs in the Sample Programs repo.
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
        page = Document("README")

        # Introduction
        page.add_header(f"Sample Programs in {language}")
        page.add_element(_get_intro_text(language))

        # Sample Programs Section
        program_list = _generate_program_list(language)
        page.add_header(_generate_program_list_header(
            language.total_programs(),
            self.repo.total_approved_projects()),
            level=2
        )
        page.add_paragraph(
            f"""
            In this section, we feature a list of completed and missing programs in {language}. See above for the
            current amount of completed programs in {language}. If you see a program that is missing and would like to 
            add it, please submit an issue, so we can assign it to you. 
            """.strip()
        )

        # Completed Programs List
        page.add_header("Completed Programs", level=3)
        page.add_paragraph(
            f"""
            Below, you'll find a list of completed code snippets in {language}. Code snippets preceded by :warning: 
            link to a GitHub issue query featuring a possible article request issue. If an article request issue 
            doesn't exist, we encourage you to create one. Meanwhile, code snippets preceded by :white_check_mark: 
            link to an existing article which provides further documentation. To see the list of approved projects, 
            check out the official Sample Programs projects list. 
            """.strip()
        ).insert_link("Sample Programs project list", "https://sample-programs.therenegadecoder.com/projects/")
        page.add_element(MDList(program_list))

        # Missing Programs List
        missing_programs_list = _generate_missing_program_list(str(language), language.missing_programs())
        page.add_header("Missing Programs", level=3)
        page.add_paragraph(
            f"""
            The following list contains all of the approved programs that are not currently implemented in {language}.
            Click on the name of the project to easily open an issue in GitHub. Alternatively, click requirements
            to check out the description of the project. 
            """.strip()
        )
        page.add_element(MDList(missing_programs_list))

        # Testing
        page.add_header("Testing", level=2)
        test_data = language.testinfo()
        if not test_data:
            page.add_paragraph(
                """
                This language currently does not feature testing. If you'd like to help in the efforts to test all of 
                the code in this repo, consider creating a testinfo.yml file with the following information:
                """
            )
            page.add_code("folder:\n  extension:\n  naming:\n\ncontainer:\n  image:\n  tag:\n  cmd:", lang="yml")
        else:
            page.add_paragraph(
                f"The following list shares details about what we're using to test all Sample Programs in {language}."
            )
            page.add_unordered_list([
                f"Docker Image: {test_data['container']['image']}",
                f"Docker Tag: {test_data['container']['tag']}"
            ])
        glotter = page.add_paragraph("See the Glotter project for more information on how to create a testinfo file.")
        glotter.insert_link("Glotter project", "https://github.com/auroq/glotter")
        page.add_horizontal_rule()
        page.add_element(_generate_credit())

        self.pages[language.pathlike_name()] = page

    def _build_readmes(self) -> None:
        """
        Generates all READMEs for the repo.
        :return: None
        """
        for _, language in self.repo.language_collections().items():
            self._build_readme(language)


if __name__ == "__main__":
    main()
