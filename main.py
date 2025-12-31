import asyncio
from scraper import ScraperClass
from search import SearchClass
import blob

# list of top level URLs 
topLevelURLs = ['https://www.google.com/']
#topLevelURLs = ['https://www.oxfordenergy.org/publication-topic/papers/']
#topLevelURLs = ['https://www.oxfordenergy.org/publications/review-of-hydrogen-leakage-along-the-supply-chain-environmental-impact-mitigation-and-recommendations-for-sustainable-deployment/']
#topLevelURLs = ['https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights/the-economic-potential-of-generative-ai-the-next-productivity-frontier#introduction',
#                'https://www.project-syndicate.org/commentary/ai-productivity-boom-forecasts-countered-by-theory-and-data-by-daron-acemoglu-2024-05',
#                'https://academic.oup.com/economicpolicy/advance-article/doi/10.1093/epolic/eiae042/7728473?login=false',
#                'https://economics.mit.edu/news/daron-acemoglu-what-do-we-know-about-economics-ai',
#                'https://www.mckinsey.com/industries/chemicals/our-insights/how-ai-enables-new-possibilities-in-chemicals']
# list of user specified keywords
#keywords = "BioVeritas partners,Bioveritas projects,Bioveritas TRL levels,Bioveritas TRL levels VFA to SAF process,Bioveritas VFA to SAF process"
keywords = 'yeast oil technology studies,yeast oil technology papers,yeast oil recent,yeast oil companies,yeast oil process'
# specify the tier, scraping, domain limits for the scraper
tierLimit = 1
totalScrapingLimit = 1000
scrapingLimit = 20
domainLimit = True
# specify if search is required
useSearch = False
# limit number of search results
searchLimit = 30

# main function calling the run scraper function in scraper.py
async def main(useSearch: bool, keywords: list, topLevelURLs: list, tierLimit: int, totalScrapingLimit: int, scrapingLimit: int, domainLimit: bool, searchLimit: int):
    # run search if required
    if useSearch:
        search = SearchClass()
        topLevelURLs = await search.runSearch(keywords, searchLimit)
    
    # run scraper
    scraper = ScraperClass(tierLimit, totalScrapingLimit, scrapingLimit, domainLimit)
    directory = await scraper.runScraper(topLevelURLs)
    
    # upload data to blob storage
    print(directory)
    await blob.uploadToBlob(directory)  # upload everything also in the container inside the corresponding Azure Storage Account  
    
asyncio.run(main(useSearch=useSearch,
                    keywords=keywords,
                    topLevelURLs=topLevelURLs,
                    tierLimit=tierLimit,
                    totalScrapingLimit=totalScrapingLimit,
                    scrapingLimit=scrapingLimit,
                    domainLimit=domainLimit,
                    searchLimit=searchLimit))