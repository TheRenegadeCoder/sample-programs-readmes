import argparse
import logging
import ssl
from urllib import request
from xml.etree import ElementTree

from snakemd import Document, InlineText, MDList, Paragraph
from subete import LanguageCollection, Repo


logger = logging.getLogger(__name__)


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


def _get_sample_programs_text() -> str:
    return """
    Below, you'll find a list of code snippets in this collection.
    Code snippets preceded by :warning: link to a GitHub 
    issue query featuring a possible article request issue. If an article request issue 
    doesn't exist, we encourage you to create one. Meanwhile, code snippets preceded 
    by :white_check_mark: link to an existing article which provides further documentation.
    """


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


def _get_complete_program_list() -> list:
    """
    A helper function which retrieves the entire list of eligible programs from the
    documentation website.
    """
    programs = list()
    logger.info(f"Attempting to open https://sample-programs.therenegadecoder.com/sitemap.xml")
    xml_data = request.urlopen("https://sample-programs.therenegadecoder.com/sitemap.xml")
    for child in ElementTree.parse(xml_data).getroot():
        url = child[0].text
        if "projects" in url and len(url.split("/")) == 6:
            programs.append(url.split("/")[4])
    return sorted(programs)


def _generate_credit() -> Paragraph:
    p = Paragraph([
        """
        This page was generated automatically by the Sample Programs READMEs tool. 
        Find out how to support this project on Github.
        """
    ])
    p.insert_link("this project", "https://github.com/TheRenegadeCoder/sample-programs-readmes")
    return p


def _generate_program_list_header(program_list, total_programs):
    i = int(((len(program_list) / len(total_programs)) * 4))
    emojis = [":disappointed:", ":thinking:", ":relaxed:", ":smile:", ":partying_face:"]
    return f"Sample Programs List — {len(program_list)}/{len(total_programs)} {emojis[i]}"


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
        self._programs = _get_complete_program_list()
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

        # Sample Programs List
        program_list = _generate_program_list(language)
        page.add_header(_generate_program_list_header(program_list, self._programs), level=2)
        page.add_paragraph(_get_sample_programs_text())
        page.add_element(MDList(program_list))

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
