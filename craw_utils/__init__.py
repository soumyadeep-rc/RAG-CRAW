from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from langchain_core.documents import Document
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
        
    print(f"Visiting: {url} | Visited Len = {len(visited)}")
    visited.add(url)
    
    try:
        driver.get(url)
        
        # Wait up to 10 seconds for the <body> tag to load. 
        # Moves on instantly if it loads faster.
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        content = driver.page_source
        
    except Exception as e:
        write_function(f"Error or timeout loading {url}: {e}")
        return []

    # UTF-8 encoding to prevent Unicode crashes
    with open('page.html', 'w', encoding='utf-8') as f:
        f.write(content)

    loader = UnstructuredHTMLLoader('page.html')
    text_documents = loader.load()

    # Safeguard against empty document lists from JS-heavy or blocked pages
    if not text_documents:
        write_function(f"Warning: No extractable text found on {url}")
        return []

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