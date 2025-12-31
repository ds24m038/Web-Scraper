import os
from dotenv import load_dotenv
from web_search_client import WebSearchClient
from web_search_client.models import SafeSearch
from azure.core.credentials import AzureKeyCredential
import time

class SearchClass:
    def __init__(self):
        # load environment variables from .env
        load_dotenv()
        # set subscription key
        self.SUBSCRIPTION_KEY = os.environ['BING_SEARCH_SUBSCRIPTION_KEY']

    # placeholder function to extract suitable search terms from user input, potentially using LLMs
    def searchTermExtractor(self, userInput:str):
        searchTerms: list[str] = []
        # placeholder for search term translation
        for term in userInput.split(','):
            searchTerms.append(term)
        print(searchTerms)
        return searchTerms
        
    # search function using Bing Web Search API
    def search(self, term: str, searchLimit: int):
        # initialize web search client
        client = WebSearchClient(AzureKeyCredential(self.SUBSCRIPTION_KEY))
        # list for storing found URLs
        searchResult = []
        # search for the term
        try:
            web_data = client.web.search(query=term, count=searchLimit)
            if web_data.web_pages.value:
                print("No. Search Results #{}".format(len(web_data.web_pages.value)))
                # store search results
                for i in range(len(web_data.web_pages.value)):
                    searchResult.append(web_data.web_pages.value[i].url)
            else:
                print("No Pages Found During Search")

        except Exception as err:
            print("Search Error. {}".format(err))
            
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
            
        print(searchResults)
        print(time.time()-start)
        
        return searchResults