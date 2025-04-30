# file: app/services/journals/issn_service.py

import aiohttp
from aiohttp import ClientError
from loguru import logger
from rdflib import Graph, URIRef, Namespace, RDF

from app.models.journal_identifiers import JournalIdentifier
from app.services.journals.issn_info import IssnInfo

BF = Namespace("http://id.loc.gov/ontologies/bibframe/")
RDF_NS = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SCHEMA = Namespace("http://schema.org/")


class ISSNService:
    """
    Service to check ISSN identifiers against the ISSN portal
    """
    BASE_URL = "https://portal.issn.org/resource/ISSN"

    def __init__(self):
        self.headers = {"Accept": "application/ld+json"}

    async def check_identifier(self, identifier: JournalIdentifier) -> IssnInfo:
        """
        Main public method: fetch, parse, and analyze ISSN metadata,
        including otherPhysicalFormat-linked ISSNs recursively.
        """
        issn = identifier.value
        visited = set()
        full_graph = Graph(base="http://issn.org/resource/ISSN/")

        await self._recursive_fetch_and_merge(issn, visited, full_graph)

        if not full_graph:
            logger.warning(f"Graph empty after crawling {issn}")
            return IssnInfo(checked_issn=issn, errors=["Failed to load ISSN metadata"])

        return self._analyze_graph(full_graph, issn, visited)

    async def _recursive_fetch_and_merge(self, issn: str, visited: set, graph: Graph):
        if issn in visited:
            return
        visited.add(issn)

        logger.debug(f"Fetching RDF for ISSN {issn}")
        raw_data = await self._fetch_issn_rdf(issn)
        if raw_data is None:
            logger.warning(f"Failed to fetch RDF for {issn}")
            return

        local_graph = self._build_graph(raw_data, issn)
        if local_graph is None:
            logger.warning(f"Failed to build RDF graph for {issn}")
            return

        graph += local_graph

        main_node = URIRef(f"http://issn.org/resource/ISSN/{issn}")
        for alt in local_graph.objects(subject=main_node, predicate=BF.otherPhysicalFormat):
            if isinstance(alt, URIRef) and "/ISSN/" in alt:
                linked_issn = alt.split("/ISSN/")[-1]
                await self._recursive_fetch_and_merge(linked_issn, visited, graph)

    async def _fetch_issn_rdf(self, issn: str) -> str | None:
        url = f"{self.BASE_URL}/{issn}?format=json"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status != 200:
                        logger.error(f"HTTP error {resp.status} fetching {url}")
                        return None
                    return await resp.text()
        except ClientError as e:
            logger.exception(f"ClientError while fetching {url}: {e}")
            return None
        except aiohttp.http_exceptions.HttpProcessingError as e:
            logger.exception(f"HTTP processing error for {url}: {e}")
            return None

    def _build_graph(self, raw_data: str, issn: str) -> Graph | None:
        g = Graph()
        try:
            g.parse(data=raw_data, format="json-ld", publicID="http://issn.org/")
            return g
        except (ValueError, SyntaxError) as e:
            logger.exception(f"Error parsing RDF for {issn}: {e}")
            return None

    def _analyze_graph(self, g: Graph, issn: str, visited: set) -> IssnInfo:
        main_node = URIRef(f"http://issn.org/resource/ISSN/{issn}")
        issn_l = None
        title = None
        urls = set()

        for identifier_uri in g.objects(main_node, BF.identifiedBy):
            if (identifier_uri, RDF.type, BF.IssnL) in g:
                value = g.value(subject=identifier_uri, predicate=RDF_NS.value)
                if value:
                    issn_l = str(value)
                    break

        name_val = g.value(subject=main_node, predicate=SCHEMA.name)
        if name_val:
            title = str(name_val)
        else:
            title_val = g.value(subject=main_node, predicate=BF.mainTitle)
            if title_val:
                title = str(title_val)

        for v in visited:
            node = URIRef(f"http://issn.org/resource/ISSN/{v}")
            for url in g.objects(subject=node, predicate=SCHEMA.url):
                urls.add(str(url))

        return IssnInfo(
            checked_issn=issn,
            issn_l=issn_l,
            related_issns=list(visited),
            title=title,
            urls=list(urls),
            errors=[]
        )
