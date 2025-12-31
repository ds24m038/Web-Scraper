

import asyncio
from playwright.async_api import async_playwright, BrowserContext
from pathlib import Path
import time, re, hashlib, json, base64
import tldextract

class ScraperClass:
    # initialize scraper client
    def __init__(self, tierLimit: int, totalScrapingLimit: int, scrapingLimit: int, domainLimit: bool):
        # limit number of concurrent tasks
        self.semaphore = asyncio.Semaphore(10)
        # limit of tiers to be scraped
        self.TIERLIMIT = tierLimit
        # limit total number of links to be scraped
        self.TOTALSCRAPINGLIMIT = totalScrapingLimit
        # limit number of links to be scraped per topLevelURL
        self.SCRAPINGLIMIT = scrapingLimit
        # limit scraping to domain of current topLevelURL
        self.DOMAINLIMIT = domainLimit

        # create output directory to save scraped data
        outputTime = time.strftime("%d%m%Y-%H%M%S")
        self.outputDir = Path(f'./output/{outputTime}/')
        self.outputDir.mkdir(parents=True, exist_ok=True)

        # queue for URLs to be scraped
        self.scrapingQueue = asyncio.Queue()
        # stores already scraped pages
        self.scrapedPages = set()
        # stores URLs to be excepted from scraping
        self.excludedDomains = set(["linkedin", "youtube", "twitter", "x", "facebook", "bluesky",])
        # list for storing scraping hierarchy
        self.hierarchy = []

    # main function coordinating the scraping & auxiliary functions
    async def runScraper(self, topLevelURLs: list):
        start = time.time()
            
        # start scraping process for each topLevelURL
        for url in topLevelURLs:
            # initialize scrapingQueue with topLevelURL -> tier 0
            await self.scrapingQueue.put({'URL': url, 'TIER': 0, 'PARENT': None})
            # create directory within output per topLevelURL to save scraped data
            domain = tldextract.extract(url).domain
            urlDirectory = self.outputDir / domain
            urlDirectory.mkdir(parents=True, exist_ok=True)
            # starts scraping process
            await self.scrapePages(urlDirectory)
            print("Finished scraping", url)
        
        # save metadata as json file
        with open(self.outputDir / 'metadata.json', 'w') as metadataFile:
            json.dump(self.hierarchy, metadataFile, indent=4)
        end = time.time()
        print("TOTAL SCRAPING TIME:", end-start)
        
        # return path to directory to be uploaded to blob storage
        return self.outputDir
        
    # function creating browser & context; calls scrapePage function per URL in scrapinqQueue
    async def scrapePages(self, directory: Path):
        async with async_playwright() as plwr:
            # create browser & context;
            browser = await plwr.chromium.launch(headless=False)
            context = await browser.new_context()
            print('BROWSER CREATED')
            tasks = []
            i = 0
            
            while True:
                # stop function if scraping queue is empty & no tasks are running
                if self.scrapingQueue.empty() and not tasks:
                    break
                
                # start scraping if queue is not empty
                if not self.scrapingQueue.empty():
                    # when total scraping limit is reached, stop creating new scraping tasks
                    if len(self.scrapedPages) >= self.TOTALSCRAPINGLIMIT:
                        break
                    if i >= self.SCRAPINGLIMIT:
                        break
                    # get URL & tier from scrapingQueue
                    urlDict = await self.scrapingQueue.get()
                    url = urlDict['URL']
                    tier = urlDict['TIER']
                    parent = urlDict['PARENT']
                    # acquire semaphore to limit number of concurrent tasks
                    await self.semaphore.acquire()
                    # create scraping task
                    task = asyncio.create_task(self.scrapePage(context, url, tier, directory, parent))
                    tasks.append(task)
                    i += 1

                if i % 10 == 0:
                    print("SCRAPED:", len(self.scrapedPages), "TASKS:", len(tasks))
                # remove completed tasks from tasks list
                tasks = [task for task in tasks if not task.done()]
                # avoid blocking event loop
                await asyncio.sleep(0)
        
            # wait for all concurrent tasks to be completed
            await asyncio.gather(*tasks)
            # close context & browser after all tasks are completed
            await context.close()
            await browser.close()
            print(f'\nSCRAPING COMPLETED\n{len(self.scrapedPages)} PAGES SCRAPED')

    # function scraping a single page
    async def scrapePage(self, context: BrowserContext, url: str, tier: int, directory: Path, parent: str):
        try:
            # create new browser page (tab)
            page = await context.new_page()
            
            # try block for scraping and handling file downloads if navigation to URL fails
            try:
                # open URL
                await page.goto(url)
                # wait for page to load properly
                await asyncio.sleep(0.5)
                # get title & duplicate free lists for links & texts
                linkLocator = page.locator('a')
                #textLocator = page.locator('p, h1, h2, h3, h4, h5, h6, span, div')
                links = await linkLocator.evaluate_all('anchors => { const seen = new Set(); return anchors.map(anchor => anchor.href).filter(href => href.length > 0 && !seen.has(href) && seen.add(href)); }')
                #texts = await textLocator.evaluate_all('elements => { const seen = new Set(); return elements.map(element => element.textContent.trim()).filter(text => text.length > 0 && !seen.has(text) && seen.add(text)); }')
                title = await page.title()
                #html = await page.content()
                # generate hash as ID for page
                hashValue = self.generateHash(url+title, 16)
                # save page as pdf
                await page.emulate_media(media="screen")
                await page.pdf(path=f"{directory}/{hashValue}.pdf", landscape=False, scale=0.7)
                # close page after crawling is completed
                await page.close()
                # add URL to set of scraped pages after successful scraping
                self.scrapedPages.add(url)
                # remove whitespace from texts list 
                #texts = [re.sub(r'\s+', ' ', text).strip() for text in texts]
                # insert links into crawlingQueue
                for link in links:
                    await self.checkURL({'URL': link, 'TIER': tier+1, 'PARENT': url})
                # construct metadata dictionary & save metadata
                pageData = {'ID': hashValue, 'TIMESTAMP': int(time.time()), 'TYPE': 'page', 'URL': url, 'TIER': tier, 'TITLE': title, 'PARENT': parent}
                await self.saveMetadata(self.hierarchy, pageData)

            # if navigation fails, handle as file download
            except Exception as e:
                print(f"DOWNLOAD DETECTED: {url}", e)
                # expect download
                async with page.expect_download() as downloadInfo:
                    # trigger download
                    await page.evaluate("window.location.href = '{}';".format(url))
                # wait for download to finish & get download object
                download = await downloadInfo.value
                # generate hash as ID for download
                hashValue = self.generateHash(download.url+download.suggested_filename, 16)
                # save download to disk
                await download.save_as(f"{directory}/downloads/{hashValue}_{download.suggested_filename}")
                print(f"DOWNLOAD SAVED: {download.suggested_filename}")
                # add URL to set of scraped pages after successful download
                self.scrapedPages.add(url)
                # generate hash as ID for download
                hashValue = self.generateHash(download.url+download.suggested_filename, 16)
                # construct metadata dictionary & save metadata
                downloadData = {'ID': hashValue, 'TIMESTAMP': int(time.time()), 'TYPE': 'download', 'URL': url, 'TIER': tier, 'TITLE': download.suggested_filename, 'PARENT': parent}
                await self.saveMetadata(self.hierarchy, downloadData)

        except Exception as e:
            print('ERROR WHILE SCRAPING', e)
        finally:
            # release semaphore to allow new tasks to be created
            self.semaphore.release()
            
    # function processing found URLs
    async def checkURL(self, urlDict: dict):
        # extract URL, tier & parent from dictionary
        url = urlDict['URL']
        tier = urlDict['TIER']
        parent = urlDict['PARENT']
        # exclude mailto & tel links
        if url.startswith('mailto:') or url.startswith('tel:'):
            return
        # add URL to scrapping queue if conditions are fulfilled
        if url not in self.scrapedPages and tier <= self.TIERLIMIT:
            # extract domain & tld from url
            extractURL = tldextract.extract(url)
            # check if URL is an excluded URL
            if extractURL.domain in self.excludedDomains:
                #print('EXCLUDED URL:', url)
                return
            # only add URL within domain if domainLimit is set
            if self.DOMAINLIMIT == True:
                fullDomain = f"{extractURL.domain}.{extractURL.suffix}"
                fullParentDomain = f"{tldextract.extract(parent).domain}.{tldextract.extract(parent).suffix}"
                if fullDomain != fullParentDomain:
                    return
            # add valid URL to scrapingQueue
            await self.scrapingQueue.put({'URL': url, 'TIER': tier, 'PARENT': parent})
                
    # function for building metadata json
    async def saveMetadata(self, hierarchy: list, metadata: dict):
        # if top level URL, append as top node
        if metadata['PARENT'] is None:
            hierarchy.append(metadata)
        # if not top level URL, search for parent in hierarchy, append as child
        else:
            for parent in hierarchy:
                if parent['URL'] == metadata['PARENT']:
                    if 'CHILDREN' not in parent:
                        parent['CHILDREN'] = []
                    parent['CHILDREN'].append(metadata)
                    return
                if 'CHILDREN' in parent:
                    await self.saveMetadata(parent['CHILDREN'], metadata)
                                
    # function for generating custom length hash
    def generateHash(self, input: str, length: int):
        sha256Hash = hashlib.sha256(input.encode()).digest()
        encodedHash = base64.b64encode(sha256Hash).decode('utf-8')
        return encodedHash.replace('/', '').replace('+', '').replace('=', '')[:length]