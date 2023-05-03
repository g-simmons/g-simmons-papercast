import os

from dotenv import load_dotenv
from papercast.pipelines import Pipeline
from papercast.processors import (
    ArxivProcessor,
    GROBIDProcessor,
    SayProcessor,
    SemanticScholarProcessor,
    CoquiTTSProcessor,
    SoundfileProcessor,
    PDFProcessor,
)
from papercast.publishers import GithubPagesPodcastPublisher  # type: ignore
from papercast.server import Server
from papercast.subscribers import ZoteroSubscriber

load_dotenv()

api_key = os.getenv("PAPERCAST_ZOTERO_API_KEY", None)
user_id = os.getenv("PAPERCAST_ZOTERO_USER_ID", None)

if api_key is None or user_id is None:
    raise ValueError("Zotero API key or user ID not found")

github_pages_kwargs = dict(
    title="g-simmons-papercast",
    base_url="https://g-simmons.github.io/g-simmons-papercast/",
    language="en-us",
    subtitle="Drinking the firehose one paper at a time",
    copyright="Rights to paper content are reserved by the authors for each paper. I make no claim to ownership or copyright of the content of this podcast.",
    author="Gabriel Simmons",
    email="gsimmons@ucdavis.edu",
    description="A podcast of research articles, created with papercast (github.com/g-simmons/papercast)",
    cover_path="https://g-simmons.github.io/g-simmons-papercast/cover.jpg",
    categories=["Mathematics", "Tech News", "Courses"],
    keywords=[
        "Machine Learning",
        "Natural Language Processing",
        "Artificial Intelligence",
    ],
    xml_path="/Users/gabe/g-simmons-papercast/feed.xml",
)
zotero_kwargs = dict(
    api_key=api_key,
    library_id=user_id,
    library_type="user",
    pdf_dir="data/pdfs",
)

grobid_kwargs = dict(
    remove_non_printable_chars=True, grobid_url="http://localhost:8070/"
)


def make_coqui_pipeline():
    pipeline = Pipeline(name="default")
    pipeline.add_processors(
        {
            "semantic_scholar": SemanticScholarProcessor(
                pdf_dir="data/pdfs", json_dir="data/json"
            ),
            "arxiv": ArxivProcessor(pdf_dir="data/pdfs", json_dir="data/json"),
            "pdf": PDFProcessor(pdf_dir="data/pdfs"),
            "zotero": ZoteroSubscriber(**zotero_kwargs),
            "grobid": GROBIDProcessor(**grobid_kwargs),
            "coqui": CoquiTTSProcessor(wav_dir="data/wavs"),
            "soundfile": SoundfileProcessor(output_format="mp3"),
            "github_pages": GithubPagesPodcastPublisher(**github_pages_kwargs),
        },
    )

    pipeline.connect("semantic_scholar", "pdf", "grobid", "pdf")
    pipeline.connect("arxiv", "pdf", "grobid", "pdf")
    pipeline.connect("pdf", "pdf", "grobid", "pdf")
    pipeline.connect("zotero", "pdf", "grobid", "pdf")
    pipeline.connect("grobid", "text", "coqui", "text")
    pipeline.connect(
        "coqui",
        "wav_path",
        "soundfile",
        "audio_path",
    )
    pipeline.connect("soundfile", "output_path", "github_pages", "mp3_path")
    pipeline.connect("grobid", "abstract", "github_pages", "description")
    pipeline.connect("grobid", "title", "github_pages", "title")

    return pipeline


def make_default_pipeline():
    pipeline = Pipeline(name="default")
    pipeline.add_processors(
        {
            "semantic_scholar": SemanticScholarProcessor(
                pdf_dir="data/pdfs", json_dir="data/json"
            ),
            "pdf": PDFProcessor(pdf_dir="data/pdfs"),
            "arxiv": ArxivProcessor(pdf_dir="data/pdfs", json_dir="data/json"),
            "zotero": ZoteroSubscriber(**zotero_kwargs),
            "grobid": GROBIDProcessor(**grobid_kwargs),
            "say": SayProcessor(mp3_dir="data/mp3s", txt_dir="data/txts"),
            "github_pages": GithubPagesPodcastPublisher(**github_pages_kwargs),
        },
    )

    pipeline.connect("semantic_scholar", "pdf", "grobid", "pdf")
    pipeline.connect("arxiv", "pdf", "grobid", "pdf")
    pipeline.connect("pdf", "pdf", "grobid", "pdf")
    pipeline.connect("zotero", "pdf", "grobid", "pdf")
    pipeline.connect("grobid", "text", "say", "text")
    pipeline.connect("say", "mp3_path", "github_pages", "mp3_path")
    pipeline.connect("grobid", "abstract", "github_pages", "description")
    pipeline.connect("grobid", "title", "github_pages", "title")

    return pipeline


default_pipeline = make_default_pipeline()
coqui_pipeline = make_coqui_pipeline()

server = Server(pipelines={"default": default_pipeline, "coqui": coqui_pipeline})

if __name__ == "__main__":
    server.run()
