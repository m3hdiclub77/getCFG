import requests
import base64
from typing import List, Optional
from urllib.parse import urlparse, unquote
import logging

class SubscriptionHandler:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def is_base64(self, s: str) -> bool:
        """Check if a string is base64 encoded."""
        try:
            # Check if string contains valid base64 characters
            if not all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in s):
                return False
            
            # Try to decode
            decoded = base64.b64decode(s).decode('utf-8')
            # Check if decoded string is a valid URL
            parsed = urlparse(decoded)
            return all([parsed.scheme, parsed.netloc])
        except Exception:
            return False

    def decode_subscription_url(self, url: str) -> str:
        """Decode base64 encoded subscription URL if necessary."""
        # First, check if URL is URL-encoded
        decoded_url = unquote(url)
        
        # Then check if it's base64 encoded
        if self.is_base64(decoded_url):
            try:
                return base64.b64decode(decoded_url).decode('utf-8')
            except Exception as e:
                self.logger.error(f"Error decoding base64 URL: {str(e)}")
                return url
        return decoded_url

    def fetch_subscription(self, url: str) -> Optional[str]:
        """Fetch content from subscription URL."""
        try:
            # Decode the URL if it's base64 encoded
            actual_url = self.decode_subscription_url(url)
            
            response = requests.get(
                actual_url, 
                headers=self.config.HEADERS, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            content = response.text
            # Try to decode content if it's base64 encoded
            if self.is_base64(content):
                try:
                    decoded_content = base64.b64decode(content).decode('utf-8')
                    return decoded_content
                except Exception as e:
                    self.logger.warning(f"Could not decode base64 content: {str(e)}")
                    return content
            return content
            
        except Exception as e:
            self.logger.error(f"Error fetching subscription from {url}: {str(e)}")
            return None

    def parse_subscription_content(self, content: str) -> List[str]:
        """Parse subscription content and extract proxy configurations."""
        configs = []
        if not content:
            return configs
            
        # Split content by common delimiters
        lines = []
        for delimiter in ['\n', '|', ';']:
            if delimiter in content:
                lines.extend(content.split(delimiter))
                break
        else:
            lines = [content]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Check if the line itself is a valid config
                if any(line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                    configs.append(line)
                    continue
                
                # Try to decode if it might be base64
                if not any(c in line for c in ':/\\'):  # Likely base64 if no URL-like characters
                    try:
                        decoded = base64.b64decode(line).decode('utf-8')
                        if any(decoded.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                            configs.append(decoded)
                            continue
                    except Exception:
                        pass
            except Exception as e:
                self.logger.debug(f"Error processing line: {str(e)}")
                continue
                
        return configs

    def process_subscription_url(self, url: str) -> List[str]:
        """Process a subscription URL and return list of valid configs."""
        content = self.fetch_subscription(url)
        if content:
            configs = self.parse_subscription_content(content)
            self.logger.info(f"Found {len(configs)} configs in subscription {url}")
            return configs
        return []
