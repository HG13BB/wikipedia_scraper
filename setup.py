#ensure we can imoport module from pip
import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='wiki_file_type_scraper',
    version='0.0.0',
    author='Henry Greeley',
    author_email='henry.greeley@gmail.com',
    description='Package to scrape wikipedia info.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/HG13BB/wikipedia_scraper',
    project_urls = {
        "Bug Tracker": "https://github.com/HG13BB/wikipedia_scraper/issues"
    },
    license='MIT',
    packages=['wiki_file_type_scraper'],
    install_requires=['bs4','pandas','requests'],
)
