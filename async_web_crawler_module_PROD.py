"""
URL Fixing Web Crawler Module

Key Features:
- Fixes YouTube channel/video URLs from @username format to standard format
- Cleans documentation anchor links by removing XML-style brackets
- Validates URL structure before processing
- Handles batch processing of multiple URLs
- Saves processed content with timestamps
- Provides detailed logging of crawling/fixing process

Common URL Fixes:
1. YouTube:   youtube.com/@username/watch?v=123 -> youtube.com/watch?v=123
2. Docs:      domain.com/<#section> -> domain.com/#section
3. Channels:  youtube.com/@username -> youtube.com/c/username

Dependencies: crawl4ai package, Python 3.7+, aiohttp
"""

import asyncio
import re
import logging
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from typing import Optional, List, Union

# Simplified imports based on actual crawl4ai package structure
from crawl4ai import AsyncWebCrawler  
from crawl4ai.models import CrawlResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FilenameGenerator:
    """Generates valid Windows filenames from URLs and content"""
    
    @staticmethod
    def extract_title(markdown_content: str) -> Optional[str]:
        """Extract title from markdown content"""
        # Look for first h1 heading
        h1_match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1)
        return None

    @staticmethod
    def clean_filename(text: str) -> str:
        """Convert text to valid Windows filename"""
        # Replace invalid chars
        clean = re.sub(r'[<>:"/\\|?*]', '', text)
        # Limit length and remove trailing spaces
        return clean[:150].strip()

    @classmethod
    def generate_filename(cls, url: str, markdown_content: str, output_dir: Path) -> Path:
        """Generate filename based on URL and content"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('.', '_')
        path = parsed_url.path.strip('/').replace('/', '_')
        
        # Try to get title from content
        title = cls.extract_title(markdown_content)
        if title:
            base_name = cls.clean_filename(title)
        else:
            base_name = f"{domain}_{path}"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{base_name}_{timestamp}.md"
        
        return output_dir / cls.clean_filename(filename)
    

class URLFixer:
    """
    Fixes and validates URLs in markdown content. Handles YouTube channels,
    documentation anchor links, and general URL cleanup operations.
    Methods:    fix_url, is_valid_url, fix_markdown_urls
    """
    
    @staticmethod
    def fix_url(url: str) -> str:
        """
        Transform malformed URLs into standard clickable formats.
        Args:       url: The URL string to clean and standardize
        Returns:    str: The cleaned and standardized URL
        Example:    youtube.com/@user/watch?v=123 -> youtube.com/watch?v=123
        """
        if not url:
            return url
            
        # Fix YouTube URLs from @channel format to standard format
        if 'youtube.com/@' in url:
            # Fix video URLs
            url = re.sub(
                r'youtube\.com/@([^/]+)/<?watch\?v=([^>]+)>?',
                r'youtube.com/watch?v=\2',  # Remove channel prefix for video URLs
                url
            )
            # Fix channel URLs
            url = re.sub(
                r'youtube\.com/@([^/]+)/?$',
                r'youtube.com/c/\1',  # Convert @ format to /c/ format
                url
            )
        
        # Fix documentation anchor links by removing XML brackets
        url = re.sub(
            r'([^/]+)/<?#([^>]+)>?',
            r'\1#\2',  # Clean anchor links
            url
        )
        
        # Remove any remaining XML-style brackets
        url = re.sub(r'[<>]', '', url)
        
        return url.strip()

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Validate URL structure with scheme and domain.
        Args:       url: The URL string to validate
        Returns:    bool: True if URL has valid structure
        Example:    https://example.com -> True, not-a-url -> False
        """
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    @classmethod
    def fix_markdown_urls(cls, content: str) -> str:
        """
        Process and fix all URLs found within markdown content.
        Args:       content: Markdown text containing URLs to process
        Returns:    str: Markdown text with all URLs cleaned and standardized
        Note:       Handles both simple links [title](url) and links with alt text
        """
        if not content:
            return content

        def replace_url(match) -> str:
            title = match.group(1)
            url = match.group(2)
            alt_text = match.group(3) if len(match.groups()) > 2 else None
            
            fixed_url = cls.fix_url(url)
            
            if cls.is_valid_url(fixed_url):
                if alt_text:
                    return f'[{title}]({fixed_url} "{alt_text}")'
                return f'[{title}]({fixed_url})'
            return match.group(0)

        pattern = r'\[(.*?)\]\((.*?)(?:\s+"(.*?)")?\)'
        return re.sub(pattern, replace_url, content)

