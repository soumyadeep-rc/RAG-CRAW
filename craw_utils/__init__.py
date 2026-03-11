import time
from selenium.webdriver.common.by import By
from langchain_core.documents import Document
from urllib.parse import urlparse
from langchain_community.document_loaders import UnstructuredHTMLLoader

def are_urls_same(url1, url2):
    # normalize urls
    url1 = url1.replace('www.', '').rstrip('/')
    url2 = url2.replace('www.', '').rstrip('/')

    url1 = urlparse(url1.lower())
    url2 = urlparse(url2.lower())
    return (url1.netloc == url2.netloc) and (url1.path == url2.path) and (url1.scheme == url2.scheme)

def url_exists_in_set(visited, url):
    url = url.split('#')[0].split('?')[0].replace('www.', '')
    for visited_url in visited:
        visited_url = visited_url.split('#')[0].split('?')[0].replace('www.', '')
        if are_urls_same(visited_url, url):
            return True
        
        # if domain is different return True
        if urlparse(visited_url).netloc != urlparse(url).netloc:
            return True
        
    return False

# return document
def scrape_site(driver, url, visited=None, count:int=2, write_function=None):

    if(write_function is None):
        write_function = print
    
    write_function(f"Scraping: {url}")
    
    # normalize url
    url = url.split('#')[0].split('?')[0]
    url = url.replace('www.', '')

    if visited is None:
        visited = set()
    if url in visited:
        return []
    print(f"Visiting: {url} + visited Len = {len(visited)}")
    visited.add(url)
    driver.get(url)
    time.sleep(2)  # Adjust timing based on the website's response time
    content = driver.page_source

    with open('page.html', 'w') as f:
        f.write(content)

    loader = UnstructuredHTMLLoader('page.html')
    text_documents = loader.load()

    links = driver.find_elements(By.TAG_NAME, 'a')
    links_hrefs = [link.get_attribute('href') for link in links]
    data = []
    temp_document = Document(page_content=text_documents[0].page_content, metadata={"source": url})
    data.append(temp_document)
    for href in links_hrefs:
        if href and not url_exists_in_set(visited, href):
            if(len(visited) >= count):
                break # Stop scraping after visiting max_pages

            data.extend(scrape_site(driver, href, visited, count, write_function=write_function))
    return data