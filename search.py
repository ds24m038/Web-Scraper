import time
from duckduckgo_search import DDGS

class SearchClass:
    def __init__(self):
        # No API key needed for DuckDuckGo
        # Create a single DDGS instance to reuse
        self.ddgs = DDGS()

    # placeholder function to extract suitable search terms from user input, potentially using LLMs
    def searchTermExtractor(self, userInput: str):
        searchTerms: list[str] = []
        # placeholder for search term translation
        for term in userInput.split(','):
            searchTerms.append(term.strip())
        print(searchTerms)
        return searchTerms
        
    # search function using DuckDuckGo Search
    def search(self, term: str, searchLimit: int):
        # list for storing found URLs
        searchResult = []
        # search for the term
        try:
            # Use the text search method
            results = list(self.ddgs.text(term, max_results=searchLimit))
            print(f"Raw results: {results}")
            for result in results:
                if 'href' in result:
                    searchResult.append(result['href'])
                elif 'link' in result:
                    searchResult.append(result['link'])
            print(f"No. Search Results #{len(searchResult)}")
        except Exception as err:
            print(f"Search Error: {err}")
            import traceback
            traceback.print_exc()
            
        return searchResult

    # main function to run searches
    async def runSearch(self, userInput: str, searchLimit: int):
        # extract search terms from user input
        searchTerms = self.searchTermExtractor(userInput)
        start = time.time()
        # list for storing search results
        searchResults = []
        # run search for each search term
        for term in searchTerms:
            searchResults.extend(self.search(term, searchLimit))
            
        print(f"Total URLs found: {searchResults}")
        print(f"Search time: {time.time()-start:.2f}s")
        
        return searchResults