async def crawl_and_fix_urls(urls: List[str], output_dir: Path = Path("Output_Results")) -> List[str]:
    """
    Crawl URLs and fix malformed URLs in their content.
    Args:       urls: List of URLs to crawl and process
                output_dir: Directory to save files (default: Output_Results)
    Returns:    List[str]: Paths to saved files containing fixed content
    Note:       Creates output_dir if missing, uses timestamps in filenames
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []
    
    async with AsyncWebCrawler() as crawler:
        for url in urls:
            try:
                logger.info(f"Crawling: {url}")
                result = await crawler.arun(url=url)
                
                if result and result.success and result.markdown:
                    # Fix URLs in the markdown
                    fixed_markdown = URLFixer.fix_markdown_urls(result.markdown)
                    
                    # Parse URL components
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc.replace('.', '_')
                    path = parsed_url.path.strip('/').replace('/', '_')
                    
                    # Create filename with timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    base_name = f"{domain}_{path}"
                    if not path:
                        base_name = domain
                        
                    filename = output_dir / f"{base_name}_{timestamp}.md"
                    filename = Path(re.sub(r'[<>:"/\\|?*]', '', str(filename)))
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(fixed_markdown)
                        
                    saved_files.append(str(filename))
                    logger.info(f"Saved fixed content to: {filename}")
                else:
                    error = result.error_message if result else "Unknown error"
                    logger.error(f"Failed to crawl {url}: {error}")
                    
            except Exception as e:
                logger.exception(f"Error processing {url}: {str(e)}")

    return saved_files

async def main(input_urls):
    """
    Entry point for URL fixing crawler.
    Tests:      1. YouTube channel URL
                2. Documentation with anchor
                3. YouTube playlist URL
    Handles:    Interrupts, logging, error cases
    """

    try:
        saved_files = await crawl_and_fix_urls(input_urls)
        if saved_files:
            logger.info(f"\nProcessed {len(saved_files)} files successfully:")
            for file in saved_files:
                logger.info(f"  - {file}")
        else:
            logger.warning("No files were processed successfully")
            
    except KeyboardInterrupt:
        logger.info("\nProcessing interrupted by user")
    except Exception as e:
        logger.exception("Fatal error occurred")
        raise

if __name__ == "__main__":

    input_urls = [
        #"https://www.youtube.com/@scaredketchup/videos",
        #"https://ai.pydantic.dev/#why-use-pydanticai",
        #"https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi",
        # "https://metron-us.com/waterscope-videos/",
        # "https://crawl4ai.com/mkdocs/",
        "https://github.com/ai-in-pm?tab=repositories"
    ]

    asyncio.run(main(input_urls))

    # CLEANUP OPERATION A LITTLE BIT
    # TODO: Fix output filename to move "crawl_results" later in filename, just before datetime stamp. 
    # TODO: Make the output report a little cleaner.
    # TODO: Set the "Output_Results" folder location in the __main__ clause, not inside the crawl_and_fix_urls() function.
    # TODO: Give some indication of progress after the script starts.

    # NO ADVERTISEMENTS BEFORE LAUNCHING TARGET VIDEO
    # TODO: see if there is a way to extract the "start" immediately URL without advertisements before the acctual video starts. 

    # STREAMLIT FRONT-END
    # TODO: Create a Streamlit front end that displays an input form, and outputs the results on-screen, and saves results to disk. 
    # TODO:     Streamlit app may require some special async event handling for Crawl4AI
    
    # NAMING OUTPUT FILE EXPLICITY IN AN INPUT FORM OR DICTIONARY
    # TODO: enhance the code to have an input_urls input data structure (list or dictionary) and loop through it correctly. 
    # TODO: the following code does not work.
    # input_urls = [
    #     {"WaterScope_University": "https://www.youtube.com/playlist?list=PLb9UHlsdZRW0P8Ff7uEOJ0az_JqFtLppz"}, 
    #     {"WaterScope_Tutorials": "https://www.youtube.com/playlist?list=PLb9UHlsdZRW1izbGv202cksQL-n-enXoM"}, 
    #     {"Water_Meter_InstallatioN": "https://www.youtube.com/playlist?list=PLb9UHlsdZRW3fj1yHlW3Z8UUcaJ04hvyu"}
    # ]

    # asyncio.run(main(input_urls[0]["WaterScope_University"]))

