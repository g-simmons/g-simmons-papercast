from papercast.pipelines import Pipeline
from papercast.processors import SemanticScholarProcessor
from papercast.processors import ArxivProcessor
from papercast.processors import PDFProcessor
from papercast.processors import SayProcessor
from papercast.processors import GROBIDProcessor
from papercast.publishers import GithubPagesPodcastPublisher
from papercast.subscribers.zotero_subscriber import ZoteroSubscriber
from papercast.server import Server
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("PAPERCAST_ZOTERO_API_KEY", None)
user_id = os.getenv("PAPERCAST_ZOTERO_USER_ID", None)

if api_key is None or user_id is None:
    raise ValueError("Zotero API key or user ID not found")

pipeline = Pipeline(name="default")

# pipeline.add_processor("zotero", ZoteroSubscriber(api_key, user_id))

pipeline.add_processor(
    "semantic_scholar",
    SemanticScholarProcessor(pdf_dir="data/pdfs", json_dir="data/json"),
)

pipeline.add_processor(
    "arxiv", ArxivProcessor(pdf_dir="data/pdfs", json_dir="data/json")
)

pipeline.add_processor("pdf", PDFProcessor(pdf_dir="data/pdfs"))

pipeline.add_processor(
    "grobid",
    GROBIDProcessor(
        remove_non_printable_chars=True, grobid_url="http://localhost:8070/"
    ),
)

pipeline.add_processor("say", SayProcessor(mp3_dir="data/mp3s", txt_dir="data/txts"))

pipeline.add_processor(
    "github_pages",
    GithubPagesPodcastPublisher(
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
    ),
)

pipeline.connect("semantic_scholar", "pdf", "grobid", "pdf")
pipeline.connect("arxiv", "pdf", "grobid", "pdf")
pipeline.connect("pdf", "pdf", "grobid", "pdf")
pipeline.connect("grobid", "text", "say", "text")
pipeline.connect("say", "mp3_path", "github_pages", "mp3_path")
pipeline.connect("grobid", "abstract", "github_pages", "description")
pipeline.connect("grobid", "title", "github_pages", "title")

server = Server(pipelines={"default": pipeline})

if __name__ == "__main__":
    server.run()
