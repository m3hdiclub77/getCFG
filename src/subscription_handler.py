def parse_subscription_content(self, content: str) -> List[str]:
        """Parse subscription content and extract proxy configurations."""
        configs = []
        if not content:
            return configs
            
        content = content.strip()
        
        try:
            decoded = base64.b64decode(content).decode('utf-8')
            for line in decoded.strip().split('\n'):
                line = line.strip()
                if line and any(line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                    configs.append(line)
            if configs:
                return configs
        except Exception as e:
            self.logger.debug(f"Failed to decode entire content as base64: {str(e)}")
        
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if any(line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                configs.append(line)
                continue
                
            try:
                decoded_line = base64.b64decode(line).decode('utf-8')
                if any(decoded_line.startswith(protocol) for protocol in self.config.SUPPORTED_PROTOCOLS):
                    configs.append(decoded_line)
            except:
                continue
                
        return configs
